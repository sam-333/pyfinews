# API reference

This document describes the public API of `pyfinews`. The package discovers financial news through Google News RSS and can enrich results with publisher URLs and extracted article text. Article-text extraction and Google News URL resolution are included in the standard installation; they do not require separate feature extras.

## Package version

Use `pyfinews.__version__` to inspect the installed package version:

```python
import pyfinews
print(pyfinews.__version__)
```

Version access is centralized in the internal `pyfinews._version` module and reads the installed distribution metadata. If metadata is unavailable, the fallback value is `0+unknown`.

## `NewsClient`

```python
NewsClient(
    *,
    timeout: float = 10.0,
    provider=None,
    taxonomy: list[dict] | None = None,
    publishers: list[dict] | None = None,
    query_limit: int = 30,
    article_timeout: float = 15.0,
    url_resolver=None,
)
```

Creates a client. Construction loads local configuration but does not make network requests.

- `timeout`: timeout in seconds for Google News RSS requests.
- `provider`: optional custom RSS provider; otherwise the default Google News RSS provider is used.
- `taxonomy`: optional taxonomy records; if omitted, packaged defaults are loaded.
- `publishers`: optional publisher records; if omitted, packaged defaults are loaded.
- `query_limit`: maximum number of planned queries to execute.
- `article_timeout`: timeout in seconds for publisher-page requests during article-text extraction.
- `url_resolver`: optional custom URL resolver.

### `get`

```python
get(*, topic=None, hours=24, max_articles=20, query_limit=None, resolve_urls=False)
```

Plans one or more queries and returns up to `max_articles` `NewsArticle` objects. Set `max_articles=None` to disable the client-side limit. `topic=None` selects the market-wide taxonomy flow. `hours=None` disables freshness operators and local lookback filtering. `query_limit` overrides the client-level query budget for this call. `resolve_urls=True` resolves Google News RSS links to publisher URLs after discovery.

### `search`

```python
search(query: str, *, hours: float | None = 24, max_articles: int | None = 20, resolve_urls: bool = False)
```

Executes a single arbitrary query. Set `hours=None` to disable freshness constraints and local lookback filtering. Set `resolve_urls=True` to resolve publisher URLs after discovery.

### URL resolution methods

```python
resolve_article_url(article)
resolve_article_urls(articles)
```

Resolve the Google News RSS URL for one article or a batch. Batch processing is sequential and preserves input order.

### Article-text methods

```python
extract_article_text(article)
extract_articles_text(articles)
```

`extract_article_text` accepts a `NewsArticle` or an HTTP(S) URL and returns an `ArticleTextResult`. `extract_articles_text` accepts a list of `NewsArticle` objects and/or URL strings. It returns one result per input in the same order; duplicate inputs are preserved. Processing is sequential.

### Resource management

`NewsClient` supports `close()` and context-manager use:

```python
with NewsClient() as client:
    articles = client.get(topic="equities")
```

The default provider uses the standard-library HTTP client and does not maintain a persistent connection. Context-manager usage makes lifecycle intent explicit and supports custom providers.

## `NewsArticle`

`NewsArticle` is an immutable normalized article model with these fields:

- `title: str`
- `url: str`
- `source: str | None`
- `published_at: datetime | None`
- `retrieved_at: datetime | None`
- `summary: str | None`
- `query: str | None`
- `resolved_url: str | None`
- `url_resolution_status: str | None` (`success` or `resolution_failed`)
- `url_resolution_error: str | None`

Non-null datetime values must be timezone-aware and are normalized to UTC. `url` remains the URL supplied by the RSS feed. When resolution succeeds, `resolved_url` contains the publisher URL. Article-text extraction prefers `resolved_url` when set; if resolution explicitly failed, extraction does not silently treat the RSS URL as a publisher URL.

## `ArticleTextExtractor` and `ArticleTextResult`

`ArticleTextExtractor` downloads publisher pages and uses Trafilatura to extract the main article text.

`ArticleTextResult` contains:

- `url: str`
- `text: str | None`
- `status: ArticleTextStatus`: `SUCCESS`, `FETCH_FAILED`, or `EXTRACTION_FAILED` (string values: `success`, `fetch_failed`, and `extraction_failed`)
- `error: str | None`

Expected per-URL failures are represented in results so batches can continue. Extraction does not bypass publisher access controls; pages may be inaccessible or may not expose extractable text.

## `GoogleNewsURLResolver` and `URLResolutionResult`

`GoogleNewsURLResolver.resolve(url)` resolves one Google News RSS URL and returns a `URLResolutionResult`. `resolve_many(urls)` processes URLs sequentially and preserves input order. A result includes the original `rss_url`, optional `resolved_url`, `status`, and `error`.

## HTTP User-Agent defaults

The default HTTP User-Agent is generated centrally as `pyfinews/<installed-version>` by `pyfinews._version`. It is used by the Google News RSS provider and article-text extractor, so it tracks the installed package version instead of remaining hardcoded to an older release. Both components accept a `user_agent` constructor argument to override the default.

## Exceptions

- `PyfinewsError`: base package exception.
- `NewsFetchError`: request or transport failure.
- `NewsParseError`: invalid or structurally unexpected RSS/XML response.
- `PublisherLoadError`: publisher configuration loading or validation failure.
- `TaxonomyLoadError`: taxonomy configuration loading or validation failure.

## Progress reporting

Sequential batch operations can report progress, including URL resolution and article-text extraction. Progress is written to standard error; interactive terminals use in-place updates, while redirected output uses separate lines. Disable progress through the relevant operation's supported progress option, where exposed.

## Public exports

The package root exposes the principal client, models, providers, query builders, URL-resolution and article-text classes, loaders, filters, deduplication helpers, exceptions, and `__version__`. See `src/pyfinews/__init__.py` for the exact export list.
