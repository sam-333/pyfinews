from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from pyfinews import GoogleNewsQuery, GoogleNewsRSSProvider, NewsFetchError, NewsParseError

RSS = b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Google News</title>
<item><title>Apple earnings beat estimates</title><link>https://example.com/apple</link>
<pubDate>Sat, 17 Oct 2026 01:00:00 GMT</pubDate><source>Example Finance</source>
<description>Results summary</description></item>
<item><title>Old market story</title><link>https://example.com/old</link>
<pubDate>Mon, 05 Oct 2026 12:00:00 GMT</pubDate></item>
</channel></rss>'''


class FakeResponse:
    status = 200
    def __init__(self, payload=RSS): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.payload


def test_provider_parses_and_normalizes_article():
    provider = GoogleNewsRSSProvider()
    
    with patch("pyfinews.providers.google_news.urlopen", return_value=FakeResponse()):
        articles = provider.search(GoogleNewsQuery("AAPL"), lookback_hours=None)
    
    assert len(articles) == 2
    assert articles[0].title == "Apple earnings beat estimates"
    assert articles[0].source == "Example Finance"
    assert articles[0].published_at == datetime(2026, 10, 17, 1, tzinfo=timezone.utc)
    assert articles[0].query == "AAPL"


def test_invalid_xml_raises_parse_error():
    with patch("pyfinews.providers.google_news.urlopen", return_value=FakeResponse(b"<rss>")):
        with pytest.raises(NewsParseError):
            GoogleNewsRSSProvider().search(GoogleNewsQuery("AAPL"), lookback_hours=None)


def test_missing_channel_raises_parse_error():
    with patch("pyfinews.providers.google_news.urlopen", return_value=FakeResponse(b"<rss/>")):
        with pytest.raises(NewsParseError, match="channel"):
            GoogleNewsRSSProvider().search(GoogleNewsQuery("AAPL"), lookback_hours=None)


def test_valid_empty_rss_feed_returns_no_articles():
    empty_feed = b"<rss version='2.0'><channel><title>Google News</title></channel></rss>"
    
    with patch("pyfinews.providers.google_news.urlopen", return_value=FakeResponse(empty_feed)):
        articles = GoogleNewsRSSProvider().search(GoogleNewsQuery("AAPL"), lookback_hours=None)
    
    assert articles == []


def test_transport_error_is_wrapped():
    from urllib.error import URLError

    with patch("pyfinews.providers.google_news.urlopen", side_effect=URLError("offline")):
        with pytest.raises(NewsFetchError):
            GoogleNewsRSSProvider().search(GoogleNewsQuery("AAPL"), lookback_hours=None)


def test_freshness_operator_windows():
    from pyfinews.providers.google_news import _query_with_freshness

    assert _query_with_freshness("AAPL", 1) == "AAPL when:1h"
    assert _query_with_freshness("AAPL", 24) == "AAPL when:24h"
    assert _query_with_freshness("AAPL", 72) == "AAPL when:7d"
    assert _query_with_freshness("AAPL", None) == "AAPL"
