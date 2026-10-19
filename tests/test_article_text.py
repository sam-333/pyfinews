import sys
from configparser import ConfigParser
from types import SimpleNamespace

import pytest

from pyfinews import ArticleTextExtractor, NewsArticle


def fake_trafilatura(*, fetch_url, extract):
    module = SimpleNamespace(fetch_url=fetch_url, extract=extract)
    settings = SimpleNamespace(use_config=ConfigParser)
    module.__path__ = []
    sys.modules["trafilatura.settings"] = settings
    return module


def test_extract_returns_main_text(monkeypatch):
    calls = []
    monkeypatch.setitem(sys.modules, "trafilatura", fake_trafilatura(
        fetch_url=lambda url, **kwargs: calls.append((url, kwargs)) or "<html>body</html>",
        extract=lambda html, **kwargs: "  Article body text  ",
    ))
    result = ArticleTextExtractor().extract(NewsArticle("Headline", "https://example.com/story"))
    assert calls[0][0] == "https://example.com/story"
    assert "config" in calls[0][1]
    assert result.url == "https://example.com/story"
    assert result.text == "Article body text"
    assert result.status == "success"
    assert result.error is None


def test_extract_reports_no_text(monkeypatch):
    monkeypatch.setitem(sys.modules, "trafilatura", fake_trafilatura(
        fetch_url=lambda *args, **kwargs: "<html></html>",
        extract=lambda *args, **kwargs: None,
    ))
    result = ArticleTextExtractor().extract("https://example.com/story")
    assert result.status == "extraction_failed"
    assert result.text is None


def test_extract_reports_fetch_failure(monkeypatch):
    monkeypatch.setitem(sys.modules, "trafilatura", fake_trafilatura(
        fetch_url=lambda *args, **kwargs: None,
        extract=lambda *args, **kwargs: "unused",
    ))
    result = ArticleTextExtractor().extract("https://example.com/story")
    assert result.status == "fetch_failed"
    assert result.error == "Download failed"


def test_extract_reports_fetch_exception(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("network unavailable")

    monkeypatch.setitem(sys.modules, "trafilatura", fake_trafilatura(
        fetch_url=fail,
        extract=lambda *args, **kwargs: "unused",
    ))
    result = ArticleTextExtractor().extract("https://example.com/story")
    assert result.status == "fetch_failed"
    assert result.error == "network unavailable"


def test_extract_prefers_resolved_url_for_news_article(monkeypatch):
    seen = []
    monkeypatch.setitem(sys.modules, "trafilatura", fake_trafilatura(
        fetch_url=lambda url, **kwargs: seen.append(url) or "<html>body</html>",
        extract=lambda html, **kwargs: "Article body text",
    ))
    article = NewsArticle(
        "Headline", "https://news.google.com/rss/articles/example",
        resolved_url="https://publisher.example/story",
    )
    result = ArticleTextExtractor().extract(article)
    assert seen == ["https://publisher.example/story"]
    assert result.url == "https://publisher.example/story"
    assert result.status == "success"


def test_extract_does_not_fetch_rss_url_after_explicit_resolution_failure(monkeypatch):
    from pyfinews import ArticleTextStatus

    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("Should not fetch the unresolved Google News URL")

    monkeypatch.setitem(sys.modules, "trafilatura", fake_trafilatura(
        fetch_url=unexpected_fetch,
        extract=lambda *args, **kwargs: "unused",
    ))
    article = NewsArticle(
        "Headline", "https://news.google.com/rss/articles/example",
        url_resolution_status="resolution_failed",
        url_resolution_error="decoder could not resolve URL",
    )
    result = ArticleTextExtractor().extract(article)
    assert result.status == ArticleTextStatus.FETCH_FAILED
    assert result.url == article.url
    assert result.error == "decoder could not resolve URL"


def test_extract_rejects_non_http_url():
    with pytest.raises(ValueError, match="http or https"):
        ArticleTextExtractor().extract("file:///tmp/story.html")


def test_invalid_timeout_rejected():
    with pytest.raises(ValueError, match="timeout"):
        ArticleTextExtractor(timeout=0)


def test_extract_many_preserves_order_and_duplicates(monkeypatch):
    extractor = ArticleTextExtractor()
    seen = []

    def fake_extract(article):
        seen.append(article)
        return SimpleNamespace(url=str(article), status="success", text="text", error=None)

    monkeypatch.setattr(extractor, "extract", fake_extract)
    inputs = ["https://example.com/a", "https://example.com/a", "https://example.com/b"]
    results = extractor.extract_many(inputs)
    assert seen == inputs
    assert len(results) == 3


def test_missing_trafilatura_has_helpful_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "trafilatura", None)
    with pytest.raises(ImportError, match="article-text"):
        ArticleTextExtractor().extract("https://example.com/story")
