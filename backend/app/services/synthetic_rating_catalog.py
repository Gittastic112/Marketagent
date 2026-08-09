from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class SyntheticRatingFirmType(str, Enum):
    LARGE_NON_FINANCIAL = "large_non_financial"
    SMALL_OR_RISKY = "small_or_risky"
    FINANCIAL_SERVICE = "financial_service"


@dataclass(frozen=True, slots=True)
class SyntheticRatingBand:
    lower_bound: float
    upper_bound: float
    rating: str
    default_spread: float


@dataclass(frozen=True, slots=True)
class SyntheticRatingSource:
    source_filename: str
    canonical_path: str
    runtime_mirror_path: str
    sha256: str
    source_as_of: str
    date_confidence: str
    catalog_version: str
    recency_claim_type: str
    recency_basis: str
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SYNTHETIC_RATING_SOURCE = SyntheticRatingSource(
    source_filename="ratings.xls",
    canonical_path="raw/models/ratings.xls",
    runtime_mirror_path="data/damodaran/raw/ratings.xls",
    sha256="45d1f61c67f02fb595661e95ef294e72524a105c9db85ee198a918386d580d3c",
    source_as_of="unknown",
    date_confidence="low",
    catalog_version="ratings-xls-45d1f61c67f0",
    recency_claim_type="User Assumption",
    recency_basis=(
        "User approved treating this undated workbook as recent for the current "
        "local workflow on 2026-08-07."
    ),
    limitations=(
        "The workbook does not provide a reliable source date for the spread table.",
        "Interest coverage must already reflect any required operating-lease capitalization.",
        "The table estimates a default spread; it does not replace an observable market cost of debt.",
    ),
)


SYNTHETIC_RATING_CATALOG: dict[
    SyntheticRatingFirmType,
    tuple[SyntheticRatingBand, ...],
] = {
    SyntheticRatingFirmType.LARGE_NON_FINANCIAL: (
        SyntheticRatingBand(-100000.0, 0.199999, "D2/D", 0.19),
        SyntheticRatingBand(0.2, 0.649999, "C2/C", 0.16),
        SyntheticRatingBand(0.65, 0.799999, "Ca2/CC", 0.1261),
        SyntheticRatingBand(0.8, 1.249999, "Caa/CCC", 0.0885),
        SyntheticRatingBand(1.25, 1.499999, "B3/B-", 0.0509),
        SyntheticRatingBand(1.5, 1.749999, "B2/B", 0.0321),
        SyntheticRatingBand(1.75, 1.999999, "B1/B+", 0.0275),
        SyntheticRatingBand(2.0, 2.2499999, "Ba2/BB", 0.0184),
        SyntheticRatingBand(2.25, 2.49999, "Ba1/BB+", 0.0138),
        SyntheticRatingBand(2.5, 2.999999, "Baa2/BBB", 0.0111),
        SyntheticRatingBand(3.0, 4.249999, "A3/A-", 0.0089),
        SyntheticRatingBand(4.25, 5.499999, "A2/A", 0.0078),
        SyntheticRatingBand(5.5, 6.499999, "A1/A+", 0.007),
        SyntheticRatingBand(6.5, 8.499999, "Aa2/AA", 0.0055),
        SyntheticRatingBand(8.5, 100000.0, "Aaa/AAA", 0.004),
    ),
    SyntheticRatingFirmType.SMALL_OR_RISKY: (
        SyntheticRatingBand(-100000.0, 0.499999, "D2/D", 0.19),
        SyntheticRatingBand(0.5, 0.799999, "C2/C", 0.16),
        SyntheticRatingBand(0.8, 1.249999, "Ca2/CC", 0.1261),
        SyntheticRatingBand(1.25, 1.499999, "Caa/CCC", 0.0885),
        SyntheticRatingBand(1.5, 1.999999, "B3/B-", 0.0509),
        SyntheticRatingBand(2.0, 2.499999, "B2/B", 0.0321),
        SyntheticRatingBand(2.5, 2.999999, "B1/B+", 0.0275),
        SyntheticRatingBand(3.0, 3.499999, "Ba2/BB", 0.0184),
        SyntheticRatingBand(3.5, 3.9999999, "Ba1/BB+", 0.0138),
        SyntheticRatingBand(4.0, 4.499999, "Baa2/BBB", 0.0111),
        SyntheticRatingBand(4.5, 5.999999, "A3/A-", 0.0089),
        SyntheticRatingBand(6.0, 7.499999, "A2/A", 0.0078),
        SyntheticRatingBand(7.5, 9.499999, "A1/A+", 0.007),
        SyntheticRatingBand(9.5, 12.499999, "Aa2/AA", 0.0055),
        SyntheticRatingBand(12.5, 100000.0, "Aaa/AAA", 0.004),
    ),
    SyntheticRatingFirmType.FINANCIAL_SERVICE: (
        SyntheticRatingBand(-100000.0, 0.049999, "D2/D", 0.19),
        SyntheticRatingBand(0.05, 0.099999, "C2/C", 0.16),
        SyntheticRatingBand(0.1, 0.199999, "Ca2/CC", 0.1261),
        SyntheticRatingBand(0.2, 0.299999, "Caa/CCC", 0.0885),
        SyntheticRatingBand(0.3, 0.399999, "B3/B-", 0.0509),
        SyntheticRatingBand(0.4, 0.499999, "B2/B", 0.0321),
        SyntheticRatingBand(0.5, 0.599999, "B1/B+", 0.0275),
        SyntheticRatingBand(0.6, 0.749999, "Ba2/BB", 0.0184),
        SyntheticRatingBand(0.75, 0.899999, "Ba1/BB+", 0.0138),
        SyntheticRatingBand(0.9, 1.199999, "Baa2/BBB", 0.0111),
        SyntheticRatingBand(1.2, 1.49999, "A3/A-", 0.0089),
        SyntheticRatingBand(1.5, 1.99999, "A2/A", 0.0078),
        SyntheticRatingBand(2.0, 2.49999, "A1/A+", 0.007),
        SyntheticRatingBand(2.5, 2.99999, "Aa2/AA", 0.0055),
        SyntheticRatingBand(3.0, 100000.0, "Aaa/AAA", 0.004),
    ),
}
