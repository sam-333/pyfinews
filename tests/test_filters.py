from datetime import datetime, timedelta, timezone
import pytest

from pyfinews import NewsArticle, filter_by_lookback


def test_filter_by_lookback_keeps_recent_timestamped_articles():
    now = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
    recent = NewsArticle(
        "Recent", "https://example.com/recent", 
        published_at=now - timedelta(hours=2)
    )
    old = NewsArticle(
        "Old", "https://example.com/old", 
        published_at=now - timedelta(hours=30)
    )
    unknown = NewsArticle("Unknown", "https://example.com/unknown")

    assert filter_by_lookback([recent, old, unknown], 24, now=now) == [recent]


def test_filter_rejects_naive_now():
    with pytest.raises(ValueError, match="timezone-aware"):
        filter_by_lookback([], 24, now=datetime(2026, 1, 1))
