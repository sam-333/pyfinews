# Configuration

`NewsClient` accepts optional `taxonomy` and `publishers` lists. If omitted, packaged JSON defaults are loaded.

## Taxonomy

A taxonomy file is a JSON list of domain objects. Each object identifies a domain and the terms used to search it. See `src/pyfinews/taxonomy/default_taxonomy.json` for the complete example and supported fields.

Important validation principles:

- Domain IDs must be unique.
- Each domain must contain a non-empty list of query terms.
- Disabled domains are ignored by query planning.

## Publishers

A publisher file is a JSON list of publisher objects. Entries use the following fields:

- `id`: stable unique identifier.
- `name`: publisher name used in publisher-targeted queries.
- `aliases`: optional metadata aliases.
- `regions`: optional metadata labels; currently not used for query selection.
- `enabled`: whether the publisher participates in query planning.
- `priority`: integer priority; lower values are considered first.

Publisher IDs must be unique. Enabled publishers are sorted by `(priority, id)` for deterministic planning. A smaller `query_limit` may mean lower-priority publishers or some domains are not reached.

## Loading custom files

```python
from pyfinews import load_publishers, load_taxonomy

taxonomy = load_taxonomy("config/taxonomy.json")
publishers = load_publishers("config/publishers.json")
```

You can pass the loaded lists directly to the client:

```python
from pyfinews import NewsClient

client = NewsClient(taxonomy=taxonomy, publishers=publishers)
```
