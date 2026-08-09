from app.api.response_contracts import (
    BINARY_ROUTE_ALLOWLIST,
    build_response_contract_inventory,
)
from app.main import app


def test_every_route_has_an_explicit_response_contract() -> None:
    inventory = build_response_contract_inventory(app)

    assert inventory
    assert not [record for record in inventory if record.contract == "legacy_json"]
    assert {
        (record.method, record.path)
        for record in inventory
        if record.contract == "binary"
    } == BINARY_ROUTE_ALLOWLIST


def test_no_content_routes_do_not_declare_response_models() -> None:
    inventory = build_response_contract_inventory(app)

    assert [record for record in inventory if record.contract == "no_content"]
