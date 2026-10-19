"""Article filtering helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from collections.abc import Iterable

from pyfinews.models import NewsArticle


def filter_by_lookback(
    articles: Iterable[NewsArticle], hours: float, *, now: datetime | None = None
) -> list[NewsArticle]:
    """Keep articles published between ``now - hours`` and ``now``.

    Articles without publication timestamps are excluded because their age cannot
    be established reliably.
    """
    if isinstance(hours, bool) or hours < 0:
        raise ValueError("hours must be non-negative")
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None or reference.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    reference = reference.astimezone(timezone.utc)
    cutoff = reference - timedelta(hours=hours)

    return [
        article for article in articles
        if article.published_at is not None and cutoff <= article.published_at <= reference
    ]
