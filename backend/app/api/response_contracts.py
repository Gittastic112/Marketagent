from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.routing import APIRoute


BINARY_ROUTE_ALLOWLIST = frozenset(
    {
        ("GET", "/api/raw-documents/{raw_document_id}/asset/content"),
        ("GET", "/api/raw-documents/{raw_document_id}/asset/pages/{page_number}.png"),
        ("GET", "/companies/{company_id}/memo"),
        ("GET", "/export/events"),
        ("GET", "/export/market-prices"),
        ("GET", "/export/portfolio-holdings"),
        ("GET", "/export/portfolio-transactions"),
        ("GET", "/export/raw-documents"),
    }
)


@dataclass(frozen=True)
class RouteResponseContract:
    method: str
    path: str
    contract: str


def _is_api_response_model(response_model: object) -> bool:
    return getattr(response_model, "__name__", "").startswith("ApiResponse")


def build_response_contract_inventory(app: FastAPI) -> list[RouteResponseContract]:
    records: list[RouteResponseContract] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(route.methods or []):
            key = (method, route.path)
            if route.status_code == 204:
                contract = "no_content"
            elif key in BINARY_ROUTE_ALLOWLIST:
                contract = "binary"
            elif _is_api_response_model(route.response_model):
                contract = "api_envelope"
            else:
                contract = "legacy_json"
            records.append(
                RouteResponseContract(
                    method=method,
                    path=route.path,
                    contract=contract,
                )
            )
    return sorted(records, key=lambda item: (item.path, item.method))
