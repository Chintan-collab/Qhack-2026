def build_financing_options(packages, best_package_name):
    selected = next(pkg for pkg in packages if pkg["name"] == best_package_name)
    capex = selected["capex"]

    financing = [
        {
            "type": "Cash",
            "monthly_payment": 0,
            "total_cost": capex,
            "fit_reason": "Best for customers who want the lowest total cost and can pay upfront.",
        },
        {
            "type": "Partial Finance",
            "monthly_payment": round(capex * 0.02, 2),
            "total_cost": round(capex * 1.08, 2),
            "fit_reason": "Strong middle-ground option for reducing upfront burden while keeping total cost moderate.",
        },
        {
            "type": "Full Finance",
            "monthly_payment": round(capex * 0.035, 2),
            "total_cost": round(capex * 1.18, 2),
            "fit_reason": "Best for customers who prioritize affordability of monthly payments over lowest total cost.",
        },
    ]

    recommended_financing = "Partial Finance"
    if capex <= 9000:
        recommended_financing = "Cash"
    elif capex >= 17000:
        recommended_financing = "Full Finance"

    for option in financing:
        option["recommended"] = option["type"] == recommended_financing

    return financing