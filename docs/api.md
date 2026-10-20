# API reference

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

### `get`

```python
get(*, topic=None, hours=24, max_articles=20, query_limit=None, resolve_urls=False)
```

Plans one or more queries and returns up to `max_articles` `NewsArticle` objects; `max_articles=None` disables the client-side limit. `topic=None` selects the market-wide taxonomy flow. `hours=None` disables freshness operators and local lookback filtering. Set `resolve_urls=True` to resolve publisher URLs after discovery; this requires the optional `url-resolution` extra.

### `search`

```python
search(query: str, *, hours: float | None = 24, max_articles: int | None = 20, resolve_urls: bool = False)
```

Executes a single arbitrary query. Set `resolve_urls=True` to resolve publisher URLs after discovery.

### Resource management

The client supports `close()` and context-manager use. The default standard-library provider does not maintain a persistent connection, but context-manager usage makes lifecycle intent explicit and supports custom providers.

## `NewsArticle`

Immutable fields:

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

Non-null datetime values must be timezone-aware and are normalized to UTC.

## Exceptions

- `PyfinewsError`: base package exception.
- `NewsFetchError`: request or transport failure.
- `NewsParseError`: invalid or structurally unexpected RSS/XML response.


## Article-text extraction (optional)

Install the optional dependency group with `uv sync --extra article-text`.

### `NewsClient.extract_article_text(article)`

Accepts a `NewsArticle` or HTTP(S) URL and returns one `ArticleTextResult`.

### `NewsClient.extract_articles_text(articles)`

Accepts a list of `NewsArticle` objects and/or URL strings. Returns one result per input in the same order; duplicate inputs are preserved. Processing is sequential.

### `ArticleTextResult`

- `url: str`
- `text: str | None`
- `status: ArticleTextStatus`: `SUCCESS`, `FETCH_FAILED`, or `EXTRACTION_FAILED` (string values are `success`, `fetch_failed`, and `extraction_failed`)
- `error: str | None`

Extraction does not bypass publisher access controls. A page may be inaccessible or may not expose extractable article text.


## Google News URL resolution

`GoogleNewsURLResolver.resolve(url)` returns a `URLResolutionResult` with the original `rss_url`, optional `resolved_url`, `status`, and `error`. `resolve_many(urls)` processes sequentially and preserves order. Resolution requires the optional `url-resolution` extra.

`NewsArticle.url` remains the URL supplied by the RSS feed. The optional `NewsArticle.resolved_url` field holds the publisher URL when resolution has been performed. `NewsClient.resolve_article_url(article)` resolves one article, while `resolve_article_urls(articles)` resolves a batch. `get()` and `search()` can resolve URLs with `resolve_urls=True`. `ArticleTextExtractor.extract(article)` prefers `resolved_url` when set and falls back to `url` only when resolution has not explicitly failed.
