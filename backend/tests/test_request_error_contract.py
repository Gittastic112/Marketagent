from uuid import UUID, uuid4


def test_provider_failure_uses_safe_code_without_exception_text(client, monkeypatch) -> None:
    def fail_lookup(**_kwargs):
        raise RuntimeError("upstream token=secret-provider-detail")

    monkeypatch.setattr("app.api.routers.companies.lookup_company", fail_lookup)

    response = client.get("/companies/lookup?ticker=AAPL")

    assert response.status_code == 502
    payload = response.json()
    assert payload["errors"][0]["code"] == "COMPANY_LOOKUP_FAILED"
    assert payload["errors"][0]["provider"] == "company_lookup"
    assert payload["errors"][0]["retryable"] is True
    assert "secret-provider-detail" not in response.text
    assert payload["meta"]["request_id"] == response.headers["X-Request-ID"]


def test_http_error_uses_public_envelope_and_request_id(client) -> None:
    supplied_request_id = str(uuid4())

    response = client.get(
        "/companies/999999",
        headers={"X-Request-ID": supplied_request_id},
    )

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == supplied_request_id
    payload = response.json()
    assert payload["data"] is None
    assert payload["meta"]["status"] == "error"
    assert payload["meta"]["request_id"] == supplied_request_id
    assert payload["errors"] == [
        {
            "code": "NOT_FOUND",
            "message": "Record not found",
            "target": None,
            "retryable": False,
            "field": None,
            "provider": None,
            "processing_run_id": None,
        }
    ]
    assert payload["detail"] == "Record not found"


def test_invalid_request_id_is_replaced_and_validation_is_structured(client) -> None:
    response = client.post(
        "/companies",
        json={},
        headers={"X-Request-ID": "not-a-valid-request-id\nforged"},
    )

    assert response.status_code == 422
    request_id = response.headers["X-Request-ID"]
    UUID(request_id)
    payload = response.json()
    assert payload["meta"]["request_id"] == request_id
    assert payload["errors"][0]["code"] == "VALIDATION_ERROR"
    assert payload["errors"][0]["field"] in {"ticker", "name"}


def test_validation_context_exceptions_are_json_safe(client) -> None:
    response = client.patch(
        "/ai-outputs/1/review",
        json={"status": "rejected"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["errors"][0]["code"] == "VALIDATION_ERROR"
    assert "Review notes are required" in payload["detail"][0]["msg"]
    assert "ctx" not in payload["detail"][0] and "input" not in payload["detail"][0]


def test_request_ids_are_unique_when_not_supplied(client) -> None:
    first = client.get("/api/health")
    second = client.get("/api/health")

    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]
    UUID(first.headers["X-Request-ID"])
    UUID(second.headers["X-Request-ID"])
