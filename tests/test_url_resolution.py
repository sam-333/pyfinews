from types import SimpleNamespace
import sys

import pytest

from pyfinews import GoogleNewsURLResolver


def test_resolver_returns_publisher_url(monkeypatch):
    calls = []
    fake_decoder = SimpleNamespace(
        gnewsdecoder=lambda url, **kwargs: calls.append((url, kwargs)) or {
            "success": True,
            "decoded_url": "https://publisher.example/story",
        }
    )
    monkeypatch.setitem(sys.modules, "googlenewsdecoder", fake_decoder)

    result = GoogleNewsURLResolver().resolve("https://news.google.com/rss/articles/example")

    assert result.status == "success"
    assert result.rss_url == "https://news.google.com/rss/articles/example"
    assert result.resolved_url == "https://publisher.example/story"
    assert calls[0][1] == {"interval": 1.0, "timeout": 15.0}


def test_resolver_supports_status_response(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "googlenewsdecoder",
        SimpleNamespace(gnewsdecoder=lambda *args, **kwargs: {
            "status": True,
            "decoded_url": "https://publisher.example/story",
        }),
    )
    result = GoogleNewsURLResolver().resolve("https://news.google.com/rss/articles/example")
    
    assert result.status == "success"


def test_resolver_reports_failure_without_raising(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "googlenewsdecoder",
        SimpleNamespace(gnewsdecoder=lambda *args, **kwargs: {
            "success": False,
            "message": "could not decode",
        }),
    )
    result = GoogleNewsURLResolver().resolve("https://news.google.com/rss/articles/example")
    
    assert result.status == "resolution_failed"
    assert result.resolved_url is None
    assert result.error == "could not decode"


def test_resolver_rejects_google_news_as_resolved_destination(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "googlenewsdecoder",
        SimpleNamespace(gnewsdecoder=lambda *args, **kwargs: {
            "success": True,
            "decoded_url": "https://news.google.com/rss/articles/still-google",
        }),
    )
    result = GoogleNewsURLResolver().resolve("https://news.google.com/rss/articles/example")
    
    assert result.status == "resolution_failed"
    assert "still points to Google News" in result.error


def test_resolver_rejects_invalid_input():
    with pytest.raises(ValueError, match=r"HTTP\(S\)"):
        GoogleNewsURLResolver().resolve("file:///tmp/article")


def test_resolver_rejects_invalid_timeout():
    with pytest.raises(ValueError, match="timeout"):
        GoogleNewsURLResolver(timeout=0)
