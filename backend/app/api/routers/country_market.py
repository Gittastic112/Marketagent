from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    ApiErrorDetail,
    ApiMeta,
    ApiResponse,
    CountryMarketContextManualCreate,
    CountryMarketContextRead,
    RiskFreeRateRead,
)
from app.api.errors import PublicApiError
from app.db.session import get_db
from app.services.country_market_context import (
    get_market_context,
    get_risk_free_rate_for_currency,
    market_context_warnings,
    normalize_currency,
    save_manual_market_context,
)


router = APIRouter(prefix="", tags=["country-market"])


@router.get("/api/market-context", response_model=ApiResponse[CountryMarketContextRead])
def read_market_context(market: str, db: Session = Depends(get_db)) -> ApiResponse[CountryMarketContextRead]:
    try:
        context = get_market_context(db=db, market=market)
    except ValueError as exc:
        raise PublicApiError(
            status_code=400,
            code="MARKET_CONTEXT_INVALID",
            message="Unsupported market. Use US or IN.",
            field="market",
        ) from exc

    if context is None:
        return _not_configured_market_context(market)

    return ApiResponse(
        data=CountryMarketContextRead.model_validate(context),
        meta=ApiMeta(
            source="manual" if context.is_manual else "provider",
            last_updated=context.updated_at,
            warnings=market_context_warnings(context),
        ),
    )


@router.post(
    "/api/market-context/manual",
    response_model=ApiResponse[CountryMarketContextRead],
    status_code=status.HTTP_201_CREATED,
)
def create_manual_market_context(
    payload: CountryMarketContextManualCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[CountryMarketContextRead]:
    try:
        context = save_manual_market_context(db=db, payload=payload)
    except ValueError as exc:
        raise PublicApiError(
            status_code=422,
            code="MARKET_CONTEXT_INVALID",
            message="Market context values are invalid.",
        ) from exc

    return ApiResponse(
        data=CountryMarketContextRead.model_validate(context),
        meta=ApiMeta(
            source="manual",
            last_updated=context.updated_at,
            warnings=market_context_warnings(context),
        ),
    )


@router.get("/api/valuation/risk-free-rate", response_model=ApiResponse[RiskFreeRateRead])
def read_risk_free_rate(currency: str, db: Session = Depends(get_db)) -> ApiResponse[RiskFreeRateRead]:
    try:
        normalized_currency = normalize_currency(currency)
        context = get_risk_free_rate_for_currency(db=db, currency=normalized_currency)
    except ValueError as exc:
        raise PublicApiError(
            status_code=400,
            code="CURRENCY_INVALID",
            message="Currency is invalid or unsupported.",
            field="currency",
        ) from exc

    if context is None:
        return ApiResponse(
            data=None,
            meta=ApiMeta(
                status="error",
                source="manual",
                is_stale=True,
                warnings=[
                    f"Risk-free rate for {normalized_currency} is not configured. Add manual market context first."
                ],
                confidence="low",
            ),
            errors=[
                ApiErrorDetail(
                    code="RISK_FREE_RATE_NOT_CONFIGURED",
                    message=f"Risk-free rate for {normalized_currency} is not configured.",
                    target="currency",
                )
            ],
        )

    return ApiResponse(
        data=RiskFreeRateRead(
            market=context.market,
            country=context.country,
            currency=context.currency,
            risk_free_rate=context.risk_free_rate or 0.0,
            risk_free_rate_source=context.risk_free_rate_source or "manual",
            as_of_date=context.as_of_date,
            is_manual=context.is_manual,
            warnings=market_context_warnings(context),
        ),
        meta=ApiMeta(
            source="manual" if context.is_manual else "provider",
            last_updated=context.updated_at,
            warnings=market_context_warnings(context),
        ),
    )


def _not_configured_market_context(market: str) -> ApiResponse[CountryMarketContextRead]:
    normalized_market = market.strip().upper()
    return ApiResponse(
        data=None,
        meta=ApiMeta(
            status="error",
            source="manual",
            is_stale=True,
            warnings=[
                f"Market context for {normalized_market} is not configured. Add manual context before using rates."
            ],
            confidence="low",
        ),
        errors=[
            ApiErrorDetail(
                code="MARKET_CONTEXT_NOT_CONFIGURED",
                message=f"Market context for {normalized_market} is not configured. Add a manual market context row.",
                target="market",
            )
        ],
    )
