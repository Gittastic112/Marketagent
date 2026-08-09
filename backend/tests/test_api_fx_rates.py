def _data(response):
    assert response.status_code < 400, response.text
    return response.json()["data"]


def test_fx_observation_crud_preserves_provenance(client):
    response = client.post(
        "/fx-rates",
        json={
            "base_currency": "inr",
            "quote_currency": "usd",
            "rate": 0.0119,
            "as_of_date": "2026-08-01",
            "provider_name": "manual",
            "source_url": "https://example.test/fx/2026-08-01",
        },
    )
    created = _data(response)
    assert created["base_currency"] == "INR"
    assert created["quote_currency"] == "USD"
    assert response.json()["meta"]["source"] == "manual"
    assert response.json()["meta"]["warnings"]

    rows = _data(client.get("/fx-rates?base_currency=INR&quote_currency=USD"))
    assert [row["id"] for row in rows] == [created["id"]]
    assert _data(client.get(f"/fx-rates/{created['id']}"))["rate"] == 0.0119

    assert client.delete(f"/fx-rates/{created['id']}").status_code == 204
    assert client.get(f"/fx-rates/{created['id']}").status_code == 404


def test_fx_observation_rejects_duplicate_source_date(client):
    payload = {
        "base_currency": "EUR",
        "quote_currency": "USD",
        "rate": 1.17,
        "as_of_date": "2026-08-01",
        "provider_name": "manual",
    }
    assert client.post("/fx-rates", json=payload).status_code == 201
    assert client.post("/fx-rates", json=payload).status_code == 409
