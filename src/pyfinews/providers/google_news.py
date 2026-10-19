"""Google News RSS transport and parsing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from time import struct_time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import feedparser

from pyfinews.exceptions import NewsFetchError, NewsParseError
from pyfinews.models import NewsArticle
from pyfinews.queries.google_news import GoogleNewsQuery

logger = logging.getLogger(__name__)


class GoogleNewsRSSProvider:
    """Fetch Google News RSS search results and normalize them with feedparser."""

    def __init__(self, *, timeout: float = 10.0, user_agent: str = "pyfinews/0.1.0") -> None:
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.timeout = float(timeout)
        self.user_agent = user_agent

    def search(
        self, 
        query: GoogleNewsQuery, 
        *, 
        lookback_hours: float | None = 24, 
        max_articles: int | None = 20
    ) -> list[NewsArticle]:
        if not isinstance(query, GoogleNewsQuery):
            raise TypeError("query must be a GoogleNewsQuery")

        if lookback_hours is not None and (
            isinstance(lookback_hours, bool)
            or not isinstance(lookback_hours, (int, float))
            or lookback_hours < 0
        ):
            raise ValueError("lookback_hours must be non-negative or None")

        if max_articles is not None and (
            isinstance(max_articles, bool)
            or not isinstance(max_articles, int)
            or max_articles < 1
        ):
            raise ValueError("max_articles must be a positive integer or None")

        effective_query = _query_with_freshness(query.query, lookback_hours)
        rss_query = GoogleNewsQuery(effective_query)
        request = Request(
            rss_query.to_url(),
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
        )
        retrieved_at = datetime.now(timezone.utc)

        try:
            with urlopen(request, timeout=self.timeout) as response:
                status = getattr(response, "status", 200)
                if status < 200 or status >= 300:
                    raise NewsFetchError(f"Google News RSS returned HTTP {status}")
                
                payload = response.read()
        except HTTPError as exc:
            raise NewsFetchError(f"Google News RSS returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            logger.warning("Google News RSS request failed: %s", exc)
            raise NewsFetchError("Could not retrieve Google News RSS feed") from exc

        feed = feedparser.parse(payload)
        if getattr(feed, "bozo", False):
            parse_error = getattr(feed, "bozo_exception", None)
            # Recoverable feeds may contain useful entries despite a parser warning.
            if not getattr(feed, "entries", []):
                raise NewsParseError("Google News returned invalid RSS/XML") from parse_error
            logger.warning("Google News RSS feed contained a parsing issue: %s", parse_error)
        if not getattr(feed, "version", ""):
            raise NewsParseError("Google News response is not a recognized RSS/Atom feed")
        feed_metadata = getattr(feed, "feed", {})
        if not feed.entries and not (feed_metadata.get("title") or feed_metadata.get("link")):
            raise NewsParseError("RSS response has no channel metadata")

        cutoff = (
            retrieved_at - timedelta(hours=lookback_hours)
            if lookback_hours is not None
            else None
        )
        
        articles: list[NewsArticle] = []
        for entry in feed.entries:
            title = _clean_text(entry.get("title"))
            url = _clean_text(entry.get("link"))

            if not title or not url:
                continue

            published_at = _parse_datetime(entry.get("published_parsed"))
            if published_at is None:
                published_at = _parse_datetime(entry.get("updated_parsed"))
            if cutoff is not None and published_at is not None and published_at < cutoff:
                continue

            source_data = entry.get("source") or {}
            source = _clean_text(source_data.get("title")) or None
            summary = _clean_text(entry.get("summary")) or None
            articles.append(
                NewsArticle(
                    title=title,
                    url=url,
                    source=source,
                    published_at=published_at,
                    retrieved_at=retrieved_at,
                    summary=summary,
                    query=query.query,
                )
            )

        articles.sort(
            key=lambda article: article.published_at
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        return articles if max_articles is None else articles[:max_articles]


def _clean_text(value: object) -> str:
    """Return trimmed text for string-valued feed fields, otherwise an empty string."""
    return value.strip() if isinstance(value, str) else ""


def _parse_datetime(value: struct_time | tuple | None) -> datetime | None:
    """Convert feedparser's parsed date tuple to a timezone-aware UTC datetime."""
    if value is None:
        return None
    try:
        return datetime(*value[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def _query_with_freshness(
    query: str, 
    lookback_hours: float | None
) -> str:
    """Add an approximate Google News freshness operator and filter dates locally too."""
    if lookback_hours is None:
        return query
    if lookback_hours <= 1:
        operator = "when:1h"
    elif lookback_hours <= 24:
        operator = "when:24h"
    elif lookback_hours <= 24 * 7:
        operator = "when:7d"
    elif lookback_hours <= 24 * 30:
        operator = "when:30d"
    else:
        return query

    return f"{query} {operator}"
