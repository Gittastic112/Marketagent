from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta

from app.api.deps import get_db
from app.models.company import Company
from app.models.market_price import CompanyMarketData, MarketPrice
from app.models.processing_run import ProcessingRun
from app.api.schemas import ApiResponse, ApiErrorDetail, CompanyMarketDataRead, MarketPriceRead
from app.services.market_data.factory import get_market_data_provider

router = APIRouter(prefix="/api/market", tags=["market"])

@router.get("/quote/{ticker}", response_model=ApiResponse[CompanyMarketDataRead])
def get_market_quote(ticker: str, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.ticker == ticker)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    market_data = company.market_data
    if not market_data:
        return ApiResponse(data=None)

    return ApiResponse(data=CompanyMarketDataRead.model_validate(market_data))

@router.get("/history/{ticker}", response_model=ApiResponse[list[MarketPriceRead]])
def get_market_history(ticker: str, range: str = "1y", db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.ticker == ticker)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    query = select(MarketPrice).where(MarketPrice.company_id == company.id)
    
    # Calculate start date based on range (default 1y)
    start_date = datetime.now(timezone.utc).date() - relativedelta(years=1)
    if range == "6m":
        start_date = datetime.now(timezone.utc).date() - relativedelta(months=6)
    elif range == "3m":
        start_date = datetime.now(timezone.utc).date() - relativedelta(months=3)
        
    query = query.where(MarketPrice.as_of_date >= start_date).order_by(MarketPrice.as_of_date.asc())
    
    prices = db.execute(query).scalars().all()
    
    # Format to match MarketPriceRead alias date
    # Alias mapping happens in Pydantic automatically with alias_generator or explicit Field alias
    return ApiResponse(data=[MarketPriceRead.model_validate(p) for p in prices])

@router.post("/ingest/{ticker}", response_model=ApiResponse[dict])
async def ingest_market_data(ticker: str, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.ticker == ticker)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    provider = get_market_data_provider()
    
    run = ProcessingRun(
        run_type="market_data_ingestion",
        company_id=company.id,
        started_at=datetime.now(timezone.utc),
        status="running"
    )
    db.add(run)
    db.commit()

    try:
        quote = await provider.get_quote(ticker)
        history = await provider.get_historical_prices(ticker, days=365)
        
        # Update quote
        if quote:
            market_data = company.market_data
            if not market_data:
                market_data = CompanyMarketData(company_id=company.id)
                db.add(market_data)
                
            market_data.current_price = quote.get("current_price")
            market_data.change_percent = quote.get("change_percent")
            market_data.volume = quote.get("volume")
            market_data.last_updated = datetime.now(timezone.utc)
            run.created_count += 1
            
        # Update history
        for price_record in history:
            date_str = price_record["date"]
            price_val = price_record["close_price"]
            
            try:
                as_of_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
                
            existing_price = db.execute(
                select(MarketPrice).where(
                    MarketPrice.company_id == company.id,
                    MarketPrice.as_of_date == as_of_date
                )
            ).scalar_one_or_none()
            
            if not existing_price:
                db.add(MarketPrice(
                    company_id=company.id,
                    ticker=ticker,
                    price=price_val,
                    as_of_date=as_of_date
                ))
                run.created_count += 1
            else:
                run.skipped_duplicate_count += 1

        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        return ApiResponse(data={"status": "success", "fetched_count": len(history) + (1 if quote else 0)})
    except Exception as e:
        run.status = "failed"
        run.error_count += 1
        run.error_details_json = {"error": str(e)}
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        return ApiResponse(data=None, errors=[ApiErrorDetail(code="ingest_failed", message=str(e))])
