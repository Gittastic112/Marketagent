---
name: Security Review
description: A mandatory security checklist for ensuring the Market Intelligence App remains secure during new feature additions. Focuses on SSRF prevention, CSRF, untrusted text rendering, and API key handling.
---

# Security Review Skill

This skill provides a checklist and guidelines for conducting security reviews when adding new features, APIs, or integrations to the Market Intelligence App.

## Pre-Integration Checklist

Before adding any new external API, data import, or AI model integration, verify the following:

- [ ] **No Hardcoded Secrets:** Verify that no API keys, tokens, or credentials are hardcoded in the source code or tests.
- [ ] **`.env` Management:** Ensure that secrets are only loaded from the environment or `.env` files. Ensure `.env.example` does not contain real secrets.
- [ ] **Log Sanitization:** Ensure that proxy routes or data fetchers redact or strip provider keys and authorization headers before logging request/response data.
- [ ] **SSRF Prevention:** If the app accepts user-provided URLs (e.g., RSS feeds, SEC filing URLs, or general web scraping), ensure URL validation blocks requests to localhost, internal network IPs (10.x.x.x, 192.168.x.x, 172.16.x.x), and the Docker socket.
- [ ] **Untrusted Input Rendering:** Treat all imported text (RSS, SEC filings, CSV imports, social posts) and AI-generated outputs as untrusted. Do NOT render them as raw HTML. Use safe rendering conventions (e.g., Markdown parsers that sanitize HTML, or React's default text escaping).
- [ ] **CSV Injection Prevention:** Any CSV export feature MUST prepend a single quote (`'`) to fields starting with `=`, `+`, `-`, or `@` to prevent CSV formula injection attacks when opened in Excel or Google Sheets.
- [ ] **Broker / Financial Integrations:** Do NOT store broker passwords directly. Any future broker integration MUST use official OAuth2 or token-based flows.

## Actionable Guidelines

### URL Validation (SSRF)
When implementing a fetch from a user-supplied URL (like RSS), use a dedicated URL validation function in `backend/app/core/security.py` that parses the URL and explicitly denies internal IP ranges.

### CSV Export Escaping
When generating CSVs (e.g., for portfolios or macros), implement a helper function:
```python
def escape_csv_formula(value: str) -> str:
    if not value:
        return value
    if value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value
```

### React / Next.js Safe Rendering
When rendering raw text or AI summaries on the frontend, avoid `dangerouslySetInnerHTML`. If you must render Markdown, use a library like `react-markdown` which escapes HTML tags by default.

### External API Mocking
Do not call live external APIs (like OpenAI, SEC, or RSS feeds) in the automated test suite. Use `unittest.mock.patch` or pytest fixtures to mock HTTP responses.
