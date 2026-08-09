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
            },
        )
        assert response.status_code == 200
        assert response.json()["meta"]["source"] == "manual"

    current = response_data(client.get("/market-regime/current"))
    assert current["mode"] == "Live"
    assert current["confidence"] == "high"
    assert current["overall_score"] == 54.0
    assert current["live_modules"] == ["Options", "Liquidity", "Volume", "Breadth", "Macro"]
