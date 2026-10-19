# pyfinews

`pyfinews` is a lightweight Python library for discovering financial-news headlines through Google News RSS. It provides a small client API, configurable financial-domain taxonomy, publisher-priority query planning, date filtering, and normalized article models.

The RSS provider uses Python's standard library for HTTP transport and `feedparser` for RSS/Atom parsing. Optional article downloading and main-text extraction are handled by Trafilatura. `feedparser` is installed automatically as a runtime dependency.

## Features

- General financial-news discovery across configurable domains.
- Topic-specific discovery for tickers, companies, sectors, macro topics, and search phrases.
- Configurable RSS request budget through `query_limit`.
- Publisher selection ordered by ascending `priority` (priority `1` is highest).
- Multiple domain terms combined into a single OR expression per publisher/domain combination.
- Configurable publisher and domain JSON files.
- Lookback filtering and newest-first sorting.
- No article deduplication: repeated items returned by Google News or overlapping queries are preserved.
- Testable transport and query-planning layers.
- Optional Google News RSS URL resolution to publisher URLs.
- Optional article main-text extraction with Trafilatura.

## Requirements

- Python 3.12 or newer.
- `uv` is recommended for environment and dependency management.

## Installation

Install from a local checkout:

```bash
uv sync --extra dev
```

Install from a package index if published:

```bash
uv add pyfinews
```

## Optional article-text extraction

Article text extraction is an optional dependency so headline discovery does not need to install the extraction stack. From a source checkout, install it with:

```bash
uv sync --extra article-text
```

Or, when installing the published package, use the `article-text` extra. Then:

```python
from pyfinews import NewsClient

with NewsClient() as news:
    articles = news.search('Apple earnings', max_articles=10, resolve_urls=True)
    results = news.extract_articles_text(articles)

for article, result in zip(articles, results):
    if result.status == "success":
        print(article.title)
        print(result.text)
    else:
        print(article.title, result.status, result.error)
```

`extract_article_text(article)` handles one `NewsArticle` or an HTTP(S) URL. `extract_articles_text(articles)` processes a list sequentially and preserves input order and duplicates. Each `ArticleTextResult` contains `url`, `text`, `status`, and `error`. `ArticleTextStatus` is a public string enum with `SUCCESS`, `FETCH_FAILED`, and `EXTRACTION_FAILED`; an individual page failure does not stop the batch. Trafilatura handles both publisher-page downloading and main-text extraction. Article extraction does not bypass paywalls, logins, or publisher access controls.

## Optional Google News URL resolution

Google News RSS entries commonly link to Google News URLs rather than directly to publisher pages. URL resolution is an optional, separate step; the normal RSS ingestion flow remains unchanged. You can resolve results directly through `NewsClient` using `resolve_urls=True` on `get()` or `search()`, or call `resolve_article_urls()` on existing results. Install the resolver extra from a source checkout:

```bash
uv sync --extra url-resolution
```

After exporting RSS results to a JSON array (or an object with an `articles` array), resolve them with:

```bash
uv run --extra url-resolution python scripts/resolve_urls.py data/articles.json
```

The script writes `data/articles_resolved.json` by default. It preserves the original `url` field, adds `rss_url`, `resolved_url`, `url_resolution_status`, and `url_resolution_error`, and continues processing when individual URLs fail. The original RSS URL remains available for provenance. The `NewsArticle.resolved_url` field is optional and appended to the model to preserve existing positional arguments. `ArticleTextExtractor.extract(article)` uses `resolved_url` when present and otherwise falls back to `url`. URL resolution does not bypass publisher paywalls, access controls, or site availability problems.

## Quick start

```python
from pyfinews import NewsClient

with NewsClient() as news:
    # Broad financial-news discovery
    market_news = news.get(hours=24, query_limit=30, max_articles=100)

    # Topic-specific discovery
    apple_news = news.get(
        topic='AAPL OR "Apple Inc"',
        hours=72,
        query_limit=10,
        max_articles=50,
    )

    # A single custom Google News query
    custom_news = news.search('semiconductor supply chain', hours=48, max_articles=20)

for article in market_news:
    print(article.published_at, article.source, article.title)
    print(article.url)
```

## API overview

### `NewsClient(...)`

- `timeout=10.0`: HTTP timeout in seconds.
- `query_limit=30`: default maximum number of RSS requests made by each `get()` call.
- `taxonomy=None`: optional list of domain configuration dictionaries.
- `publishers=None`: optional list of publisher configuration dictionaries.
- `provider=None`: optional provider implementation, useful for testing or customization.

### `news.get(...)`

- `topic=None`: optional ticker, company, sector, macro topic, or query phrase. If omitted, uses the financial taxonomy.
- `hours=24`: lookback window in hours. Set to `None` to disable local lookback filtering and omit the freshness operator.
- `max_articles=20`: maximum number of articles returned; pass `None` for no client-side maximum.
- `query_limit=None`: per-call maximum number of RSS requests; defaults to the client's configured budget.

`max_articles` controls the maximum number of returned articles; `max_articles=None` disables the result limit (the number returned still depends on what Google News supplies). `query_limit` controls the number of RSS requests, not the number of articles. Each attempted query consumes one request from the budget. A small budget favors higher-priority publishers and may not cover every domain.

### `news.search(query, ...)`

Runs one arbitrary query without the financial taxonomy or publisher query planner. It accepts `hours` and `max_articles`, but not `query_limit` because it makes one RSS request.

### `NewsArticle`

Each result is an immutable `NewsArticle` with `title`, `url`, optional `source`, `published_at`, `retrieved_at`, `summary`, `query`, `resolved_url`, `url_resolution_status`, and `url_resolution_error` fields. Datetimes are normalized to UTC. `url` retains the URL supplied by the feed; `resolved_url` optionally stores the publisher URL.

## Query planning

For market-wide discovery, the planner:

1. Excludes domains and publishers marked `enabled: false`.
2. Sorts enabled publishers by ascending numeric `priority`, with publisher ID as a deterministic tie-breaker.
3. Combines all configured terms within each domain into one quoted OR expression.
4. Generates publisher/domain queries, iterating publishers by priority and domains in taxonomy order.
5. Appends broad domain-only queries after publisher-targeted combinations.
6. Removes duplicate query strings and returns no more than `query_limit` queries.

For topic-specific discovery, the planner starts with the base topic query, followed by publisher-targeted variants in priority order. Publisher names are query hints, not strict source filters. The `aliases` and `regions` fields are retained as metadata; they do not currently affect query selection.

## Configuration

Default JSON files ship with the package:

- `pyfinews.taxonomy/default_taxonomy.json`: financial domains and query terms.
- `pyfinews.publishers/default_publishers.json`: publisher metadata.

Example publisher entry:

```json
{
  "id": "reuters",
  "name": "Reuters",
  "aliases": ["Reuters News"],
  "regions": ["global", "asia"],
  "enabled": true,
  "priority": 1
}
```

Load the defaults or a custom configuration file:

```python
from pyfinews import load_publishers, load_taxonomy

domains = load_taxonomy()
publishers = load_publishers()
custom_domains = load_taxonomy("config/taxonomy.json")
custom_publishers = load_publishers("config/publishers.json")
```

See [Configuration](docs/configuration.md) for the schema and validation rules.

## Development and tests

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run python -m compileall -q src tests
```

An optional live RSS check is available at `scripts/validate_rss.py`. It makes external network requests, so it is separate from the unit test suite:

```bash
uv run python scripts/validate_rss.py
```

## Important behavior and limitations

- Google News RSS is not a stable, officially documented search API; behavior and availability may change.
- Freshness operators are approximate; local date filtering is also applied when `hours` is specified.
- Publisher names in queries do not guarantee that all results originate from that publisher.
- Summary text and timestamps depend on the RSS entries returned by Google News.
- Headline discovery retrieves RSS-provided metadata. Optional article-text extraction attempts to retrieve publisher pages, but does not bypass paywalls, logins, or publisher access controls; some pages may not yield text.

## Documentation

- [Architecture](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [API reference](docs/api.md)

## License

MIT. See [LICENSE](LICENSE).


### Progress updates for URL resolution and text extraction

`NewsClient.get()` and `NewsClient.search()` print item-level progress updates to stderr by default when URL resolution or article-text extraction is enabled. Set `show_progress=False` to suppress these updates. Headlines are deduplicated by normalized title before `max_articles` is applied; URLs are not part of the deduplication key.

```python
articles = client.get(
    topic="AAPL",
    max_articles=20,
    resolve_urls=True,
    extract_text=True,
    show_progress=True,
)
```
