import csv
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.schemas import ApiResponse

from app.db.session import get_db
from app.models.portfolio import PortfolioHolding, PortfolioTransaction
from app.models.market_price import MarketPrice
from datetime import datetime, date

router = APIRouter()

from app.core.security import escape_csv_formula

@router.get("/export/portfolio-holdings")
def export_portfolio_holdings(db: Session = Depends(get_db)):
    holdings = db.scalars(select(PortfolioHolding)).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["portfolio_id", "company_id", "ticker", "quantity", "average_cost", "currency", "as_of_date"])
    
    for holding in holdings:
        writer.writerow([
            holding.portfolio_id,
            holding.company_id or "",
            escape_csv_formula(holding.ticker),
            holding.quantity,
            holding.average_cost,
            escape_csv_formula(holding.currency),
            holding.as_of_date.isoformat()
        ])
        
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=portfolio_holdings.csv"
    return ApiResponse(data=response)

@router.get("/export/portfolio-transactions")
def export_portfolio_transactions(db: Session = Depends(get_db)):
    transactions = db.scalars(select(PortfolioTransaction)).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["portfolio_id", "company_id", "ticker", "transaction_type", "quantity", "price", "fees", "currency", "transaction_date", "notes"])
    
    for tx in transactions:
        writer.writerow([
            tx.portfolio_id,
            tx.company_id or "",
            escape_csv_formula(tx.ticker),
            escape_csv_formula(tx.transaction_type),
            tx.quantity,
            tx.price,
            tx.fees,
            escape_csv_formula(tx.currency),
            tx.transaction_date.isoformat(),
            escape_csv_formula(tx.notes) if tx.notes else ""
        ])
        
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=portfolio_transactions.csv"
    return ApiResponse(data=response)

@router.get("/export/market-prices")
def export_market_prices(db: Session = Depends(get_db)):
    prices = db.scalars(select(MarketPrice)).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["company_id", "ticker", "price", "currency", "as_of_date", "source_name"])
    
    for p in prices:
        writer.writerow([
            p.company_id or "",
            escape_csv_formula(p.ticker),
            p.price,
            escape_csv_formula(p.currency),
            p.as_of_date.isoformat(),
            escape_csv_formula(p.source_name) if p.source_name else ""
        ])
        
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=market_prices.csv"
    return ApiResponse(data=response)

from app.models.raw_document import RawDocument
from app.models.event import Event

@router.get("/export/raw-documents")
def export_raw_documents(db: Session = Depends(get_db)):
    docs = db.scalars(select(RawDocument)).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "company_id", "source_name", "source_type", "url", "published_at", "ingested_at", "content_hash"])
    
    for d in docs:
        writer.writerow([
            d.id,
            d.company_id or "",
            escape_csv_formula(d.source_name),
            escape_csv_formula(d.source_type),
            escape_csv_formula(d.url) if d.url else "",
            d.published_at.isoformat() if d.published_at else "",
            d.ingested_at.isoformat() if d.ingested_at else "",
            escape_csv_formula(d.content_hash)
        ])
        
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=raw_documents.csv"
    return ApiResponse(data=response)

@router.get("/export/events")
def export_events(db: Session = Depends(get_db)):
    events = db.scalars(select(Event)).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "company_id", "raw_document_id", "headline", "summary", "event_date", "classification", "credibility_score", "importance_score"])
    
    for e in events:
        writer.writerow([
            e.id,
            e.company_id or "",
            e.raw_document_id or "",
            escape_csv_formula(e.headline),
            escape_csv_formula(e.summary) if e.summary else "",
            e.event_date.isoformat() if e.event_date else "",
            escape_csv_formula(e.classification) if e.classification else "",
            e.credibility_score,
            e.importance_score
        ])
        
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=events.csv"
    return ApiResponse(data=response)

@router.post("/import/market-prices")
def import_market_prices(preview: bool = False, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Must be a CSV file")
    
    content = file.file.read().decode('utf-8')
    reader = csv.DictReader(StringIO(content))
    
    valid_rows = []
    error_rows = []
    records_to_add = []
    
    for row_idx, row in enumerate(reader, start=2):
        errors = []
        ticker = row.get("ticker", "").strip("'")
        price_str = row.get("price", "0")
        currency = row.get("currency", "USD").strip("'")
        as_of_date_str = row.get("as_of_date", "")
        source_name = row.get("source_name", "").strip("'")

        price = 0.0
        try:
            price = float(price_str)
        except ValueError:
            errors.append({"row_index": row_idx, "field": "price", "message": "Invalid price format"})
            
        as_of_date = None
        try:
            if as_of_date_str:
                as_of_date = date.fromisoformat(as_of_date_str)
            else:
                errors.append({"row_index": row_idx, "field": "as_of_date", "message": "Required field missing"})
        except ValueError:
            errors.append({"row_index": row_idx, "field": "as_of_date", "message": "Invalid date format, expected YYYY-MM-DD"})

        if not ticker:
            errors.append({"row_index": row_idx, "field": "ticker", "message": "Required field missing"})

        if not errors:
            duplicate = db.scalars(select(MarketPrice).where(
                MarketPrice.ticker == ticker,
                MarketPrice.as_of_date == as_of_date,
                MarketPrice.source_name == source_name
            )).first()
            if duplicate:
                errors.append({"row_index": row_idx, "field": "duplicate", "message": "Record already exists in database"})

        if not errors:
            valid_rows.append({"row_index": row_idx, "data": row, "is_valid": True, "errors": []})
            records_to_add.append(
                MarketPrice(
                    ticker=ticker,
                    price=price,
                    currency=currency,
                    as_of_date=as_of_date,
                    source_name=source_name
                )
            )
        else:
            error_rows.append({"row_index": row_idx, "data": row, "is_valid": False, "errors": errors})

    if preview:
        return ApiResponse(data={
            "is_preview": True,
            "total_rows": len(valid_rows) + len(error_rows),
            "valid_count": len(valid_rows),
            "error_count": len(error_rows),
            "rows": valid_rows + error_rows
        })

    if error_rows:
        raise HTTPException(status_code=400, detail={"message": "CSV contains errors", "errors": error_rows})

    try:
        db.add_all(records_to_add)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error during import: {str(e)}")

    return ApiResponse(data={"status": "ok", "imported_count": len(records_to_add)})

@router.post("/import/portfolio-transactions")
def import_portfolio_transactions(preview: bool = False, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Must be a CSV file")
        
    content = file.file.read().decode('utf-8')
    reader = csv.DictReader(StringIO(content))
    
    valid_rows = []
    error_rows = []
    records_to_add = []
    
    for row_idx, row in enumerate(reader, start=2):
        errors = []
        portfolio_id_str = row.get("portfolio_id", "0")
        ticker = row.get("ticker", "").strip("'")
        tx_type = row.get("transaction_type", "").strip("'")
        qty_str = row.get("quantity", "0")
        price_str = row.get("price", "0")
        currency = row.get("currency", "USD").strip("'")
        tx_date_str = row.get("transaction_date", "")
        notes = row.get("notes", "").strip("'")

        portfolio_id = 0
        try:
            portfolio_id = int(portfolio_id_str)
        except ValueError:
            errors.append({"row_index": row_idx, "field": "portfolio_id", "message": "Invalid integer"})
            
        qty = 0.0
        try:
            qty = float(qty_str)
        except ValueError:
            errors.append({"row_index": row_idx, "field": "quantity", "message": "Invalid number format"})
            
        price = 0.0
        try:
            price = float(price_str)
        except ValueError:
            errors.append({"row_index": row_idx, "field": "price", "message": "Invalid number format"})
            
        tx_date = None
        try:
            if tx_date_str:
                tx_date = date.fromisoformat(tx_date_str)
            else:
                errors.append({"row_index": row_idx, "field": "transaction_date", "message": "Required field missing"})
        except ValueError:
            errors.append({"row_index": row_idx, "field": "transaction_date", "message": "Invalid date format, expected YYYY-MM-DD"})

        if not ticker:
            errors.append({"row_index": row_idx, "field": "ticker", "message": "Required field missing"})
            
        if not tx_type:
            errors.append({"row_index": row_idx, "field": "transaction_type", "message": "Required field missing"})

        if not errors:
            duplicate = db.scalars(select(PortfolioTransaction).where(
                PortfolioTransaction.portfolio_id == portfolio_id,
                PortfolioTransaction.ticker == ticker,
                PortfolioTransaction.transaction_type == tx_type,
                PortfolioTransaction.transaction_date == tx_date,
                PortfolioTransaction.quantity == qty,
                PortfolioTransaction.price == price
            )).first()
            if duplicate:
                errors.append({"row_index": row_idx, "field": "duplicate", "message": "Record already exists in database"})

        if not errors:
            valid_rows.append({"row_index": row_idx, "data": row, "is_valid": True, "errors": []})
            records_to_add.append(
                PortfolioTransaction(
                    portfolio_id=portfolio_id,
                    ticker=ticker,
                    transaction_type=tx_type,
                    quantity=qty,
                    price=price,
                    currency=currency,
                    transaction_date=tx_date,
                    notes=notes
                )
            )
        else:
            error_rows.append({"row_index": row_idx, "data": row, "is_valid": False, "errors": errors})

    if preview:
        return ApiResponse(data={
            "is_preview": True,
            "total_rows": len(valid_rows) + len(error_rows),
            "valid_count": len(valid_rows),
            "error_count": len(error_rows),
            "rows": valid_rows + error_rows
        })

    if error_rows:
        raise HTTPException(status_code=400, detail={"message": "CSV contains errors", "errors": error_rows})

    try:
        from app.services.portfolio_holdings import apply_transaction_to_holding, apply_transaction_to_cash
        for tx in records_to_add:
            db.add(tx)
            db.flush() # get ID
            apply_transaction_to_holding(db, tx)
            apply_transaction_to_cash(db, tx)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error during import: {str(e)}")

    return ApiResponse(data={"status": "ok", "imported_count": len(records_to_add)})

@router.post("/import/portfolio-holdings")
def import_portfolio_holdings(preview: bool = False, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Must be a CSV file")
        
    content = file.file.read().decode('utf-8')
    reader = csv.DictReader(StringIO(content))
    
    valid_rows = []
    error_rows = []
    records_to_add = []
    
    for row_idx, row in enumerate(reader, start=2):
        errors = []
        portfolio_id_str = row.get("portfolio_id", "0")
        ticker = row.get("ticker", "").strip("'")
        qty_str = row.get("quantity", "0")
        cost_str = row.get("average_cost", "0")
        currency = row.get("currency", "USD").strip("'")
        as_of_date_str = row.get("as_of_date", "")

        portfolio_id = 0
        try:
            portfolio_id = int(portfolio_id_str)
        except ValueError:
            errors.append({"row_index": row_idx, "field": "portfolio_id", "message": "Invalid integer"})

        qty = 0.0
        try:
            qty = float(qty_str)
        except ValueError:
            errors.append({"row_index": row_idx, "field": "quantity", "message": "Invalid number format"})
            
        cost = 0.0
        try:
            cost = float(cost_str)
        except ValueError:
            errors.append({"row_index": row_idx, "field": "average_cost", "message": "Invalid number format"})
            
        as_of_date = None
        try:
            if as_of_date_str:
                as_of_date = date.fromisoformat(as_of_date_str)
            else:
                errors.append({"row_index": row_idx, "field": "as_of_date", "message": "Required field missing"})
        except ValueError:
            errors.append({"row_index": row_idx, "field": "as_of_date", "message": "Invalid date format, expected YYYY-MM-DD"})

        if not ticker:
            errors.append({"row_index": row_idx, "field": "ticker", "message": "Required field missing"})

        if not errors:
            duplicate = db.scalars(select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.ticker == ticker,
                PortfolioHolding.as_of_date == as_of_date
            )).first()
            if duplicate:
                errors.append({"row_index": row_idx, "field": "duplicate", "message": "Record already exists in database"})

        if not errors:
            valid_rows.append({"row_index": row_idx, "data": row, "is_valid": True, "errors": []})
            records_to_add.append(
                PortfolioHolding(
                    portfolio_id=portfolio_id,
                    ticker=ticker,
                    quantity=qty,
                    average_cost=cost,
                    currency=currency,
                    as_of_date=as_of_date
                )
            )
        else:
            error_rows.append({"row_index": row_idx, "data": row, "is_valid": False, "errors": errors})

    if preview:
        return ApiResponse(data={
            "is_preview": True,
            "total_rows": len(valid_rows) + len(error_rows),
            "valid_count": len(valid_rows),
            "error_count": len(error_rows),
            "rows": valid_rows + error_rows
        })

    if error_rows:
        raise HTTPException(status_code=400, detail={"message": "CSV contains errors", "errors": error_rows})

    try:
        db.add_all(records_to_add)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error during import: {str(e)}")

    return ApiResponse(data={"status": "ok", "imported_count": len(records_to_add)})
