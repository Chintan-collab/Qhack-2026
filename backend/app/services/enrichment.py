def enrich_lead(lead: dict) -> dict:
    confidence = 100
    assumptions = []

    if not lead.get("household_size"):
        lead["household_size"] = 2
        assumptions.append("Household size defaulted to 2")
        confidence -= 5

    if not lead.get("annual_consumption_kwh"):
        lead["annual_consumption_kwh"] = 2500 + lead["household_size"] * 500
        assumptions.append("Consumption estimated from household size")
        confidence -= 10

    if not lead.get("budget_band"):
        assumptions.append("Budget band not provided")
        confidence -= 8

    if not lead.get("customer_goal"):
        assumptions.append("Customer goal not provided")
        confidence -= 5

    product_interest = (lead.get("product_interest") or "solar").lower()

    if "heat" in product_interest:
        lead["market_context"] = (
            "Heating electrification is becoming more relevant as households look for lower long-term heating costs, "
            "reduced dependence on conventional heating systems, and more manageable upfront adoption through financing."
        )
        lead["heating_upgrade_signal"] = "high relevance"
        lead["likely_objection"] = "high upfront installation cost"
        lead["recommended_opening"] = (
            "Many households are looking for a practical way to modernize heating without carrying the full upfront cost at once."
        )
        if "current_heating_type" not in lead:
            assumptions.append("Current heating system not provided")
            confidence -= 12

    elif "wallbox" in product_interest:
        lead["market_context"] = (
            "Home charging is becoming increasingly important for EV-owning households, especially when combined with smart charging "
            "and future energy-system integration."
        )
        lead["ev_readiness_signal"] = "moderate to high relevance"
        lead["likely_objection"] = "whether the installation is worth the investment right now"
        lead["recommended_opening"] = (
            "This solution makes home charging more convenient today and creates a better foundation for future energy upgrades."
        )

    elif "battery" in product_interest:
        lead["market_context"] = (
            "Solar-plus-storage solutions are increasingly attractive for households that want stronger control over electricity costs, "
            "greater self-consumption, and more resilience against price volatility."
        )
        lead["solar_potential"] = "moderate to high"
        lead["likely_objection"] = "battery cost versus perceived payback"
        lead["recommended_opening"] = (
            "This setup helps the household use more of its own solar energy and reduce reliance on grid electricity."
        )

    else:
        lead["market_context"] = (
            "Solar adoption remains attractive for households seeking lower electricity bills, long-term savings, "
            "and a stronger path toward energy independence."
        )
        lead["solar_potential"] = "moderate"
        lead["likely_objection"] = "upfront investment"
        lead["recommended_opening"] = (
            "This is a practical way to reduce electricity costs while building long-term value into the property."
        )

    lead["confidence"] = max(confidence, 45)
    lead["assumptions"] = assumptions

    return lead