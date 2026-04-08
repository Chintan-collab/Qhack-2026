def build_report(enriched, packages, financing, ai_summary, best_package):
    product_interest = (enriched.get("product_interest") or "").lower()

    market_context = {
        "summary": enriched.get("market_context", "No market context available."),
    }

    if "solar" in product_interest or "battery" in product_interest:
        market_context["relevance_signal"] = enriched.get("solar_potential", "estimated")
    elif "heat" in product_interest:
        market_context["relevance_signal"] = enriched.get("heating_upgrade_signal", "high relevance")
    elif "wallbox" in product_interest:
        market_context["relevance_signal"] = enriched.get("ev_readiness_signal", "moderate relevance")
    else:
        market_context["relevance_signal"] = "estimated"

    best_package_data = next((pkg for pkg in packages if pkg["name"] == best_package), None)
    recommended_finance = next((f for f in financing if f.get("recommended")), None)

    return {
        "customer_summary": {
            "postcode": enriched["postcode"],
            "product_interest": enriched["product_interest"],
            "estimated_profile": (
                f"Household size {enriched['household_size']} with annual consumption "
                f"{enriched['annual_consumption_kwh']} kWh"
            ),
            "customer_goal": enriched.get("customer_goal") or "Not provided",
            "budget_band": enriched.get("budget_band") or "Not provided",
        },
        "market_context": market_context,
        "recommended_packages": packages,
        "best_package": best_package,
        "best_package_details": best_package_data,
        "financing_options": financing,
        "recommended_financing": recommended_finance,
        "installer_pitch": {
            "recommended_opening": enriched.get("recommended_opening", "Lead with value, affordability, and practical next steps."),
            "likely_objection": enriched.get("likely_objection", "Upfront cost may be the main concern."),
            "sales_focus": enriched.get("sales_focus", "Position the solution around savings, practicality, and financing flexibility."),
        },
        "ai_summary": ai_summary,
        "confidence": enriched["confidence"],
        "assumptions": enriched["assumptions"],
    }