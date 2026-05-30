from typing import Sequence
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import schemas
from app.db.session import get_db
from app.models.financial import FinancialStatementPeriod, FinancialMetric
from app.models.company import Company
from app.models.processing_run import ProcessingRun
from app.api.schemas import ApiResponse, ApiErrorDetail, FinancialPeriodRead
from app.services.fundamentals import fetch_sec_company_facts, process_sec_facts

router = APIRouter(tags=["fundamentals"])


@router.post("/companies/{company_id}/financial-periods", response_model=ApiResponse[schemas.FinancialStatementPeriodRead], status_code=status.HTTP_201_CREATED)
def create_financial_period(company_id: int, period_in: schemas.FinancialStatementPeriodCreate, db: Session = Depends(get_db)) -> FinancialStatementPeriod:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    period = FinancialStatementPeriod(**period_in.model_dump())
    period.company_id = company_id
    db.add(period)
    db.commit()
    db.refresh(period)
    return ApiResponse(data=period)


@router.get("/companies/{company_id}/financial-periods", response_model=ApiResponse[list[schemas.FinancialStatementPeriodRead]])
def list_financial_periods(company_id: int, db: Session = Depends(get_db)) -> Sequence[FinancialStatementPeriod]:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    periods = db.scalars(
        select(FinancialStatementPeriod)
        .where(FinancialStatementPeriod.company_id == company_id)
        .order_by(FinancialStatementPeriod.year.desc(), FinancialStatementPeriod.quarter.desc())
    ).all()
    return ApiResponse(data=periods)


@router.post("/financial-periods/{period_id}/metrics", response_model=ApiResponse[schemas.FinancialMetricRead], status_code=status.HTTP_201_CREATED)
def create_financial_metric(period_id: int, metric_in: schemas.FinancialMetricCreate, db: Session = Depends(get_db)) -> FinancialMetric:
    period = db.get(FinancialStatementPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    metric = FinancialMetric(**metric_in.model_dump())
    metric.period_id = period_id
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return ApiResponse(data=metric)


@router.delete("/financial-periods/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial_period(period_id: int, db: Session = Depends(get_db)) -> None:
    period = db.get(FinancialStatementPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    
    db.delete(period)
    db.commit()


@router.get("/{ticker}/trends", response_model=ApiResponse[list[FinancialPeriodRead]])
def get_financial_trends(ticker: str, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.ticker == ticker)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    periods = db.execute(
        select(FinancialStatementPeriod)
        .where(FinancialStatementPeriod.company_id == company.id)
        .order_by(FinancialStatementPeriod.year.desc(), FinancialStatementPeriod.quarter.desc())
    ).scalars().all()
    
    return ApiResponse(data=[FinancialPeriodRead.model_validate(p) for p in periods])


@router.post("/ingest/{ticker}", response_model=ApiResponse[dict])
async def ingest_fundamentals(ticker: str, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.ticker == ticker)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not company.cik:
        return ApiResponse(data=None, errors=[ApiErrorDetail(code="missing_cik", message="Company does not have a CIK configured.")])

    run = ProcessingRun(
        run_type="fundamentals_ingestion",
        company_id=company.id,
        started_at=datetime.now(timezone.utc),
        status="running"
    )
    db.add(run)
    db.commit()

    try:
        facts_data = await fetch_sec_company_facts(company.cik)
        if facts_data:
            periods_created, metrics_created = process_sec_facts(db, company.id, facts_data)
            run.created_count = periods_created + metrics_created
        
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        return ApiResponse(data={"status": "success", "periods_updated": run.created_count})
    except Exception as e:
        run.status = "failed"
        run.error_count += 1
        run.error_details_json = {"error": str(e)}
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        return ApiResponse(data=None, errors=[ApiErrorDetail(code="ingest_failed", message=str(e))])
