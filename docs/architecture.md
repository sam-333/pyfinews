# Architecture

## Overview

`pyfinews` separates the public client, query planning, RSS transport and parsing, normalized data models, URL resolution, article-text extraction, and configuration loading. Package version access and the default HTTP User-Agent are centralized in a small internal module.

```text
                         +---------------------+
                         |      NewsClient     |
                         +---------------------+
                           |       |        |
                           v       v        v
                  FinancialQuery  Google   URL resolution
                     Builder      News RSS  + article text
                       |          Provider       |
                       v             |           v
                taxonomy +           v     publisher pages
                publishers       NewsArticle

                   _version.py
                     |       |
                     v       v
               __version__  DEFAULT_USER_AGENT
```

## Modules

- `client.py`: public orchestration, query budgeting, lookback filtering, sorting, result caps, and coordination of URL resolution and article-text extraction.
- `_version.py`: retrieves the installed distribution version and defines the shared default HTTP User-Agent. It is an internal module and does not import the public package API.
- `queries/google_news.py`: Google News RSS query value object and query URL encoding.
- `queries/financial.py`: market-wide and topic-specific query planning.
- `providers/google_news.py`: Google News RSS HTTP transport using `urllib.request`; RSS/Atom parsing and normalization are delegated to `feedparser`.
- `models.py`: immutable normalized article and result models, including URL-resolution metadata.
- `url_resolution.py`: Google News RSS URL resolution using `googlenewsdecoder`.
- `article_text.py`: publisher-page download and Trafilatura main-text extraction.
- `filters.py`: local lookback filtering.
- `deduplication.py`: title normalization and article deduplication helpers. Deduplication is an explicit utility, not an automatic discovery-stage behavior.
- `taxonomy/loader.py`: taxonomy loading and validation.
- `publishers/loader.py`: publisher metadata loading and validation.
- Progress utility module(s): shared progress reporting for sequential batch operations.
- `exceptions.py`: package-level exceptions for fetch/parse failures and configuration loading.

## Version and User-Agent handling

`_version.py` is the single source for runtime package-version access and the default HTTP User-Agent:

- `__version__` is read from the installed `pyfinews` distribution metadata.
- If distribution metadata cannot be found, the fallback is `0+unknown`.
- `DEFAULT_USER_AGENT` is built as `pyfinews/<version>`.
- `__init__.py`, `article_text.py`, and `providers/google_news.py` import from `_version.py`, rather than importing version constants from one another.

This avoids a circular import in which a submodule imports `__version__` from `pyfinews` while `pyfinews/__init__.py` is still importing that submodule.

## Runtime dependencies

- `urllib.request` provides HTTP transport for Google News RSS and publisher-page requests.
- `feedparser` parses RSS/Atom responses.
- `googlenewsdecoder` resolves Google News RSS URLs to publisher URLs.
- `trafilatura` extracts main text from publisher pages.

These features are included in the standard installation; article-text extraction and URL resolution do not require separate extras. Development tooling is installed through the `dev` extra. Consult `pyproject.toml` for authoritative dependency constraints.

## Query planning and result flow

1. `NewsClient` receives the request and determines whether to use market-wide or topic-specific query planning.
2. `FinancialQueryBuilder` creates candidate queries using configured taxonomy and publisher metadata.
3. `GoogleNewsQuery` encodes each query for Google News RSS.
4. `GoogleNewsRSSProvider` requests and parses RSS/Atom results.
5. Results are normalized into `NewsArticle` objects.
6. Client-side filtering, sorting, and result limits are applied.
7. If requested, URL resolution enriches articles with publisher URLs. Article-text extraction can then use the resolved publisher URL.

## Duplicate handling

The package does not automatically deduplicate discovery results. Repeated stories can occur when planned queries overlap or the feed contains repeated items. This is intentional; callers can use the exported deduplication helpers when they want to apply a deduplication policy.

## Failure handling

- Transport failures are wrapped as `NewsFetchError`.
- Invalid RSS/XML or missing required feed structure raises `NewsParseError`.
- Taxonomy and publisher configuration failures use their respective loader exceptions.
- Invalid public argument values raise `ValueError` or `TypeError`, as appropriate.
- Missing or malformed publication dates are treated as unknown rather than causing parsing to fail.
- URL resolution and article-text extraction return structured per-item statuses for expected item-level failures, allowing batch processing to continue.

## Batch processing and progress

URL resolution and article-text extraction process inputs sequentially and preserve input order. Progress reporting writes to standard error and adapts to interactive terminals versus redirected output. Per-item URL-resolution and extraction failures are represented in their result objects; other failures may be reported and raised according to the operation's contract.

## Article-text extraction limitations

Article extraction downloads publisher pages and passes the response body to Trafilatura. It does not bypass paywalls, authentication, robots restrictions, or other publisher access controls. Some pages may not be accessible or may not expose extractable article text.
