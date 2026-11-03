from datetime import datetime

from helpers import response_data, response_errors


def test_schedule_api_starts_unconfigured(client) -> None:
    response = client.get("/daily-brief-schedule")

    assert response.status_code == 200
    assert response_data(response) is None


def test_schedule_api_validates_and_persists_owned_schedule(client) -> None:
    response = client.put(
        "/daily-brief-schedule",
        json={
            "enabled": True,
            "timezone": "Asia/Kolkata",
            "local_time": "07:15:00",
            "days_of_week": [0, 1, 2, 3, 4],
        },
    )

    assert response.status_code == 200
    body = response_data(response)
    assert body["enabled"] is True
    assert body["timezone"] == "Asia/Kolkata"
    assert body["days_of_week"] == [0, 1, 2, 3, 4]
    assert body["generation_mode"] == "deterministic_no_external_ai"
    assert datetime.fromisoformat(body["next_run_at"]).tzinfo is not None

    loaded = response_data(client.get("/daily-brief-schedule"))
    assert loaded["id"] == body["id"]


def test_schedule_api_rejects_invalid_timezone_and_empty_enabled_days(client) -> None:
    invalid_zone = client.put(
        "/daily-brief-schedule",
        json={
            "enabled": True,
            "timezone": "Not/A_Zone",
            "local_time": "07:00:00",
            "days_of_week": [0],
        },
    )
    assert invalid_zone.status_code == 422
    assert response_errors(invalid_zone)[0]["code"] == "VALIDATION_ERROR"

    no_days = client.put(
        "/daily-brief-schedule",
        json={
            "enabled": True,
            "timezone": "UTC",
            "local_time": "07:00:00",
            "days_of_week": [],
        },
    )
    assert no_days.status_code == 422


def test_run_due_endpoint_does_not_force_early_generation(client) -> None:
    client.put(
        "/daily-brief-schedule",
        json={
            "enabled": True,
            "timezone": "UTC",
            "local_time": "23:59:00",
            "days_of_week": [0, 1, 2, 3, 4, 5, 6],
        },
    )

    result = response_data(client.post("/daily-brief-schedule/run-due"))
    assert result["schedules_checked"] == 0
    assert result["briefs_created"] == 0
