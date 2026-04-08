from enum import Enum

from pydantic import BaseModel


class SalesPhase(str, Enum):
    DATA_GATHERING = "data_gathering"
    RESEARCH = "research"
    STRATEGY = "strategy"
    DELIVERABLE = "deliverable"
    COMPLETE = "complete"


class ProductRecommendation(BaseModel):
    """A product the installer can offer this customer."""
    name: str  # e.g. "Solar PV 10 kWp", "Heat pump Vaillant aroTHERM"
    description: str = ""
    estimated_price_eur: str = ""
    key_benefits: list[str] = []


class CompetitorInfo(BaseModel):
    name: str
    description: str = ""
    strengths: list[str] = []
    weaknesses: list[str] = []
    market_share: str = ""


class ObjectionResponse(BaseModel):
    objection: str
    response: str


class SalesData(BaseModel):
    """Structured data accumulated by agents throughout the sales pipeline.

    Context: An energy installer (solar, heat pumps, wallboxes, batteries)
    uses this to build a personalized pitch for a residential customer.
    """

    # Phase tracking
    phase: SalesPhase = SalesPhase.DATA_GATHERING

    # ── Customer & property info (data gathering) ───────────────
    customer_name: str | None = None
    postal_code: str | None = None
    city: str | None = None
    product_interest: str | None = None  # "Solar", "Heat pump", "Wallbox", etc.
    household_size: int | None = None
    house_type: str | None = None  # "Detached", "Semi-detached", "Townhouse", etc.
    build_year: int | None = None
    roof_orientation: str | None = None
    electricity_kwh_year: int | None = None
    heating_type: str | None = None  # "Gas", "Oil", "Heat pump", "District heating"
    monthly_energy_bill_eur: int | None = None
    existing_assets: str | None = None  # "None", "Solar 5 kWp", etc.
    financial_profile: str | None = None
    notes: str | None = None

    # ── Product recommendations ─────────────────────────────────
    recommendations: list[ProductRecommendation] = []

    # ── Research fields ─────────────────────────────────────────
    competitors: list[CompetitorInfo] = []
    market_trends: list[str] = []
    regional_incentives: list[str] = []  # subsidies, tax credits, local programs
    energy_price_outlook: str | None = None
    industry_insights: list[str] = []

    # ── Strategy fields ─────────────────────────────────────────
    positioning: str | None = None
    value_proposition: str | None = None
    key_messages: list[str] = []
    objections: list[ObjectionResponse] = []
    savings_estimate: str | None = None  # e.g. "~€1,200/year"
    payback_period: str | None = None  # e.g. "~8 years"
    financing_options: list[str] = []

    def is_gathering_complete(self) -> bool:
        """Minimum data to proceed: we need the customer, property, and interest."""
        return bool(
            self.customer_name
            and self.product_interest
            and self.house_type
            and self.heating_type
        )

    def is_research_complete(self) -> bool:
        return bool(self.regional_incentives or self.market_trends)

    def is_strategy_complete(self) -> bool:
        return bool(self.value_proposition and self.key_messages)
