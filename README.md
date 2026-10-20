# pyfinews

`pyfinews` is a lightweight Python library for discovering financial-news headlines through Google News RSS. It provides a high-level client API, configurable financial-domain taxonomy, publisher-priority query planning, date filtering, normalized article models, Google News URL resolution, and article-text extraction.

The package uses Python's standard library for HTTP transport, `feedparser` for RSS/Atom parsing, `googlenewsdecoder` and `selectolax` for resolving Google News links, and Trafilatura for downloading publisher pages and extracting main article text. These are runtime dependencies and are installed automatically with `pyfinews`.

## Features

- Discover financial news across configurable domains and topics.
- Search for tickers, companies, sectors, macroeconomic topics, and arbitrary phrases.
- Configure the RSS request budget through `query_limit`.
- Prioritize publishers by ascending `priority` (priority `1` is highest).
- Combine domain terms into OR expressions for publisher/domain query planning.
- Load default or custom publisher and domain JSON configuration.
- Filter by lookback window and sort results newest-first.
- Deduplicate returned headlines by normalized title before applying `max_articles`.
- Optionally resolve Google News RSS links to publisher URLs.
- Optionally download article pages and extract their main text.
- Preserve item-level failures as result statuses so one problematic article does not stop a batch.
- Keep transport and query-planning layers testable and customizable.

## Requirements

- Python 3.12 or newer.
- `uv` is recommended for development and dependency management. `pip` can also be used to install the published package.

## Installation

Install the published package with `uv`:

```bash
uv add pyfinews
```

Or install it with `pip`:

```bash
python -m pip install pyfinews
```

To work on a local checkout, install the development dependencies:

```bash
uv sync --extra dev
```

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

    # One custom Google News query
    semiconductor_news = news.search(
        "semiconductor supply chain",
        hours=48,
        max_articles=20,
    )

    # Resolve Google News URLs and extract article text when useful
    resolved_articles = news.get(
        topic="AAPL",
        max_articles=10,
        resolve_urls=True,
        extract_text=True,
        show_progress=False,
    )

for article in market_news:
    print(article.published_at, article.source, article.title)
    print(article.url)
```

`show_progress` controls item-level progress messages written to stderr during URL resolution or text extraction. Set `show_progress=False` to suppress them.

## Article-text extraction

Article-text extraction is available through Trafilatura, which is installed as a runtime dependency. Use `NewsClient` to process a batch:

```python
from pyfinews import NewsClient

with NewsClient() as news:
    articles = news.search(
        'Apple earnings',
        max_articles=10,
        resolve_urls=True,
    )
    results = news.extract_articles_text(articles)

for article, result in zip(articles, results):
    if result.status == "success":
        print(article.title)
        print(result.text)
    else:
        print(article.title, result.status, result.error)
```

The client also provides `extract_article_text(article)` for one `NewsArticle` or an HTTP(S) URL. `extract_articles_text(articles)` processes a list sequentially and preserves input order and duplicates. Each `ArticleTextResult` contains `url`, `text`, `status`, and `error`. `ArticleTextStatus` is a public string enum with `SUCCESS`, `FETCH_FAILED`, and `EXTRACTION_FAILED` statuses. A page-level failure is returned as a result and does not stop the batch.

Trafilatura handles publisher-page downloading and main-text extraction. Extraction may fail because of site structure, network issues, or publisher restrictions. It does not bypass paywalls, logins, or other access controls.

## Google News URL resolution

Google News RSS entries commonly link to Google News URLs rather than directly to publisher pages. URL resolution is a separate step and does not change the original RSS URL. Resolve URLs during a client query with `resolve_urls=True`, or resolve articles you already have using `resolve_article_urls()`.

```python
from pyfinews import NewsClient

with NewsClient() as news:
    articles = news.search(
        'Apple earnings',
        max_articles=10,
        resolve_urls=True,
        show_progress=False,
    )

for article in articles:
    print(article.title)
    print("RSS URL:", article.url)
    print("Publisher URL:", article.resolved_url)
    print("Resolution status:", article.url_resolution_status)
```

The package also includes a script for resolving URLs in an exported JSON file. The input can be a JSON array or an object containing an `articles` array:

```bash
uv run python scripts/resolve_urls.py data/articles.json
```

By default, the script writes `data/articles_resolved.json`. It preserves the original `url` field and adds `rss_url`, `resolved_url`, `url_resolution_status`, and `url_resolution_error`. Individual failures do not stop the batch, and the original RSS URL remains available for provenance.

`NewsArticle.resolved_url` is optional. Article-text extraction uses `resolved_url` when present and otherwise falls back to `url`. URL resolution does not guarantee that a publisher page is accessible or extractable, and it does not bypass paywalls or other access controls.

## API overview

### `NewsClient(...)`

- `timeout=10.0`: HTTP timeout in seconds.
- `query_limit=30`: default maximum number of RSS requests made by each `get()` call.
- `taxonomy=None`: optional list of domain configuration dictionaries.
- `publishers=None`: optional list of publisher configuration dictionaries.
- `provider=None`: optional provider implementation, useful for testing or customization.

### `news.get(...)`

- `topic=None`: optional ticker, company, sector, macro topic, or query phrase. If omitted, the financial taxonomy is used.
- `hours=24`: lookback window in hours. Set to `None` to disable local lookback filtering and omit the freshness operator.
- `max_articles=20`: maximum number of articles returned; pass `None` for no client-side maximum.
- `query_limit=None`: per-call maximum number of RSS requests; defaults to the client's configured budget.
- `resolve_urls=False`: whether to resolve Google News URLs to publisher URLs.
- `extract_text=False`: whether to extract main text from article pages.
- `show_progress=True`: whether to display item-level progress during URL resolution or text extraction.

`max_articles` controls the maximum number of returned articles; `max_articles=None` disables the client-side result limit. The number returned still depends on what Google News supplies. Headlines are deduplicated by normalized title before `max_articles` is applied; the URL is not part of the deduplication key.

`query_limit` controls the number of RSS requests, not the number of articles. Each attempted query consumes one request from the budget. A small budget favors higher-priority publishers and may not cover every domain.

### `news.search(query, ...)`

Runs one arbitrary query without the financial taxonomy or publisher query planner. It accepts `hours` and `max_articles`, and supports URL resolution and article-text extraction when requested. It makes one RSS request, so `query_limit` does not apply.

### `NewsArticle`

Each result is an immutable `NewsArticle` with `title`, `url`, optional `source`, `published_at`, `retrieved_at`, `summary`, `query`, `resolved_url`, `url_resolution_status`, and `url_resolution_error` fields. Datetimes are normalized to UTC. `url` retains the URL supplied by the feed; `resolved_url` optionally stores the publisher URL.

### `ArticleTextResult`

Each extraction result contains:

- `url`: the URL used for extraction.
- `text`: extracted article text, or `None` if extraction failed.
- `status`: `success`, `fetch_failed`, or `extraction_failed`.
- `error`: an explanatory message when the operation failed.

### `URLResolutionResult`

Each URL-resolution result contains the original RSS URL, the resolved publisher URL when successful, a status, and an error message when resolution fails. Resolution failures are returned as results rather than raised for individual URLs.

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

Clone the repository and install development dependencies:

```bash
uv sync --extra dev
```

Run the test suite and static checks:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run python -m compileall -q src tests
```

An optional live run is available at `scripts/get_news.py`. It makes external network requests, so it is separate from the unit test suite:

```bash
uv run python scripts/get_news.py
```

## Important behavior and limitations

- Google News RSS is not a stable, officially documented search API; behavior and availability may change.
- Freshness operators are approximate; local date filtering is also applied when `hours` is specified.
- Publisher names in queries do not guarantee that all results originate from that publisher.
- Summary text and timestamps depend on the RSS entries returned by Google News.
- Article-text extraction attempts to download publisher pages, but some pages may not yield text because of network failures, page structure, paywalls, logins, or other access controls.
- URL resolution may fail for individual RSS entries; check `url_resolution_status` and `url_resolution_error` before relying on `resolved_url`.

## Documentation

- [Architecture](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [API reference](docs/api.md)

## License

MIT. See [LICENSE](LICENSE).
