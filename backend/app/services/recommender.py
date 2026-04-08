def recommend_packages(profile: dict):
    kwh = profile.get("annual_consumption_kwh", 0)
    product_interest = (profile.get("product_interest") or "solar").lower()
    budget_band = (profile.get("budget_band") or "").lower()
    household_size = profile.get("household_size", 2)

    # Heat pump packages
    if "heat" in product_interest:
        packages = [
            {
                "name": "Starter",
                "system": "Heat pump basic package",
                "capex": 12000,
                "annual_savings": 1100,
                "fit_reason": "Best for budget-sensitive households looking for an entry-level heating upgrade.",
                "sales_pitch": "Lead with lower heating cost volatility and financing flexibility.",
                "target_customer": "Cost-conscious households replacing conventional heating.",
            },
            {
                "name": "Recommended",
                "system": "Heat pump + optimization package",
                "capex": 16500,
                "annual_savings": 1700,
                "fit_reason": "Balanced package for households seeking stronger efficiency and better long-term value.",
                "sales_pitch": "Position this as the strongest balance of savings, comfort, and affordability.",
                "target_customer": "Households looking for a practical long-term upgrade.",
            },
            {
                "name": "Premium",
                "system": "Heat pump + optimization + smart controls",
                "capex": 22000,
                "annual_savings": 2300,
                "fit_reason": "Best for households prioritizing efficiency, smart-home readiness, and long-term performance.",
                "sales_pitch": "Lead with future-proofing, efficiency, and comfort optimization.",
                "target_customer": "High-intent households focused on premium electrification.",
            },
        ]

        if budget_band == "low":
            best = "Starter"
        elif budget_band == "high":
            best = "Premium"
        elif kwh >= 3500 or household_size >= 3:
            best = "Recommended"
        else:
            best = "Starter"

    # Wallbox packages
    elif "wallbox" in product_interest:
        packages = [
            {
                "name": "Starter",
                "system": "Basic wallbox package",
                "capex": 1800,
                "annual_savings": 250,
                "fit_reason": "Simple entry option for EV charging at home.",
                "sales_pitch": "Lead with convenience and readiness for daily home charging.",
                "target_customer": "First-time EV households.",
            },
            {
                "name": "Recommended",
                "system": "Smart wallbox + load management",
                "capex": 2800,
                "annual_savings": 450,
                "fit_reason": "Best mix of smart charging, usability, and long-term flexibility.",
                "sales_pitch": "Position this as the practical choice for optimized charging and future energy integration.",
                "target_customer": "Households that want smarter control and better energy usage.",
            },
            {
                "name": "Premium",
                "system": "Smart wallbox + load management + solar integration readiness",
                "capex": 4200,
                "annual_savings": 650,
                "fit_reason": "Designed for households planning broader home-energy optimization.",
                "sales_pitch": "Lead with future readiness and integration with solar or battery systems.",
                "target_customer": "Homeowners planning integrated energy systems.",
            },
        ]

        if budget_band == "low":
            best = "Starter"
        elif budget_band == "high":
            best = "Premium"
        else:
            best = "Recommended"

    # Solar + battery packages
    elif "battery" in product_interest:
        packages = [
            {
                "name": "Starter",
                "system": "5 kWp solar + entry battery package",
                "capex": 10500,
                "annual_savings": 1200,
                "fit_reason": "Good entry point for households seeking bill reduction and some storage benefits.",
                "sales_pitch": "Lead with self-consumption and better control over electricity costs.",
                "target_customer": "Smaller households starting with solar + storage.",
            },
            {
                "name": "Recommended",
                "system": "7 kWp solar + 5 kWh battery",
                "capex": 13500,
                "annual_savings": 1700,
                "fit_reason": "Strong balance of generation, storage, and financing affordability.",
                "sales_pitch": "Position this as the best conversion package for savings and manageable monthly payments.",
                "target_customer": "Medium-demand households looking for balanced value.",
            },
            {
                "name": "Premium",
                "system": "10 kWp solar + 10 kWh battery",
                "capex": 19000,
                "annual_savings": 2450,
                "fit_reason": "Best for high-consumption households that want maximum independence and storage value.",
                "sales_pitch": "Lead with energy independence and long-term savings.",
                "target_customer": "Larger or higher-usage households.",
            },
        ]

        if budget_band == "low":
            best = "Starter"
        elif budget_band == "high":
            best = "Premium"
        elif kwh <= 3000:
            best = "Starter"
        elif kwh <= 5500:
            best = "Recommended"
        else:
            best = "Premium"

    # Solar packages
    else:
        packages = [
            {
                "name": "Starter",
                "system": "5 kWp solar package",
                "capex": 8000,
                "annual_savings": 900,
                "fit_reason": "Best for smaller households starting their solar journey with lower upfront cost.",
                "sales_pitch": "Lead with affordability and immediate bill reduction.",
                "target_customer": "Budget-conscious households with moderate consumption.",
            },
            {
                "name": "Recommended",
                "system": "7 kWp solar + efficiency optimization",
                "capex": 12500,
                "annual_savings": 1550,
                "fit_reason": "Most balanced option for savings, system size, and financing comfort.",
                "sales_pitch": "Position this as the most practical package for long-term value.",
                "target_customer": "Households wanting the strongest balance between capex and savings.",
            },
            {
                "name": "Premium",
                "system": "10 kWp solar + premium optimization package",
                "capex": 18000,
                "annual_savings": 2200,
                "fit_reason": "Best for households prioritizing maximum production and long-term upside.",
                "sales_pitch": "Lead with energy independence and stronger long-term savings.",
                "target_customer": "Larger households or high-consumption homeowners.",
            },
        ]

        if budget_band == "low":
            best = "Starter"
        elif budget_band == "high":
            best = "Premium"
        elif kwh <= 3500:
            best = "Starter"
        elif kwh <= 5500:
            best = "Recommended"
        else:
            best = "Premium"

    return packages, best