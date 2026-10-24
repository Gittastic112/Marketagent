"""Profile matching checks without a database, provider or persisted fixtures."""
from types import SimpleNamespace

import pytest

from app.services.industry_mapping import IndustryMappingService


def suggestions(monkeypatch, industry, sector, taxonomy):
    requested = []

    def available(db, country, *, fallback_to_loaded=True):
        requested.append((country, fallback_to_loaded))
        return taxonomy

    monkeypatch.setattr(IndustryMappingService, "get_available_industries", available)
    monkeypatch.setattr(IndustryMappingService, "_benchmark_availability", lambda *args: {"margins": True})
    company = SimpleNamespace(industry=industry, sector=sector)
    db = SimpleNamespace(get=lambda *args: company)
    result = IndustryMappingService.suggest_damodaran_industries(db, 1, "United States")
    return result, requested


def test_consumer_electronics_does_not_suggest_healthcare_or_biotechnology(monkeypatch):
    rows, _ = suggestions(monkeypatch, "Consumer Electronics", "Technology", [
        "Healthcare Information and Technology", "Business & Consumer Services",
        "Electronics (Consumer & Office)", "Drugs (Biotechnology)", "Software (Internet)",
    ])
    assert [row["industryName"] for row in rows] == ["Electronics (Consumer & Office)"]
    assert "company industry" in rows[0]["reason"]
    assert "review" in rows[0]["reason"].lower()


@pytest.mark.parametrize("industry", [None, "", "Business Services", "Information Technology"])
def test_broad_or_missing_profile_does_not_invent_a_specific_comparison(monkeypatch, industry):
    rows, _ = suggestions(monkeypatch, industry, "Technology", [
        "Healthcare Information and Technology", "Business & Consumer Services", "Software (Internet)",
    ])
    assert rows == []


def test_suggestions_remain_in_the_requested_benchmark_market(monkeypatch):
    rows, requested = suggestions(monkeypatch, "Internet Software", "Technology", [])
    assert rows == []
    assert requested == [("United States", False)]


def test_specific_transport_and_software_words_still_match(monkeypatch):
    rows, _ = suggestions(monkeypatch, "Transport Infrastructure", None, [
        "Transportation", "Transportation (Railroads)", "Farming/Agriculture",
    ])
    assert {row["industryName"] for row in rows} == {"Transportation", "Transportation (Railroads)"}
    rows, _ = suggestions(monkeypatch, "Internet Software", "Technology", [
        "Software (Internet)", "Retail (Grocery and Food)",
    ])
    assert [row["industryName"] for row in rows] == ["Software (Internet)"]


def test_bank_profile_does_not_match_nonbank_financial_services(monkeypatch):
    rows, _ = suggestions(monkeypatch, "Banks", "Financial Services", [
        "Bank (Money Center)", "Financial Svcs. (Non-bank & Insurance)", "Insurance (General)",
    ])
    assert [row["industryName"] for row in rows] == ["Bank (Money Center)"]
