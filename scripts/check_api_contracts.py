"""Export the critical wire contracts checked by both backend and frontend CI.

Run with the backend's Python dependencies. Regenerate explicitly after an
intentional contract change, then review the manifest diff and both test suites.
"""
import argparse
import json
from pathlib import Path
from typing import Any

from app.schemas import ai_consent, brief, companies, evidence, financials, market, operations, research
from app.schemas.common import ApiErrorDetail, ApiMeta, ApiResponse

CONTRACTS = {
    "contract": {"ApiMeta": ApiMeta, "ApiErrorDetail": ApiErrorDetail, "ApiResponse": ApiResponse[Any]},
    "companies": {"Company": companies.CompanyRead, "ExposureTag": companies.ExposureTagRead, "Source": evidence.SourceRead},
    "daily-brief": {
        "DailyBriefPayload": brief.DailyBriefPayload, "DailyBrief": brief.DailyBriefRead,
        "SavedDailyBrief": brief.DailyBriefRead, "DailyBriefSchedule": brief.DailyBriefScheduleRead,
        "DailyBriefScheduleRunResult": brief.DailyBriefScheduleRunResult,
    },
    "operations": {"ProcessingRun": operations.ProcessingRunRead, "RuntimeReadiness": operations.RuntimeReadinessRead},
    "market": {"MarketPrice": market.MarketPriceRead, "CompanyMarketData": market.CompanyMarketDataRead},
    "research": {"ResearchSession": research.ResearchSessionDetail, "ResearchMessage": research.ResearchMessageRead,
                 "DecisionLog": research.DecisionLogRead, "OutcomeReview": research.OutcomeReviewRead,
                 "EvidenceLedgerItem": research.EvidenceLedgerItemRead, "VariantPerception": research.VariantPerceptionRead},
    "financials": {"FinancialExtractionCandidate": financials.FinancialExtractionCandidateRead},
    "ai-consent": {
        "AIConsentDecision": ai_consent.AIConsentDecisionRead,
        "AIConsentAction": ai_consent.AIConsentActionRead,
        "AIConsentOverview": ai_consent.AIConsentOverview,
        "AIConsentHistory": ai_consent.AIConsentHistory,
    },
}
MANIFEST = Path(__file__).resolve().parents[1] / "data/contracts/frontend-backend.json"


def contract_manifest():
    return {
        "format_version": 1,
        "contracts": {
            module: {name: model.model_json_schema(mode="serialization", by_alias=True) for name, model in models.items()}
            for module, models in CONTRACTS.items()
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Replace the reviewed contract manifest")
    parser.add_argument("--output", type=Path, default=MANIFEST)
    args = parser.parse_args()
    expected = contract_manifest()
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n")
    elif json.loads(args.output.read_text()) != expected:
        raise SystemExit("Backend wire contracts changed. Review and regenerate the contract manifest.")
    print(f"Verified {sum(len(models) for models in CONTRACTS.values())} frontend/backend contracts")


if __name__ == "__main__":
    main()
