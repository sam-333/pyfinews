import pytest

from pyfinews import ArticleTextExtractor, ArticleTextStatus, NewsArticle
from pyfinews import article_text as article_text_module


@pytest.fixture
def trafilatura_mocks(monkeypatch):
    calls = {"fetch": [], "extract": []}

    def fetch_url(url, **kwargs):
        calls["fetch"].append((url, kwargs))

        return "<html><body>Article</body></html>"

    def extract(html, **kwargs):
        calls["extract"].append((html, kwargs))

        return "Article body text"

    monkeypatch.setattr(article_text_module.trafilatura, "fetch_url", fetch_url)
    monkeypatch.setattr(article_text_module.trafilatura, "extract", extract)

    return calls


def test_extract_returns_main_text_and_passes_config(monkeypatch, trafilatura_mocks):
    from configparser import ConfigParser

    import trafilatura.settings

    configs = []

    def use_config():
        config = ConfigParser()
        configs.append(config)
        return config

    monkeypatch.setattr(trafilatura.settings, "use_config", use_config)
    result = ArticleTextExtractor(timeout=9, user_agent="test-agent").extract(
        "https://example.com/story"
    )

    assert result.url == "https://example.com/story"
    assert result.text == "Article body text"
    assert result.status == ArticleTextStatus.SUCCESS
    assert result.error is None
    assert trafilatura_mocks["fetch"][0][0] == "https://example.com/story"
    assert configs[0].get("DEFAULT", "DOWNLOAD_TIMEOUT") == "9"
    assert configs[0].get("DEFAULT", "USER_AGENTS") == "test-agent"
    assert trafilatura_mocks["extract"] == [
        ("<html><body>Article</body></html>", {
            "url": "https://example.com/story", "include_comments": False
        })
    ]


@pytest.mark.parametrize("empty_text", [None, "", "   ", 123])
def test_extract_reports_no_text(monkeypatch, trafilatura_mocks, empty_text):
    monkeypatch.setattr(
        article_text_module.trafilatura, "extract", lambda *args, **kwargs: empty_text
    )
    result = ArticleTextExtractor().extract("https://example.com/story")
    assert result.status == ArticleTextStatus.EXTRACTION_FAILED
    assert result.text is None
    assert result.error == "No main article text found"


def test_extract_reports_download_failure(monkeypatch, trafilatura_mocks):
    monkeypatch.setattr(
        article_text_module.trafilatura, "fetch_url", lambda *args, **kwargs: None
    )
    result = ArticleTextExtractor().extract("https://example.com/story")
    assert result.status == ArticleTextStatus.FETCH_FAILED
    assert result.text is None
    assert result.error == "Download failed"


def test_extract_reports_fetch_exception(monkeypatch, trafilatura_mocks):
    def fail(*args, **kwargs):
        raise OSError("network unavailable")

    monkeypatch.setattr(article_text_module.trafilatura, "fetch_url", fail)
    result = ArticleTextExtractor().extract("https://example.com/story")
    assert result.status == ArticleTextStatus.FETCH_FAILED
    assert result.text is None
    assert result.error == "network unavailable"


def test_extract_reports_extraction_exception(monkeypatch, trafilatura_mocks):
    def fail(*args, **kwargs):
        raise RuntimeError("extractor crashed")

    monkeypatch.setattr(article_text_module.trafilatura, "extract", fail)
    result = ArticleTextExtractor().extract("https://example.com/story")
    assert result.status == ArticleTextStatus.EXTRACTION_FAILED
    assert result.text is None
    assert result.error == "extractor crashed"


def test_extract_prefers_resolved_url_for_news_article(trafilatura_mocks):
    article = NewsArticle(
        "Headline", "https://news.google.com/rss/articles/example",
        resolved_url="https://publisher.example/story",
    )
    result = ArticleTextExtractor().extract(article)
    assert [url for url, _ in trafilatura_mocks["fetch"]] == [
        "https://publisher.example/story"
    ]
    assert result.url == "https://publisher.example/story"
    assert result.status == ArticleTextStatus.SUCCESS


def test_extract_does_not_fetch_after_resolution_failure(trafilatura_mocks):
    article = NewsArticle(
        "Headline", "https://news.google.com/rss/articles/example",
        url_resolution_status="resolution_failed",
        url_resolution_error="decoder could not resolve URL",
    )
    result = ArticleTextExtractor().extract(article)
    assert result.status == ArticleTextStatus.FETCH_FAILED
    assert result.url == article.url
    assert result.text is None
    assert result.error == "decoder could not resolve URL"
    assert trafilatura_mocks["fetch"] == []


@pytest.mark.parametrize("url", ["", "   ", None, 123])
def test_extract_rejects_empty_or_non_string_url(url):
    with pytest.raises(ValueError, match="non-empty URL"):
        ArticleTextExtractor().extract(url)


@pytest.mark.parametrize("url", ["file:///tmp/story.html", "ftp://example.com/story"])
def test_extract_rejects_non_http_url(url):
    with pytest.raises(ValueError, match="http or https"):
        ArticleTextExtractor().extract(url)


@pytest.mark.parametrize("timeout", [0, -1, True, "5"])
def test_invalid_timeout_rejected(timeout):
    with pytest.raises(ValueError, match="timeout"):
        ArticleTextExtractor(timeout=timeout)


def test_extract_many_preserves_order_and_duplicates(monkeypatch):
    extractor = ArticleTextExtractor()
    seen = []

    def fake_extract(article):
        seen.append(article)
        return article

    monkeypatch.setattr(extractor, "extract", fake_extract)
    inputs = ["https://example.com/a", "https://example.com/a", "https://example.com/b"]
    results = extractor.extract_many(inputs)
    assert seen == inputs
    assert results == inputs
