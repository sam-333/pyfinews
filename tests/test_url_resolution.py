import pytest

from pyfinews import GoogleNewsURLResolver
from pyfinews import url_resolution as url_resolution_module

GOOGLE_NEWS_URL = "https://news.google.com/rss/articles/example"
PUBLISHER_URL = "https://publisher.example/story"


def test_resolver_returns_publisher_url(monkeypatch):
    calls = []

    def decode(url, **kwargs):
        calls.append((url, kwargs))
        return {"success": True, "decoded_url": PUBLISHER_URL}

    monkeypatch.setattr(url_resolution_module, "gnewsdecoder", decode)
    result = GoogleNewsURLResolver().resolve(GOOGLE_NEWS_URL)
    assert result.status == "success"
    assert result.rss_url == GOOGLE_NEWS_URL
    assert result.resolved_url == PUBLISHER_URL
    assert result.error is None
    assert calls == [(GOOGLE_NEWS_URL, {"interval": 1.0, "timeout": 15.0})]


def test_resolver_passes_custom_interval_and_timeout(monkeypatch):
    calls = []
    monkeypatch.setattr(
        url_resolution_module,
        "gnewsdecoder",
        lambda url, **kwargs: calls.append(kwargs) or {
            "success": True, "decoded_url": PUBLISHER_URL
        },
    )
    result = GoogleNewsURLResolver(interval=0.25, timeout=8).resolve(GOOGLE_NEWS_URL)
    assert result.status == "success"
    assert calls == [{"interval": 0.25, "timeout": 8.0}]


def test_resolver_supports_status_response(monkeypatch):
    monkeypatch.setattr(
        url_resolution_module, "gnewsdecoder",
        lambda *args, **kwargs: {"status": True, "decoded_url": PUBLISHER_URL},
    )
    result = GoogleNewsURLResolver().resolve(GOOGLE_NEWS_URL)
    assert result.status == "success"
    assert result.resolved_url == PUBLISHER_URL


def test_resolver_reports_decoder_failure_without_raising(monkeypatch):
    monkeypatch.setattr(
        url_resolution_module, "gnewsdecoder",
        lambda *args, **kwargs: {"success": False, "message": "could not decode"},
    )
    result = GoogleNewsURLResolver().resolve(GOOGLE_NEWS_URL)
    assert result.status == "resolution_failed"
    assert result.resolved_url is None
    assert result.error == "could not decode"


def test_resolver_reports_decoder_exception_without_raising(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("decoder network unavailable")

    monkeypatch.setattr(url_resolution_module, "gnewsdecoder", fail)
    result = GoogleNewsURLResolver().resolve(GOOGLE_NEWS_URL)
    assert result.status == "resolution_failed"
    assert result.resolved_url is None
    assert result.error == "decoder network unavailable"


@pytest.mark.parametrize("decoded", [None, "not a dict", [], 42])
def test_resolver_rejects_invalid_decoder_result(monkeypatch, decoded):
    monkeypatch.setattr(
        url_resolution_module, "gnewsdecoder", lambda *args, **kwargs: decoded
    )
    result = GoogleNewsURLResolver().resolve(GOOGLE_NEWS_URL)
    assert result.status == "resolution_failed"
    assert result.resolved_url is None
    assert result.error == "Decoder returned an invalid result"


def test_resolver_rejects_missing_decoded_url(monkeypatch):
    monkeypatch.setattr(
        url_resolution_module, "gnewsdecoder",
        lambda *args, **kwargs: {"success": True},
    )
    result = GoogleNewsURLResolver().resolve(GOOGLE_NEWS_URL)
    assert result.status == "resolution_failed"
    assert result.resolved_url is None
    assert result.error == "Could not resolve URL"


def test_resolver_rejects_invalid_decoded_url(monkeypatch):
    monkeypatch.setattr(
        url_resolution_module, "gnewsdecoder",
        lambda *args, **kwargs: {"success": True, "decoded_url": "file:///tmp/story.html"},
    )
    result = GoogleNewsURLResolver().resolve(GOOGLE_NEWS_URL)
    assert result.status == "resolution_failed"
    assert result.resolved_url is None
    assert result.error == "Decoder returned an invalid HTTP(S) URL"


def test_resolver_rejects_google_news_destination(monkeypatch):
    monkeypatch.setattr(
        url_resolution_module, "gnewsdecoder",
        lambda *args, **kwargs: {
            "success": True,
            "decoded_url": "https://news.google.com/rss/articles/still-google",
        },
    )
    result = GoogleNewsURLResolver().resolve(GOOGLE_NEWS_URL)
    assert result.status == "resolution_failed"
    assert result.resolved_url is None
    assert result.error == "Resolved URL still points to Google News"


@pytest.mark.parametrize("url", ["", "   ", None, 123])
def test_resolver_rejects_empty_or_non_string_input(url):
    with pytest.raises(ValueError, match="non-empty string"):
        GoogleNewsURLResolver().resolve(url)


@pytest.mark.parametrize(
    "url", ["file:///tmp/article", "ftp://example.com/article", "https:///missing-host", "not a url"]
)
def test_resolver_rejects_non_absolute_http_url(url):
    with pytest.raises(ValueError, match=r"absolute HTTP\(S\) URL"):
        GoogleNewsURLResolver().resolve(url)


@pytest.mark.parametrize("interval", [-1, True, "1"])
def test_resolver_rejects_invalid_interval(interval):
    with pytest.raises(ValueError, match="interval"):
        GoogleNewsURLResolver(interval=interval)


@pytest.mark.parametrize("timeout", [0, -1, True, "5"])
def test_resolver_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError, match="timeout"):
        GoogleNewsURLResolver(timeout=timeout)


def test_resolve_many_preserves_order_and_duplicates(monkeypatch):
    calls = []

    def decode(url, **kwargs):
        calls.append(url)
        return {"success": True, "decoded_url": f"https://publisher.example/{len(calls)}"}

    monkeypatch.setattr(url_resolution_module, "gnewsdecoder", decode)
    urls = [GOOGLE_NEWS_URL, GOOGLE_NEWS_URL, "https://news.google.com/rss/articles/other"]
    results = GoogleNewsURLResolver().resolve_many(urls)
    assert [result.rss_url for result in results] == urls
    assert [result.status for result in results] == ["success"] * 3
    assert calls == urls
