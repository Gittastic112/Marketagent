from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, RawDocument, Source
from app.services.rss_ingestion import ingest_rss_feed_url, ingest_rss_xml


RSS_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>Market News</title>
    <item>
      <title>Apple expands services</title>
      <link>https://example.com/apple-services</link>
      <description>Apple announced a services expansion.</description>
      <pubDate>Sun, 24 May 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Microsoft cloud demand rises</title>
      <link>https://example.com/msft-cloud</link>
      <description>Cloud demand increased.</description>
    </item>
  </channel>
</rss>
"""


def test_ingest_rss_xml_stores_raw_documents_and_skips_duplicates() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple Inc.")
        source = Source(name="Example RSS", source_type="rss", base_url="https://example.com/feed.xml")
        session.add_all([company, source])
        session.commit()

        first_result = ingest_rss_xml(session, source_id=source.id, rss_xml=RSS_XML, company_id=company.id)
        second_result = ingest_rss_xml(session, source_id=source.id, rss_xml=RSS_XML, company_id=company.id)
        documents = list(session.scalars(select(RawDocument).order_by(RawDocument.id)))

    assert first_result.created == 2
    assert first_result.fetched_count == 2
    assert first_result.created_count == 2
    assert first_result.error_count == 0
    assert first_result.skipped_duplicates == 0
    assert second_result.created == 0
    assert second_result.skipped_duplicate_count == 2
    assert second_result.skipped_duplicates == 2
    assert len(documents) == 2
    assert documents[0].document_type == "rss_item"
    assert documents[0].title == "Apple expands services"
    assert documents[0].url == "https://example.com/apple-services"
    assert documents[0].raw_text == "Apple announced a services expansion."
    assert documents[0].raw_payload_json["source_kind"] == "rss"
    assert documents[0].raw_payload_json["source_name"] == "Example RSS"
    assert documents[0].raw_payload_json["pubDate"] == "Sun, 24 May 2026 12:00:00 GMT"
    assert documents[0].published_at is not None
    assert documents[0].ingested_at is not None
    assert documents[0].content_hash


def test_ingest_rss_xml_treats_same_source_url_as_duplicate_and_links_obvious_company() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    rss_xml = """<rss version="2.0">
      <channel>
        <item>
          <title>NVDA supply update</title>
          <link>https://example.com/nvda-supply</link>
          <description>NVIDIA supply improved.</description>
        </item>
        <item>
          <title>Nvidia supply follow-up</title>
          <link>https://example.com/nvda-supply</link>
          <description>Duplicate URL with different text.</description>
        </item>
      </channel>
    </rss>
    """

    with Session(engine) as session:
        company = Company(ticker="NVDA", name="NVIDIA Corporation")
        source = Source(name="Example RSS", source_type="rss", base_url="https://example.com/feed.xml")
        session.add_all([company, source])
        session.commit()

        result = ingest_rss_xml(session, source_id=source.id, rss_xml=rss_xml)
        documents = list(session.scalars(select(RawDocument).order_by(RawDocument.id)))

    assert result.fetched_count == 2
    assert result.created_count == 1
    assert result.skipped_duplicate_count == 1
    assert len(documents) == 1
    assert documents[0].company_id == company.id


def test_ingest_rss_xml_links_company_by_alias() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    rss_xml = """<rss version="2.0">
      <channel>
        <item>
          <title>Google expands cloud capacity</title>
          <link>https://example.com/google-cloud</link>
          <description>Cloud demand remains strong.</description>
        </item>
      </channel>
    </rss>
    """

    with Session(engine) as session:
        company = Company(ticker="GOOGL", name="Alphabet Inc.", aliases_json=["Google"])
        source = Source(name="Example RSS", source_type="rss")
        session.add_all([company, source])
        session.commit()

        ingest_rss_xml(session, source_id=source.id, rss_xml=rss_xml)
        document = session.scalar(select(RawDocument))

    assert document is not None
    assert document.company_id == company.id


def test_ingest_rss_xml_does_not_link_ambiguous_company_match() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    rss_xml = """<rss version="2.0">
      <channel>
        <item>
          <title>Cloud demand rises</title>
          <link>https://example.com/cloud-demand</link>
          <description>Cloud revenue remains important.</description>
        </item>
      </channel>
    </rss>
    """

    with Session(engine) as session:
        first_company = Company(ticker="MSFT", name="Microsoft", aliases_json=["Cloud"])
        second_company = Company(ticker="AMZN", name="Amazon", aliases_json=["Cloud"])
        source = Source(name="Example RSS", source_type="rss")
        session.add_all([first_company, second_company, source])
        session.commit()

        ingest_rss_xml(session, source_id=source.id, rss_xml=rss_xml)
        document = session.scalar(select(RawDocument))

    assert document is not None
    assert document.company_id is None


def test_ingest_rss_feed_url_uses_mocked_fetcher_and_reports_errors() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    class FakeResponse:
        text = RSS_XML

        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        return FakeResponse()

    def failing_get(url: str, **kwargs: object) -> FakeResponse:
        raise RuntimeError("network unavailable")

    with Session(engine) as session:
        source = Source(name="Example RSS", source_type="rss", base_url="https://example.com/feed.xml")
        session.add(source)
        session.commit()

        result = ingest_rss_feed_url(session, source_id=source.id, feed_url=source.base_url, http_get=fake_get)
        error_result = ingest_rss_feed_url(session, source_id=source.id, feed_url=source.base_url, http_get=failing_get)
        documents = list(session.scalars(select(RawDocument).order_by(RawDocument.id)))

    assert result.fetched_count == 2
    assert result.created_count == 2
    assert result.error_count == 0
    assert len(documents) == 2
    assert error_result.created_count == 0
    assert error_result.error_count == 1
