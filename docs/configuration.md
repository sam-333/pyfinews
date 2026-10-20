# Configuration

`NewsClient` accepts optional taxonomy and publisher records. If either argument is omitted, the corresponding packaged JSON defaults are loaded. You can use the defaults or load your own JSON files and pass the resulting records to the client.

## Client-level settings

```python
from pyfinews import NewsClient

client = NewsClient(
    timeout=10.0,
    taxonomy=None,
    publishers=None,
    query_limit=30,
    article_timeout=15.0,
)
```

- `timeout`: timeout in seconds for Google News RSS requests.
- `taxonomy`: custom taxonomy records, or `None` to use packaged defaults.
- `publishers`: custom publisher records, or `None` to use packaged defaults.
- `query_limit`: maximum number of planned queries to execute.
- `article_timeout`: timeout in seconds for publisher-page requests during article-text extraction.
- `provider`: optionally inject a custom RSS provider.
- `url_resolver`: optionally inject a custom URL resolver.

Client construction loads local configuration but does not itself make network requests.

## Taxonomy

A taxonomy file is a JSON list of domain objects. Each object identifies a domain and the terms used to search it. See `src/pyfinews/taxonomy/default_taxonomy.json` for the packaged example and supported fields.

Validation principles:

- Domain IDs must be unique.
- Each domain must contain a non-empty list of query terms.
- Disabled domains are ignored by query planning.

Load a custom taxonomy file:

```python
from pyfinews import load_taxonomy

taxonomy = load_taxonomy("config/taxonomy.json")
```

## Publishers

A publisher file is a JSON list of publisher objects. Entries use the following fields:

- `id`: stable unique identifier.
- `name`: publisher name used in publisher-targeted queries.
- `aliases`: optional metadata aliases.
- `regions`: optional metadata labels; currently not used for query selection.
- `enabled`: whether the publisher participates in query planning.
- `priority`: integer priority; lower values are considered first.

Publisher IDs must be unique. Enabled publishers are sorted by `(priority, id)` for deterministic planning. A smaller `query_limit` may mean lower-priority publishers or some domains are not reached.

Load a custom publisher file:

```python
from pyfinews import load_publishers

publishers = load_publishers("config/publishers.json")
```

## Pass custom configuration to the client

```python
from pyfinews import NewsClient, load_publishers, load_taxonomy

taxonomy = load_taxonomy("config/taxonomy.json")
publishers = load_publishers("config/publishers.json")

with NewsClient(taxonomy=taxonomy, publishers=publishers) as client:
    articles = client.get(topic="equities")
```

## HTTP timeouts and User-Agent

The RSS provider and article-text extractor use separate timeout settings:

- `timeout` configures Google News RSS requests.
- `article_timeout` configures publisher-page requests for article-text extraction.

The default HTTP User-Agent is generated centrally as `pyfinews/<installed-version>` in `pyfinews._version`. This keeps it aligned with the installed package version rather than hardcoding a release number. The relevant provider and extractor constructors accept a `user_agent` argument for explicit overrides.

For example, when constructing a provider directly:

```python
from pyfinews import GoogleNewsRSSProvider

provider = GoogleNewsRSSProvider(
    timeout=10.0,
    user_agent="my-application/1.0",
)
```

For article-text extraction:

```python
from pyfinews import ArticleTextExtractor

extractor = ArticleTextExtractor(
    timeout=15.0,
    user_agent="my-application/1.0",
)
```

The constructor signatures in the installed release are authoritative.

## Query-specific controls

```python
articles = client.get(
    topic="equities",
    hours=24,
    max_articles=20,
    query_limit=10,
    resolve_urls=True,
)
```

- `hours` controls the freshness window. Use `None` to disable freshness operators and local lookback filtering.
- `max_articles` caps returned articles. Use `None` to disable the client-side cap.
- `query_limit` overrides the client-level query budget for this call.
- `resolve_urls=True` resolves Google News RSS URLs to publisher URLs after discovery.

For a single arbitrary query, use `client.search(query, ...)`, which supports `hours`, `max_articles`, and `resolve_urls`.

## Configuration boundaries

Taxonomy and publisher JSON files affect query planning; they do not configure article extraction or URL resolution. Those behaviors are controlled through `NewsClient` and the relevant provider/extractor constructor arguments. Versioning does not require a separate configuration file: version access and the default User-Agent are derived from installed package metadata.
