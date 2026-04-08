def generate_ai_summary(enriched, packages, financing, best_package):
    goal = enriched.get("customer_goal") or "cost savings"
    product_interest = (enriched.get("product_interest") or "clean-energy solution").replace("_", " ")
    confidence = enriched.get("confidence", 0)

    best_package_data = next((pkg for pkg in packages if pkg["name"] == best_package), None)
    recommended_finance = next((f for f in financing if f.get("recommended")), None)

    fit_reason = best_package_data.get("fit_reason") if best_package_data else "It offers the strongest overall fit."
    sales_pitch = best_package_data.get("sales_pitch") if best_package_data else "Lead with value and financing flexibility."

    finance_line = (
        f"The recommended financing route is {recommended_finance['type']}, "
        f"which supports affordability while keeping the offer practical."
        if recommended_finance
        else "Flexible financing should be used to reduce adoption barriers."
    )

    likely_objection = enriched.get("likely_objection", "upfront investment")
    recommended_opening = enriched.get(
        "recommended_opening",
        "Start with the practical value of the solution and then connect it to monthly affordability."
    )

    return (
        f"This lead shows interest in {product_interest} and is primarily motivated by {goal}. "
        f"The strongest package recommendation is {best_package} because {fit_reason} "
        f"{sales_pitch} "
        f"{finance_line} "
        f"The most likely objection is {likely_objection}. "
        f"A strong opener would be: {recommended_opening} "
        f"Current report confidence is {confidence}/100."
    )