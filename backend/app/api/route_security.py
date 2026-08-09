from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from app.api.dependencies import get_current_user


PUBLIC_ROUTE_ALLOWLIST = frozenset(
    {
        ("GET", "/api/health"),
        ("GET", "/health"),
    }
)


@dataclass(frozen=True)
class RouteSecurityRecord:
    method: str
    path: str
    name: str
    classification: str
    has_auth_dependency: bool


def _has_dependency(dependant: Dependant, dependency: object) -> bool:
    if dependant.call is dependency:
        return True
    return any(
        _has_dependency(child, dependency)
        for child in dependant.dependencies
    )


def build_route_security_inventory(app: FastAPI) -> list[RouteSecurityRecord]:
    records: list[RouteSecurityRecord] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(route.methods or []):
            key = (method, route.path)
            is_public = key in PUBLIC_ROUTE_ALLOWLIST
            records.append(
                RouteSecurityRecord(
                    method=method,
                    path=route.path,
                    name=route.name,
                    classification="public" if is_public else "authenticated",
                    has_auth_dependency=_has_dependency(
                        route.dependant,
                        get_current_user,
                    ),
                )
            )
    return sorted(records, key=lambda item: (item.path, item.method))
