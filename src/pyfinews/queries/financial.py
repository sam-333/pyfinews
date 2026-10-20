"""Deterministic financial-news query planning using taxonomy and publisher metadata."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pyfinews.queries.google_news import GoogleNewsQuery


class FinancialQueryBuilder:
    """Build query plans bounded by a maximum RSS-request budget.

    Market queries are ordered by publisher priority (ascending numeric value).
    For each publisher, every enabled domain is queried before moving to the next
    publisher. Broad domain-only queries follow publisher-targeted combinations.
    This makes a small query budget favor high-priority publishers while retaining
    broad discovery when the budget is large enough.
    """

    def __init__(
        self,
        domains: Sequence[Mapping[str, Any]],
        publishers: Sequence[Mapping[str, Any]],
        *,
        query_limit: int = 30,
    ) -> None:
        self._validate_query_limit(query_limit)
        self.query_limit = query_limit
        self._domains = tuple(
            dict(domain) for domain in domains if domain.get("enabled", True)
        )
        enabled_publishers = [
            dict(publisher) for publisher in publishers if publisher.get("enabled", True)
        ]

        for index, publisher in enumerate(enabled_publishers):
            priority = publisher.get("priority", 1)

            if isinstance(priority, bool) or not isinstance(priority, int):
                raise TypeError(f"publishers[{index}].priority must be an integer")

        self._publishers = tuple(
            sorted(
                enabled_publishers,
                key=lambda publisher: (publisher.get("priority", 1), publisher.get("id", "")),
            )
        )
        self._validate_domains()
        self._validate_publishers()

    def build_market_queries(
        self, 
        *, 
        query_limit: int | None = None
    ) -> list[GoogleNewsQuery]:
        """Build market-wide queries, prioritizing publishers before broad queries."""
        budget = self._resolve_query_limit(query_limit)

        if not self._domains:
            raise ValueError("At least one enabled financial domain is required")
        if not self._publishers:
            raise ValueError("At least one enabled publisher is required")

        candidates: list[GoogleNewsQuery] = []
        for publisher in self._publishers:
            for domain in self._domains:
                terms_query = _terms_or_query(domain["query_terms"])
                candidates.append(
                    GoogleNewsQuery(f'({terms_query}) "{publisher["name"]}"')
                )

        return _unique_queries(candidates)[:budget]

    def build_topic_queries(
        self, topic: str, 
        *, 
        query_limit: int | None = None
    ) -> list[GoogleNewsQuery]:
        """Build a topic query followed by publisher-targeted variants by priority."""
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("topic must be a non-empty string")

        budget = self._resolve_query_limit(query_limit)
        normalized_topic = topic.strip()
        candidates = [
            GoogleNewsQuery(f'({normalized_topic}) "{publisher["name"]}"')
            for publisher in self._publishers
        ]

        return _unique_queries(candidates)[:budget]

    def _resolve_query_limit(self, query_limit: int | None) -> int:
        budget = self.query_limit if query_limit is None else query_limit
        self._validate_query_limit(budget)

        return budget

    @staticmethod
    def _validate_query_limit(query_limit: int) -> None:
        if isinstance(query_limit, bool) or not isinstance(query_limit, int) or query_limit < 1:
            raise ValueError("query_limit must be a positive integer")

    def _validate_domains(self) -> None:
        seen: set[str] = set()
        for index, domain in enumerate(self._domains):
            domain_id = domain.get("id")
            terms = domain.get("query_terms")

            if not isinstance(domain_id, str) or not domain_id.strip():
                raise ValueError(f"domains[{index}].id must be a non-empty string")
            if domain_id in seen:
                raise ValueError(f"Duplicate domain id: {domain_id!r}")

            if not isinstance(terms, list) or not terms or any(
                not isinstance(term, str) or not term.strip() for term in terms
            ):
                raise ValueError(f"domains[{index}].query_terms must be a non-empty string list")

            seen.add(domain_id)
            domain["query_terms"] = [term.strip() for term in terms]

    def _validate_publishers(self) -> None:
        seen: set[str] = set()
        for index, publisher in enumerate(self._publishers):
            publisher_id = publisher.get("id")
            name = publisher.get("name")
            priority = publisher.get("priority", 1)

            if not isinstance(publisher_id, str) or not publisher_id.strip():
                raise ValueError(f"publishers[{index}].id must be a non-empty string")
            if publisher_id in seen:
                raise ValueError(f"Duplicate publisher id: {publisher_id!r}")

            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"publishers[{index}].name must be a non-empty string")
            if isinstance(priority, bool) or not isinstance(priority, int):
                raise TypeError(f"publishers[{index}].priority must be an integer")

            seen.add(publisher_id)
            publisher["name"] = name.strip()
            publisher["priority"] = priority


def _terms_or_query(terms: Sequence[str]) -> str:
    """Combine domain terms into one OR query, quoting each phrase safely."""
    quoted = []
    for term in terms:
        escaped = term.replace("\\", "\\\\").replace('"', '\\"')
        quoted.append(f'"{escaped}"')

    return " OR ".join(quoted)


def _unique_queries(queries: Sequence[GoogleNewsQuery]) -> list[GoogleNewsQuery]:
    result: list[GoogleNewsQuery] = []
    seen: set[str] = set()

    for query in queries:
        key = query.query.casefold()

        if key not in seen:
            seen.add(key)
            result.append(query)

    return result
