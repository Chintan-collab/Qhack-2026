"""AnalysisAgent — turns raw customer/property data into inferred metrics.

Runs three real-data APIs deterministically in parallel:
  * Nominatim    — postal_code → lat/lon
  * PVGIS        — lat/lon + kWp → annual solar yield + optimal angles
  * SMARD        — German wholesale day-ahead electricity price

Then calls Gemini once to synthesize:
  * house_type_probability (from postal_code + build_year + context)
  * current_heating_cost_eur_year (from heating_type + house + household size)
  * optimal_bundle (solar + battery + heat pump + wallbox as applicable)
  * financing_options (tailored to financial_profile + bundle total cost)

All results are written back to SalesData in shared state.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.agents.base.agent import BaseAgent
from app.agents.base.llm import chat_completion
from app.agents.base.types import AgentContext, AgentMessage, MessageRole
from app.agents.sales.schemas import (
    ProductRecommendation,
    SalesData,
    SalesPhase,
)
from app.agents.tools.nominatim import (
    GeocodeError,
    GeocodeResult,
    geocode_postal_code,
)
from app.agents.tools.pvgis import (
    PVGISError,
    PVGISResult,
    estimate_pv_yield,
)
from app.agents.tools.smard import (
    FILTER_DAY_AHEAD_PRICE,
    SmardError,
    SmardSeries,
    fetch_smard_series,
)
from app.core.logging import logger

# Retail markup over wholesale day-ahead for German residential.
# Wholesale is typically 5-15 ct/kWh; residential retail 30-40 ct/kWh.
# This rough markup (taxes, grid fees, levies, supplier margin) is only
# used as a fallback when we have no better signal.
DEFAULT_RETAIL_MARKUP_EUR_KWH = 0.22

# House-type → default PV system size assumption, used when we don't
# have a better roof-area estimate.
DEFAULT_KWP_BY_HOUSE_TYPE: dict[str, float] = {
    "detached": 9.0,
    "semi-detached": 6.5,
    "townhouse": 5.0,
    "terraced": 5.0,
    "apartment": 3.0,
    "bungalow": 6.0,
}
FALLBACK_DEFAULT_KWP = 7.0


SYSTEM_PROMPT = """\
You are an energy-analysis AI for a German residential energy installer. \
The deterministic tools have already been run (geocoding, PVGIS solar yield, \
SMARD electricity prices). Your job is to infer the remaining structured \
values that those APIs cannot give us:

1. **house_type_probability** — a probability distribution over likely house \
types for this postal code + build year + known hints. Use your knowledge of \
German residential housing stock. Keys should be from this set: \
["Detached", "Semi-detached", "Townhouse", "Apartment", "Bungalow"]. \
Values must sum to ~1.0.

2. **current_heating_cost_eur_year** — integer euros per year, based on \
heating_type, house_type, build_year, household_size. Provide a short \
reasoning string explaining the estimate.

3. **optimal_bundle** — the best combination of products for this customer. \
Use the solar yield from PVGIS, the retail electricity price, and the \
customer profile to pick 2-5 items from: solar PV, battery storage, heat \
pump, wallbox / EV charger, energy management system. Give each item a \
name, short description, rough price range in euros, and 2-3 key benefits. \
Also produce a bundle_rationale string and a bundle_total_cost_eur integer.

4. **financing_options** — 2-4 realistic financing paths tailored to the \
customer's financial_profile and the bundle total cost. Use German-market \
options where possible (KfW 270/442, installer leasing, cash discount, etc.).

Call `store_analysis` once with ALL of these values. Do not ask questions — \
you have all the context you need. Be concise and grounded in the numbers."""


STORE_ANALYSIS_TOOL = {
    "name": "store_analysis",
    "description": "Store the inferred analysis values in one call.",
    "input_schema": {
        "type": "object",
        "properties": {
            "house_type_probability": {
                "type": "object",
                "description": (
                    "Map of house type label to probability (0-1). "
                    "Values should sum to ~1.0."
                ),
            },
            "house_type_reasoning": {"type": "string"},
            "current_heating_cost_eur_year": {"type": "integer"},
            "heating_cost_notes": {"type": "string"},
            "optimal_bundle": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "estimated_price_eur": {"type": "string"},
                        "key_benefits": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["name"],
                },
            },
            "optimal_bundle_rationale": {"type": "string"},
            "optimal_bundle_total_cost_eur": {"type": "integer"},
            "financing_options": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "house_type_probability",
            "optimal_bundle",
            "financing_options",
        ],
    },
}


# ── helpers ─────────────────────────────────────────────────────────


def _get_sales_data(context: AgentContext) -> SalesData:
    raw = context.shared_state.get("sales_data")
    if isinstance(raw, SalesData):
        return raw
    if isinstance(raw, dict):
        return SalesData(**raw)
    return SalesData()


def _save_sales_data(context: AgentContext, data: SalesData) -> None:
    context.shared_state["sales_data"] = data.model_dump()


def _pick_kwp(house_type: str | None) -> float:
    if not house_type:
        return FALLBACK_DEFAULT_KWP
    key = house_type.strip().lower()
    for pattern, kwp in DEFAULT_KWP_BY_HOUSE_TYPE.items():
        if pattern in key:
            return kwp
    return FALLBACK_DEFAULT_KWP


async def _run_geocode(
    postal_code: str, http: httpx.AsyncClient
) -> GeocodeResult | None:
    try:
        return await geocode_postal_code(postal_code, client=http)
    except GeocodeError as exc:
        logger.warning(f"Nominatim geocoding failed: {exc}")
        return None


async def _run_pvgis(
    lat: float, lon: float, kwp: float, http: httpx.AsyncClient
) -> PVGISResult | None:
    try:
        return await estimate_pv_yield(lat=lat, lon=lon, kwp=kwp, client=http)
    except PVGISError as exc:
        logger.warning(f"PVGIS call failed: {exc}")
        return None


async def _run_smard(http: httpx.AsyncClient) -> SmardSeries | None:
    try:
        # Grab the last few daily slices so the average is stable.
        return await fetch_smard_series(
            filter_id=FILTER_DAY_AHEAD_PRICE,
            region="DE",
            resolution="day",
            window=7,
            client=http,
        )
    except SmardError as exc:
        logger.warning(f"SMARD call failed: {exc}")
        return None


def _apply_api_results(
    data: SalesData,
    geo: GeocodeResult | None,
    pv: PVGISResult | None,
    pv_kwp: float,
    smard: SmardSeries | None,
) -> list[str]:
    """Write API results into SalesData and return a short notes list."""
    notes: list[str] = []

    if geo:
        data.latitude = geo.lat
        data.longitude = geo.lon
        data.location_display_name = geo.display_name
    else:
        notes.append("Geocoding unavailable — PVGIS skipped.")

    if pv:
        data.assumed_system_kwp = pv_kwp
        data.solar_potential_kwh_year = int(round(pv.annual_kwh))
        data.solar_specific_yield_kwh_per_kwp = round(
            pv.specific_yield_kwh_per_kwp, 1
        )
        data.solar_optimal_tilt_deg = pv.optimal_tilt_deg
        data.solar_optimal_azimuth_deg = pv.optimal_azimuth_deg
        data.solar_monthly_kwh = [round(m, 1) for m in pv.monthly_kwh]
        data.solar_notes = (
            f"PVGIS assumes a {pv_kwp} kWp system at optimal tilt "
            f"{pv.optimal_tilt_deg}°, azimuth {pv.optimal_azimuth_deg}°."
        )
    elif geo:
        notes.append("PVGIS unavailable — solar estimate missing.")

    if smard:
        avg_mwh = smard.average
        latest_mwh = smard.latest
        if avg_mwh is not None:
            data.wholesale_price_eur_mwh_avg = round(avg_mwh, 2)
        if latest_mwh is not None:
            data.wholesale_price_eur_mwh_latest = round(latest_mwh, 2)
        if avg_mwh is not None:
            # Convert wholesale €/MWh → €/kWh, then add retail markup.
            wholesale_eur_kwh = avg_mwh / 1000.0
            data.local_electricity_price_eur_kwh = round(
                wholesale_eur_kwh + DEFAULT_RETAIL_MARKUP_EUR_KWH, 4
            )
            data.electricity_price_notes = (
                f"SMARD day-ahead avg {wholesale_eur_kwh*100:.1f} ct/kWh "
                f"(wholesale) + ~{DEFAULT_RETAIL_MARKUP_EUR_KWH*100:.0f} ct/kWh "
                f"retail markup (taxes/grid/levies)."
            )
    else:
        notes.append("SMARD unavailable — electricity price missing.")

    return notes


def _format_context_for_llm(data: SalesData) -> str:
    """Give the LLM everything it needs to synthesize the remaining fields."""
    snapshot = {
        "customer": {
            "name": data.customer_name,
            "postal_code": data.postal_code,
            "city": data.city,
            "location": data.location_display_name,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "product_interest": data.product_interest,
            "household_size": data.household_size,
            "house_type": data.house_type,
            "build_year": data.build_year,
            "roof_orientation": data.roof_orientation,
            "electricity_kwh_year": data.electricity_kwh_year,
            "heating_type": data.heating_type,
            "monthly_energy_bill_eur": data.monthly_energy_bill_eur,
            "existing_assets": data.existing_assets,
            "financial_profile": data.financial_profile,
            "notes": data.notes,
        },
        "solar": {
            "assumed_system_kwp": data.assumed_system_kwp,
            "annual_kwh": data.solar_potential_kwh_year,
            "specific_yield_kwh_per_kwp": data.solar_specific_yield_kwh_per_kwp,
            "optimal_tilt_deg": data.solar_optimal_tilt_deg,
            "optimal_azimuth_deg": data.solar_optimal_azimuth_deg,
            "monthly_kwh": data.solar_monthly_kwh,
        },
        "electricity": {
            "wholesale_eur_mwh_avg": data.wholesale_price_eur_mwh_avg,
            "wholesale_eur_mwh_latest": data.wholesale_price_eur_mwh_latest,
            "retail_estimate_eur_kwh": data.local_electricity_price_eur_kwh,
        },
        "research": {
            "regional_incentives": data.regional_incentives,
            "market_trends": data.market_trends,
        },
    }
    return json.dumps(snapshot, indent=2, default=str)


def _apply_llm_output(data: SalesData, tool_input: dict[str, Any]) -> None:
    if "house_type_probability" in tool_input:
        raw = tool_input["house_type_probability"] or {}
        if isinstance(raw, dict):
            cleaned: dict[str, float] = {}
            for k, v in raw.items():
                try:
                    cleaned[str(k)] = float(v)
                except (TypeError, ValueError):
                    continue
            if cleaned:
                data.house_type_probability = cleaned
    if tool_input.get("house_type_reasoning"):
        data.house_type_reasoning = str(tool_input["house_type_reasoning"])

    if tool_input.get("current_heating_cost_eur_year") is not None:
        try:
            data.current_heating_cost_eur_year = int(
                tool_input["current_heating_cost_eur_year"]
            )
        except (TypeError, ValueError):
            pass
    if tool_input.get("heating_cost_notes"):
        data.heating_cost_notes = str(tool_input["heating_cost_notes"])

    bundle_raw = tool_input.get("optimal_bundle") or []
    bundle: list[ProductRecommendation] = []
    for item in bundle_raw:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        bundle.append(
            ProductRecommendation(
                name=str(item["name"]),
                description=str(item.get("description", "")),
                estimated_price_eur=str(item.get("estimated_price_eur", "")),
                key_benefits=[
                    str(b) for b in (item.get("key_benefits") or []) if b
                ],
            )
        )
    if bundle:
        data.optimal_bundle = bundle

    if tool_input.get("optimal_bundle_rationale"):
        data.optimal_bundle_rationale = str(tool_input["optimal_bundle_rationale"])
    if tool_input.get("optimal_bundle_total_cost_eur") is not None:
        try:
            data.optimal_bundle_total_cost_eur = int(
                tool_input["optimal_bundle_total_cost_eur"]
            )
        except (TypeError, ValueError):
            pass

    fin_raw = tool_input.get("financing_options") or []
    if fin_raw:
        data.financing_options = [str(f) for f in fin_raw if f]


def _build_summary(data: SalesData, api_notes: list[str]) -> str:
    lines = ["## Analysis complete"]

    if data.location_display_name:
        lines.append(
            f"**Location:** {data.location_display_name} "
            f"(lat {data.latitude}, lon {data.longitude})"
        )

    if data.solar_potential_kwh_year is not None:
        lines.append(
            f"**Solar potential (PVGIS):** ~{data.solar_potential_kwh_year:,} kWh/year "
            f"for a {data.assumed_system_kwp} kWp system "
            f"(specific yield ~{data.solar_specific_yield_kwh_per_kwp:.0f} kWh/kWp, "
            f"optimal tilt {data.solar_optimal_tilt_deg}°, "
            f"azimuth {data.solar_optimal_azimuth_deg}°)."
        )

    if data.local_electricity_price_eur_kwh is not None:
        lines.append(
            f"**Electricity price (retail est.):** "
            f"~{data.local_electricity_price_eur_kwh*100:.1f} ct/kWh "
            f"(SMARD wholesale avg "
            f"{(data.wholesale_price_eur_mwh_avg or 0)/10:.1f} ct/kWh + markup)."
        )

    if data.house_type_probability:
        top = sorted(
            data.house_type_probability.items(), key=lambda x: x[1], reverse=True
        )[:3]
        lines.append(
            "**House type probability:** "
            + ", ".join(f"{k} {v*100:.0f}%" for k, v in top)
        )
        if data.house_type_reasoning:
            lines.append(f"> {data.house_type_reasoning}")

    if data.current_heating_cost_eur_year is not None:
        lines.append(
            f"**Current heating costs:** ~€{data.current_heating_cost_eur_year:,}/year"
        )
        if data.heating_cost_notes:
            lines.append(f"> {data.heating_cost_notes}")

    if data.optimal_bundle:
        lines.append("**Optimal product bundle:**")
        for item in data.optimal_bundle:
            price = f" — {item.estimated_price_eur}" if item.estimated_price_eur else ""
            lines.append(f"- **{item.name}**{price}: {item.description}")
        if data.optimal_bundle_total_cost_eur is not None:
            lines.append(
                f"**Bundle total (est.):** €{data.optimal_bundle_total_cost_eur:,}"
            )
        if data.optimal_bundle_rationale:
            lines.append(f"> {data.optimal_bundle_rationale}")

    if data.financing_options:
        lines.append("**Financing options:**")
        for opt in data.financing_options:
            lines.append(f"- {opt}")

    if api_notes:
        lines.append("\n_Data source notes:_")
        for note in api_notes:
            lines.append(f"- {note}")

    lines.append("\nReady for the strategy phase.")
    return "\n".join(lines)


# ── agent ───────────────────────────────────────────────────────────


@dataclass
class AnalysisAgent(BaseAgent):
    name: str = "analysis"
    description: str = (
        "Infers solar potential, electricity prices, heating costs, "
        "optimal product bundle, and financing options from real APIs + LLM."
    )
    system_prompt: str = SYSTEM_PROMPT
    tools: list[Any] = field(default_factory=list)

    async def execute(
        self, context: AgentContext, message: AgentMessage
    ) -> AgentMessage:
        sales_data = _get_sales_data(context)

        # Pick a reasonable system size to ask PVGIS about.
        kwp = _pick_kwp(sales_data.house_type)

        api_notes: list[str] = []
        geo: GeocodeResult | None = None
        pv: PVGISResult | None = None
        smard: SmardSeries | None = None

        async with httpx.AsyncClient(timeout=30.0) as http:
            # SMARD runs independently of the others.
            smard_task = asyncio.create_task(_run_smard(http))

            if sales_data.postal_code:
                geo = await _run_geocode(sales_data.postal_code, http)
                if geo:
                    pv = await _run_pvgis(geo.lat, geo.lon, kwp, http)
            else:
                api_notes.append(
                    "No postal_code on file — skipped geocoding + PVGIS."
                )

            smard = await smard_task

        api_notes.extend(_apply_api_results(sales_data, geo, pv, kwp, smard))

        # Now let Gemini fill in house_type_probability, heating_costs,
        # optimal_bundle, financing_options — grounded in the API results.
        context_json = _format_context_for_llm(sales_data)
        system = (
            self.system_prompt
            + "\n\nContext snapshot (ground your answers in these numbers):\n"
            + context_json
        )

        messages = [
            {
                "role": "user",
                "content": (
                    "Run the analysis now and call store_analysis with the "
                    "inferred values."
                ),
            }
        ]

        try:
            response = await chat_completion(
                model=self.model,
                max_tokens=2048,
                system=system,
                messages=messages,
                tools=[STORE_ANALYSIS_TOOL],
            )
        except Exception as exc:
            logger.error(f"AnalysisAgent LLM call failed: {exc}")
            response = None

        if response:
            for tc in response.tool_calls:
                if tc.name == "store_analysis":
                    _apply_llm_output(sales_data, tc.input)

        # Advance phase once we have the minimum viable outputs.
        if sales_data.is_analysis_complete():
            sales_data.phase = SalesPhase.STRATEGY

        _save_sales_data(context, sales_data)

        summary = _build_summary(sales_data, api_notes)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=summary,
            agent_name=self.name,
            metadata={
                "phase": sales_data.phase.value,
                "sales_data": sales_data.model_dump(),
            },
        )

    async def plan(self, context: AgentContext, task: str) -> list[str]:
        return [
            "Geocode postal code via Nominatim",
            "Call PVGIS for solar yield and optimal angles",
            "Fetch SMARD day-ahead wholesale price",
            "Infer house type probability, heating costs, bundle, financing",
            "Store structured analysis in SalesData",
        ]

    async def can_handle(self, message: AgentMessage) -> float:
        return 0.2
