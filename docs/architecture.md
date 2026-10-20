# Architecture

## Overview

`pyfinews` separates the public client, query planning, RSS transport/parsing, data models, and configuration loading.

```text
NewsClient
  ├── FinancialQueryBuilder ── taxonomy + publisher configuration
  ├── GoogleNewsQuery ── query encoding and URL construction
  └── GoogleNewsRSSProvider ── HTTP request and RSS/XML parsing
        └── NewsArticle results
```

## Modules

- `client.py`: public orchestration, request budgeting, lookback filtering, sorting, and result caps.
- `queries/google_news.py`: Google News RSS query value object and URL encoding.
- `queries/financial.py`: market-wide and topic query planning.
- `providers/google_news.py`: HTTP transport using `urllib.request`, with RSS/Atom parsing and normalization delegated to `feedparser`.
- `models.py`: immutable normalized article model.
- `article_text.py`: optional publisher-page download and Trafilatura main-text extraction.
- `filters.py`: local lookback filtering.
- `taxonomy/loader.py`: domain taxonomy loading and validation.
- `publishers/loader.py`: publisher metadata loading and validation.
- `exceptions.py`: package-level fetch and parse exceptions.

## Runtime dependencies

HTTP transport uses `urllib.request`; RSS/Atom parsing uses `feedparser`. The runtime dependency is declared in `pyproject.toml`. The `dev` extra installs test/build/lint tools. The optional `article-text` extra installs Trafilatura and its extraction dependencies.

## Duplicate handling

The package deliberately does not deduplicate article records. Repeated stories can occur when several planned queries overlap or when the feed itself contains repeated items. This behavior is intentional until a deduplication policy is explicitly reintroduced.

## Failure handling

Transport failures are wrapped as `NewsFetchError`. Invalid RSS/XML or missing required feed structure raises `NewsParseError`. Invalid public argument values raise `ValueError` or `TypeError` as appropriate. Missing or malformed publication dates are treated as unknown rather than causing parsing to fail.

## Article text extraction

Article extraction is separate from RSS discovery. It downloads each publisher URL with the standard-library HTTP client, then passes the response body to Trafilatura. Per-URL fetch and extraction failures are returned as statuses, allowing batches to continue. This does not circumvent paywalls or authentication.
