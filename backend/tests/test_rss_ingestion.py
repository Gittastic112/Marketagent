from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, RawDocument, Source
from app.services.rss_ingestion import ingest_rss_xml


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
    assert first_result.skipped_duplicates == 0
    assert second_result.created == 0
    assert second_result.skipped_duplicates == 2
    assert len(documents) == 2
    assert documents[0].document_type == "rss_item"
    assert documents[0].title == "Apple expands services"
    assert documents[0].url == "https://example.com/apple-services"
    assert documents[0].raw_text == "Apple announced a services expansion."
    assert documents[0].raw_payload_json["source_kind"] == "rss"
