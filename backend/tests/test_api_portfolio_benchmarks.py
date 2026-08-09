from datetime import date


def _data(response):
    assert response.status_code < 400, response.text
    return response.json()["data"]


def test_portfolio_benchmark_crud_is_owned_and_normalized(client):
    portfolio = _data(client.post("/portfolios", json={"name": "Benchmark Test", "base_currency": "USD"}))
    created = _data(
        client.post(
            "/portfolio-benchmarks",
            json={
                "portfolio_id": portfolio["id"],
                "ticker": "spy",
                "currency": "usd",
                "provider_name": "manual",
                "effective_from": str(date(2026, 1, 1)),
            },
        )
    )

    assert created["ticker"] == "SPY"
    assert created["currency"] == "USD"
    assert _data(client.get(f"/portfolio-benchmarks?portfolio_id={portfolio['id']}"))[0]["id"] == created["id"]

    updated = _data(
        client.patch(
            f"/portfolio-benchmarks/{created['id']}",
            json={"ticker": "qqq", "notes": "Growth comparison"},
        )
    )
    assert updated["ticker"] == "QQQ"
    assert updated["notes"] == "Growth comparison"

    assert client.delete(f"/portfolio-benchmarks/{created['id']}").status_code == 204
    assert client.get(f"/portfolio-benchmarks/{created['id']}").status_code == 404


def test_portfolio_allows_only_one_benchmark_config(client):
    portfolio = _data(client.post("/portfolios", json={"name": "One Benchmark", "base_currency": "USD"}))
    payload = {
        "portfolio_id": portfolio["id"],
        "ticker": "SPY",
        "currency": "USD",
        "effective_from": "2026-01-01",
    }
    assert client.post("/portfolio-benchmarks", json=payload).status_code == 201
    duplicate = client.post("/portfolio-benchmarks", json={**payload, "ticker": "QQQ"})
    assert duplicate.status_code == 409
