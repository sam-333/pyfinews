"""Google News RSS query representation."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

GOOGLE_NEWS_RSS_SEARCH_URL = "https://news.google.com/rss/search"


@dataclass(frozen=True, slots=True)
class GoogleNewsQuery:
    """A Google News RSS search query, without language/country configuration."""

    query: str

    def __post_init__(self) -> None:
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")

        object.__setattr__(self, "query", self.query.strip())

    def to_url(self) -> str:
        """Build a URL with safe query-string encoding."""
        return f"{GOOGLE_NEWS_RSS_SEARCH_URL}?{urlencode({'q': self.query})}"
