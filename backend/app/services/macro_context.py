from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark


DEFAULT_MACRO_MARKET = "IN"
DEFAULT_MACRO_COUNTRY = "India"
DEFAULT_CLASSIFICATION_SYSTEM = "SIC"
DEFAULT_CURRENCY_CONTEXT = "INR"
DEFAULT_CURRENCY_VARIABLE_DESCRIPTION = (
    "Source file currency movement convention not fully verified."
)
NEGATIVE_DURATION_WARNING = (
    "Negative raw duration means the sector coefficient is positive to rate changes "
    "or source convention differs. Treat as source coefficient, not normal bond-like duration."
)


def duration_magnitude(duration: float | None) -> float | None:
    if duration is None:
        return None
    return abs(duration)


def duration_interpretation(duration: float | None) -> str:
    if duration is None:
        return "No source duration coefficient available."
    if duration < 0:
        return NEGATIVE_DURATION_WARNING
    return "Positive raw duration is preserved from the source coefficient."


def benchmark_context(benchmark: SectorMacroSensitivityBenchmark) -> dict[str, object]:
    raw_duration = benchmark.firm_value_duration
    return {
        "market": benchmark.market,
        "country": benchmark.country,
        "classification_system": benchmark.classification_system,
        "currency_context": benchmark.currency_context,
        "currency_variable_description": benchmark.currency_variable_description,
        "raw_duration": raw_duration,
        "duration_magnitude": duration_magnitude(raw_duration),
        "duration_interpretation": duration_interpretation(raw_duration),
    }
