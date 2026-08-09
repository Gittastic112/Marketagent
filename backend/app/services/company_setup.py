import logging
import os

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    CompanySetupIdentityResolution,
    CompanySetupSourceReadiness,
    CompanySetupStepUpdate,
    CompanySetupWorkflowRead,
)
from app.models import Company
from app.models.company_setup import CompanySetupWorkflow
from app.services.sec_ingestion import lookup_cik_for_ticker


DEFAULT_SEC_USER_AGENT = "Market Intelligence Engine local research app"
logger = logging.getLogger(__name__)


def get_or_start_company_setup(db: Session, company_id: int) -> CompanySetupWorkflowRead:
    company = _get_company(db, company_id)
    workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company_id))
    if workflow is None:
        workflow = CompanySetupWorkflow(
            company_id=company_id,
            current_step=_initial_step(company),
            identity_status=_initial_identity_status(company),
            source_status=_source_status(company),
            filing_status="missing",
            financial_extraction_status="missing",
            industry_mapping_status="missing",
            valuation_readiness_status="blocked",
            security_review_status="local_only",
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
    return workflow_response(workflow, company)


def get_company_setup(db: Session, company_id: int) -> CompanySetupWorkflowRead:
    company = _get_company(db, company_id)
    workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company_id))
    if workflow is None:
        raise HTTPException(status_code=404, detail="Company setup workflow not found")
    return workflow_response(workflow, company)


def update_company_setup_step(db: Session, company_id: int, payload: CompanySetupStepUpdate) -> CompanySetupWorkflowRead:
    company = _get_company(db, company_id)
    workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company_id))
    if workflow is None:
        raise HTTPException(status_code=404, detail="Company setup workflow not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(workflow, field, value)

    db.commit()
    db.refresh(workflow)
    return workflow_response(workflow, company)


def confirm_company_identity(db: Session, company_id: int) -> CompanySetupWorkflowRead:
    company = _get_company(db, company_id)
    workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company_id))
    if workflow is None:
        workflow = CompanySetupWorkflow(company_id=company_id)
        db.add(workflow)

    workflow.identity_status = "reviewed"
    workflow.current_step = "source_setup"
    workflow.source_status = _source_status(company)
    db.commit()
    db.refresh(workflow)
    return workflow_response(workflow, company)


def resolve_company_identity(db: Session, company_id: int) -> CompanySetupIdentityResolution:
    company = _get_company(db, company_id)
    warnings: list[str] = []

    if (company.market or "US").upper() == "US" and not company.cik:
        try:
            cik = lookup_cik_for_ticker(company.ticker)
        except Exception as exc:
            logger.error(
                "Company setup SEC CIK lookup failed",
                extra={"provider": "SEC EDGAR", "exception_type": type(exc).__name__},
            )
            warnings.append("SEC CIK lookup is temporarily unavailable.")
        else:
            if cik:
                company.cik = cik
                company.regulatory_id = company.regulatory_id or cik
                company.regulatory_id_type = company.regulatory_id_type or "CIK"
                db.commit()
                db.refresh(company)

    missing = _missing_identifiers(company)
    return CompanySetupIdentityResolution(
        company_id=company.id,
        market=company.market or "US",
        ticker=company.ticker,
        local_symbol=company.local_symbol,
        primary_exchange=company.primary_exchange,
        regulatory_id=company.regulatory_id,
        regulatory_id_type=company.regulatory_id_type,
        cik=company.cik,
        confidence_label="high" if not missing else "medium" if company.market == "IN" else "low",
        missing_identifiers=missing,
        warnings=warnings,
    )


def workflow_response(workflow: CompanySetupWorkflow, company: Company) -> CompanySetupWorkflowRead:
    return CompanySetupWorkflowRead(
        id=workflow.id,
        company_id=workflow.company_id,
        current_step=workflow.current_step,
        identity_status=workflow.identity_status,
        source_status=workflow.source_status,
        filing_status=workflow.filing_status,
        financial_extraction_status=workflow.financial_extraction_status,
        industry_mapping_status=workflow.industry_mapping_status,
        valuation_readiness_status=workflow.valuation_readiness_status,
        security_review_status=workflow.security_review_status,
        source_readiness=source_readiness(company),
        next_recommended_step=_next_recommended_step(workflow),
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


def source_readiness(company: Company) -> list[CompanySetupSourceReadiness]:
    market = (company.market or "US").upper()
    if market == "IN":
        return [
            CompanySetupSourceReadiness(
                provider_name="India Manual Filings",
                capability="filings",
                market="IN",
                status="manual_only",
                notes="Automated India filing discovery is not configured.",
                action_required="Use manual annual report, quarterly results, or exchange announcement upload/link.",
            ),
            CompanySetupSourceReadiness(
                provider_name="Manual Fundamentals",
                capability="financial_statements",
                market="IN",
                status="manual_only",
                notes="India fundamentals require manual entry or reviewed imports.",
                action_required="Enter or import reviewed financial statement metrics before valuation autofill.",
            ),
        ]

    sec_configured = _valid_sec_user_agent(os.getenv("SEC_USER_AGENT"))
    return [
        CompanySetupSourceReadiness(
            provider_name="SEC EDGAR",
            capability="filings",
            market="US",
            status="configured" if sec_configured else "missing_key",
            notes="SEC EDGAR can discover and ingest US filings when SEC_USER_AGENT is configured.",
            action_required=None if sec_configured else "Set SEC_USER_AGENT with a real contact email.",
        ),
        CompanySetupSourceReadiness(
            provider_name="SEC Company Facts",
            capability="financial_statements",
            market="US",
            status="configured" if sec_configured else "missing_key",
            notes="SEC company facts can seed financial periods, but reviewed metrics are still required.",
            action_required=None if sec_configured else "Set SEC_USER_AGENT before SEC fundamentals ingestion.",
        ),
    ]


def _get_company(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _initial_step(company: Company) -> str:
    return "source_setup" if _initial_identity_status(company) == "reviewed" else "identity"


def _initial_identity_status(company: Company) -> str:
    market = (company.market or "US").upper()
    if market == "US":
        return "reviewed" if company.cik or company.regulatory_id else "needs_review"
    return "needs_review"


def _source_status(company: Company) -> str:
    market = (company.market or "US").upper()
    if market == "IN":
        return "manual_only"
    return "configured" if _valid_sec_user_agent(os.getenv("SEC_USER_AGENT")) else "missing"


def _valid_sec_user_agent(value: str | None) -> bool:
    return bool(value and "@" in value and value != DEFAULT_SEC_USER_AGENT)


def _missing_identifiers(company: Company) -> list[str]:
    market = (company.market or "US").upper()
    missing: list[str] = []
    if not company.local_symbol:
        missing.append("local_symbol")
    if not company.primary_exchange:
        missing.append("primary_exchange")
    if market == "US" and not company.cik:
        missing.append("cik")
    if market == "IN" and not company.isin:
        missing.append("isin")
    return missing


def _next_recommended_step(workflow: CompanySetupWorkflow) -> str:
    if workflow.identity_status != "reviewed":
        return "Confirm company identity."
    if workflow.source_status in {"missing", "missing_key"}:
        return "Configure required source credentials."
    if workflow.filing_status == "missing":
        return "Fetch US filings or add manual India filings."
    if workflow.financial_extraction_status in {"missing", "needs_review"}:
        return "Extract and review financial statement metrics."
    if workflow.industry_mapping_status != "reviewed":
        return "Confirm industry mapping before benchmark-derived assumptions."
    if workflow.valuation_readiness_status != "ready":
        return "Review assumptions before running valuation."
    return "Run valuation and review memo."
