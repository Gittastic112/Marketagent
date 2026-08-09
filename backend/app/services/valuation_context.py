from app.models import Company


def build_company_valuation_context(company: Company) -> dict:
    market = (company.market or "US").upper()
    if market == "IN":
        country = company.country or "India"
        currency = company.currency or "INR"
        recommended_benchmark_country = "India"
    elif market == "US":
        country = company.country or "United States"
        currency = company.currency or "USD"
        recommended_benchmark_country = "United States"
    else:
        country = company.country or "Unknown"
        currency = company.currency or "USD"
        recommended_benchmark_country = country

    warnings = ["Cash flows and discount rate must be in the same currency."]
    if market == "IN":
        warnings.append("Do not use a US risk-free rate with INR cash flows without an explicit currency adjustment.")

    return {
        "company_id": company.id,
        "market": market,
        "country": country,
        "default_currency": currency,
        "cash_flow_currency": currency,
        "discount_rate_currency": currency,
        "available_benchmark_countries": ["India", "United States"],
        "recommended_benchmark_country": recommended_benchmark_country,
        "benchmark_source": "Damodaran/local benchmarks",
        "warnings": warnings,
    }
