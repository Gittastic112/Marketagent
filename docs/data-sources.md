# Data Sources

## Principle

Start with clean, legal, source-backed inputs.

Do not start with scraping social platforms.

The first version should prioritize public, stable, structured sources.

---

## Source priority

### Tier 1: Start here

| Source | Use | Complexity |
|---|---|---:|
| Manual thesis notes | Store your own thinking | Low |
| SEC EDGAR | Filings | Medium |
| RSS feeds | Basic news | Low |
| FRED | Macro data | Medium |
| Manual document uploads | Research notes/reports | Low |

---

### Tier 2: Add later

| Source | Use | Complexity |
|---|---|---:|
| Alpha Vantage | Market data | Medium |
| Finnhub | Market/news/fundamentals | Medium |
| News API | Headlines | Medium |
| GDELT | macro narrative layer | Medium-high |
| Nasdaq Data Link | datasets | Medium-high |

---

### Tier 3: Much later

| Source | Use | Complexity |
|---|---|---:|
| X/Twitter official API | social diffusion | High |
| Reddit API | community narrative | High |
| Unusual Whales | options/flow | Medium-high |
| SpotGamma | positioning context | Medium |
| Factiva/Dow Jones | premium news | Enterprise |
| Bloomberg/FactSet/LSEG | institutional data | Enterprise |

---

## MVP source plan

Version 0.1:

- manual company entry
- manual thesis notes
- manual raw document entry

Version 0.2:

- RSS ingestion
- SEC filing metadata

Version 0.3:

- SEC filing text
- simple filing change detection

Version 0.4:

- FRED macro series
- basic market data

Version 0.5:

- optional OpenAI-powered document summaries

---

## Data provenance requirements

Every source record must store:

- provider
- source type
- source URL
- published timestamp
- ingestion timestamp
- raw text or raw payload
- content hash
- linked company if applicable

---

## Data licensing rule

If a source prohibits scraping or redistribution, do not scrape it.

Use:

- official APIs
- licensed feeds
- manual review
- approved exports

The system should be legally clean before it becomes powerful.
