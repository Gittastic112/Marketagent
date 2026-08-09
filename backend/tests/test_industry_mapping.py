import pytest
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.company_setup import CompanySetupWorkflow
from app.models.damodaran import DamodaranDatasetFile
from app.models.damodaran_fundamentals import CountryMarketStats, DamodaranMarginBenchmark
from app.services.industry_mapping import IndustryMappingService

def test_suggest_damodaran_industries(db_session: Session):
    # Setup benchmarks
    dataset = DamodaranDatasetFile(
        uploaded_filename="marginIndia.xls",
        dataset_code="margin",
        country="India",
        source_file_type="xls",
    )
    db_session.add(dataset)
    db_session.flush()

    benchmark1 = DamodaranMarginBenchmark(
        dataset_file_id=dataset.id,
        industry_name="Software (Internet)",
        number_of_firms=10,
        gross_margin=0.8,
        ebitda_margin=0.3,
        ebit_margin=0.2,
        net_margin=0.15,
        country="India"
    )
    benchmark2 = DamodaranMarginBenchmark(
        dataset_file_id=dataset.id,
        industry_name="Retail (Grocery and Food)",
        number_of_firms=5,
        gross_margin=0.2,
        ebitda_margin=0.1,
        ebit_margin=0.05,
        net_margin=0.02,
        country="India"
    )
    db_session.add_all([benchmark1, benchmark2])
    db_session.commit()

    # Setup company
    company = Company(
        name="Tech Startup",
        ticker="TECH",
        industry="Internet Software",
        sector="Technology",
        market="India"
    )
    db_session.add(company)
    db_session.commit()

    # Test
    suggestions = IndustryMappingService.suggest_damodaran_industries(db_session, company.id, "India")

    assert len(suggestions) > 0
    names = [s["industryName"] for s in suggestions]
    assert "Software (Internet)" in names
    software = next(item for item in suggestions if item["industryName"] == "Software (Internet)")
    assert software["benchmarkAvailability"]["margins"] is True
    assert software["benchmarkAvailability"]["capex"] is False

def test_confirm_industry_mapping(db_session: Session):
    dataset = DamodaranDatasetFile(
        uploaded_filename="marginIndia.xls",
        dataset_code="margin",
        country="India",
        source_file_type="xls",
    )
    db_session.add(dataset)
    db_session.flush()
    db_session.add(
        DamodaranMarginBenchmark(
            dataset_file_id=dataset.id,
            industry_name="Software (Internet)",
            country="India",
        )
    )
    company = Company(
        name="Tech Startup",
        ticker="TECH",
        industry="Internet Software",
        market="India"
    )
    db_session.add(company)
    db_session.flush()
    workflow = CompanySetupWorkflow(
        company_id=company.id,
        current_step="financial_review",
        financial_extraction_status="reviewed",
    )
    db_session.add(workflow)
    db_session.commit()

    updated = IndustryMappingService.confirm_industry_mapping(db_session, company.id, "software (internet)")
    assert updated.damodaran_industry == "Software (Internet)"
    db_session.refresh(workflow)
    assert workflow.industry_mapping_status == "reviewed"
    assert workflow.current_step == "valuation_review"

def test_confirm_industry_mapping_not_found(db_session: Session):
    with pytest.raises(ValueError, match="Company not found"):
        IndustryMappingService.confirm_industry_mapping(db_session, 9999, "Software (Internet)")


def test_confirm_industry_mapping_rejects_name_outside_loaded_taxonomy(db_session: Session):
    company = Company(name="Ports Co", ticker="PORT", market="IN", country="India")
    db_session.add(company)
    db_session.commit()

    with pytest.raises(ValueError, match="not present in the loaded taxonomy"):
        IndustryMappingService.confirm_industry_mapping(db_session, company.id, "Advertising")


def test_suggestions_do_not_invent_fallback_without_company_profile(db_session: Session):
    dataset = DamodaranDatasetFile(
        uploaded_filename="marginIndia.xls",
        dataset_code="margin",
        country="India",
        source_file_type="xls",
    )
    db_session.add(dataset)
    db_session.flush()
    db_session.add(
        DamodaranMarginBenchmark(
            dataset_file_id=dataset.id,
            industry_name="Advertising",
            country="India",
        )
    )
    company = Company(name="Unclassified Co", ticker="NONE", market="IN", country="India")
    db_session.add(company)
    db_session.commit()

    assert IndustryMappingService.suggest_damodaran_industries(db_session, company.id, "India") == []


def test_suggestions_exclude_unrelated_edit_distance_matches(db_session: Session):
    dataset = DamodaranDatasetFile(
        uploaded_filename="marginIndia.xls",
        dataset_code="margin",
        country="India",
        source_file_type="xls",
    )
    db_session.add(dataset)
    db_session.flush()
    db_session.add_all(
        [
            DamodaranMarginBenchmark(
                dataset_file_id=dataset.id,
                industry_name=industry_name,
                country="India",
            )
            for industry_name in ("Transportation", "Transportation (Railroads)", "Farming/Agriculture")
        ]
    )
    company = Company(
        name="Ports Co",
        ticker="PORT",
        market="IN",
        country="India",
        industry="Transport Infrastructure",
    )
    db_session.add(company)
    db_session.commit()

    suggestions = IndustryMappingService.suggest_damodaran_industries(db_session, company.id, "India")
    names = [item["industryName"] for item in suggestions]

    assert "Transportation" in names
    assert "Farming/Agriculture" not in names


def test_available_industries_fall_back_to_loaded_taxonomy_country(db_session: Session):
    dataset = DamodaranDatasetFile(
        uploaded_filename="marginIndia.xls",
        dataset_code="margin",
        country="India",
        source_file_type="xls",
    )
    db_session.add(dataset)
    db_session.flush()
    db_session.add(
        DamodaranMarginBenchmark(
            dataset_file_id=dataset.id,
            industry_name="Software (Internet)",
            country="India",
        )
    )
    db_session.commit()

    industries = IndustryMappingService.get_available_industries(
        db_session,
        "United States",
    )

    assert industries == ["Software (Internet)"]
    assert IndustryMappingService.get_available_industries(
        db_session,
        "United States",
        fallback_to_loaded=False,
    ) == []
    assert IndustryMappingService.get_available_countries(db_session) == ["India"]


def test_macro_availability_uses_only_active_country_stats(db_session: Session) -> None:
    old = DamodaranDatasetFile(
        uploaded_filename="countrystats.xls",
        dataset_code="countrystats",
        country="Global",
        source_file_type="xls",
        import_kind="typed",
        is_active=False,
        row_count=1,
    )
    db_session.add(old)
    db_session.flush()
    db_session.add(
        CountryMarketStats(dataset_file_id=old.id, country="India")
    )
    db_session.commit()
    assert IndustryMappingService._benchmark_availability(
        db_session, "India", "Advertising"
    )["macro"] is False

    current = DamodaranDatasetFile(
        uploaded_filename="countrystats.xls",
        dataset_code="countrystats",
        country="Global",
        source_file_type="xls",
        import_kind="typed",
        is_active=True,
        row_count=1,
    )
    db_session.add(current)
    db_session.flush()
    db_session.add(
        CountryMarketStats(dataset_file_id=current.id, country="India")
    )
    db_session.commit()
    assert IndustryMappingService._benchmark_availability(
        db_session, "India", "Advertising"
    )["macro"] is True


def test_available_industry_taxonomy_uses_only_active_margin_versions(
    db_session: Session,
) -> None:
    old = DamodaranDatasetFile(
        uploaded_filename="marginIndia.xls",
        dataset_code="margins",
        country="India",
        source_file_type="xls",
        import_kind="typed",
        is_active=False,
        row_count=1,
    )
    current = DamodaranDatasetFile(
        uploaded_filename="marginIndia.xls",
        dataset_code="margins",
        country="India",
        source_file_type="xls",
        import_kind="typed",
        is_active=True,
        row_count=1,
    )
    db_session.add_all([old, current])
    db_session.flush()
    db_session.add_all([
        DamodaranMarginBenchmark(
            dataset_file_id=old.id,
            industry_name="Obsolete Industry",
            country="India",
        ),
        DamodaranMarginBenchmark(
            dataset_file_id=current.id,
            industry_name="Advertising",
            country="India",
        ),
    ])
    db_session.commit()

    assert IndustryMappingService.get_available_industries(db_session, "India") == [
        "Advertising"
    ]
    assert IndustryMappingService.get_available_countries(db_session) == ["India"]
