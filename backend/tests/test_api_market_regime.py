from datetime import date

from fastapi.testclient import TestClient

from helpers import response_data


def test_current_market_regime_is_enveloped_and_idempotent(client: TestClient) -> None:
    first_response = client.get("/market-regime/current")
    second_response = client.get("/market-regime/current")

    assert first_response.status_code == 200
    assert first_response.json()["meta"]["source"] == "manual"
    first = response_data(first_response)
    second = response_data(second_response)
    assert first["id"] == second["id"]
    assert first["mode"] == "Incomplete"
    assert first["overall_score"] == 0
    assert first["warnings"]


def test_manual_inputs_recalculate_current_market_regime(client: TestClient) -> None:
    values = {
        "options": 70,
        "liquidity": 60,
        "volume": 50,
        "breadth": 40,
        "macro": 30,
    }
    for metric_name, value in values.items():
        response = client.post(
            "/market-regime/inputs",
            json={
                "metric_name": metric_name,
                "value": value,
                "as_of_date": date.today().isoformat(),
                "source_url": None,
                "source_name": "User research worksheet",
                "input_type": "manual",
                "methodology": "Normalized by the user to the documented -100 to 100 regime scale.",
            },
        )
        assert response.status_code == 200
        assert response.json()["meta"]["source"] == "manual"

    current = response_data(client.get("/market-regime/current"))
    assert current["mode"] == "Live"
    assert current["confidence"] == "high"
    assert current["overall_score"] == 54.0
    assert current["live_modules"] == ["Options", "Liquidity", "Volume", "Breadth", "Macro"]


def test_market_regime_input_rejects_unbounded_or_untraceable_values(client: TestClient) -> None:
    invalid_value = client.post(
        "/market-regime/inputs",
        json={
            "metric_name": "options",
            "value": 101,
            "as_of_date": date.today().isoformat(),
            "source_name": "User worksheet",
            "input_type": "manual",
            "methodology": "Normalized to the regime scale from the cited option indicators.",
        },
    )
    assert invalid_value.status_code == 422

    provider_without_source = client.post(
        "/market-regime/inputs",
        json={
            "metric_name": "macro",
            "value": 10,
            "as_of_date": date.today().isoformat(),
            "source_name": "External macro provider",
            "input_type": "provider",
            "methodology": "Provider value normalized to the regime scale.",
        },
    )
    assert provider_without_source.status_code == 422
