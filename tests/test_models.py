from datetime import datetime, timezone

import pytest

from pyfinews import ArticleTextStatus, NewsArticle


def test_article_normalizes_timestamps_to_utc():
    article = NewsArticle(
        " Headline ", " https://example.com/story ",
        published_at=datetime(2026, 10, 17, 10, tzinfo=timezone.utc),
    )

    assert article.title == "Headline"
    assert article.url == "https://example.com/story"
    assert article.published_at.tzinfo is timezone.utc


def test_article_rejects_empty_title():
    with pytest.raises(ValueError, match="title"):
        NewsArticle("  ", "https://example.com")


def test_article_rejects_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        NewsArticle("Headline", "https://example.com", published_at=datetime(2026, 1, 1))


def test_resolved_url_is_optional_and_validated():
    article = NewsArticle(
        "Headline", "https://news.google.com/rss/articles/example",
        resolved_url=" https://publisher.example/story ",
    )
    assert article.url == "https://news.google.com/rss/articles/example"
    assert article.resolved_url == "https://publisher.example/story"

    with pytest.raises(ValueError, match="resolved_url"):
        NewsArticle("Headline", "https://news.google.com/rss/articles/example", resolved_url=" ")


def test_third_positional_argument_remains_source_for_compatibility():
    article = NewsArticle("Headline", "https://example.com/story", "Example News")
    
    assert article.source == "Example News"
    assert article.resolved_url is None


def test_article_text_status_is_a_public_enum():
    assert ArticleTextStatus.SUCCESS == "success"
    assert ArticleTextStatus.FETCH_FAILED == "fetch_failed"
    assert ArticleTextStatus.EXTRACTION_FAILED == "extraction_failed"


def test_url_resolution_metadata_is_validated():
    article = NewsArticle(
        "Headline", "https://news.google.com/rss/articles/example",
        url_resolution_status="resolution_failed", url_resolution_error="decoder error",
    )

    assert article.url_resolution_status == "resolution_failed"
    assert article.url_resolution_error == "decoder error"

    with pytest.raises(ValueError, match="url_resolution_status"):
        NewsArticle("Headline", "https://example.com", url_resolution_status="unknown")


def test_news_article_supports_url_resolution_fields():
    from pyfinews import NewsArticle

    article = NewsArticle(
        "Headline",
        "https://news.google.com/rss/articles/example",
        resolved_url="https://publisher.example/story",
        url_resolution_status="success",
        url_resolution_error=None,
    )

    assert article.resolved_url == "https://publisher.example/story"
    assert article.url_resolution_status == "success"
    assert article.url_resolution_error is None
