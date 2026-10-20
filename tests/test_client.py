from datetime import UTC, datetime

import pytest

from pyfinews import NewsArticle, NewsClient


class FakeProvider:
    def __init__(self, articles):
        self.articles = articles
        self.queries = []

    def search(self, query, *, lookback_hours=24, max_articles=20):
        self.queries.append(query.query)
        
        return self.articles if max_articles is None else self.articles[:max_articles]


def test_search_wraps_custom_query_and_deduplicates_by_title():
    article = NewsArticle("Headline", "https://example.com/story", published_at=datetime.now(UTC))
    provider = FakeProvider([article, article])
    client = NewsClient(provider=provider)
    result = client.search("AAPL", hours=None)

    assert result == [article]
    assert provider.queries == ["AAPL"]


def test_get_uses_query_limit_and_priority_ordering():
    now = datetime.now(UTC)
    article = NewsArticle("Headline", "https://example.com/story", published_at=now)
    provider = FakeProvider([article])
    domains = [{"id": "macro", "name": "Macro", "query_terms": ["inflation"]}]
    publishers = [
        {"id": "b", "name": "B Outlet", "priority": 2},
        {"id": "a", "name": "A Outlet", "priority": 1},
    ]
    client = NewsClient(provider=provider, taxonomy=domains, publishers=publishers, query_limit=2)
    result = client.get(hours=None, max_articles=5)

    assert result == [article]
    assert len(provider.queries) == 2
    assert provider.queries[0].endswith('"A Outlet"')
    assert provider.queries[1].endswith('"B Outlet"')


def test_per_call_query_limit_overrides_default():
    provider = FakeProvider([])
    domains = [{"id": "macro", "name": "Macro", "query_terms": ["inflation"]}]
    publishers = [{"id": "r", "name": "Reuters", "priority": 1}]
    client = NewsClient(provider=provider, taxonomy=domains, publishers=publishers, query_limit=10)
    client.get(hours=None, query_limit=1)
    assert len(provider.queries) == 1


def test_invalid_hours_rejected():
    client = NewsClient(provider=FakeProvider([]))
    with pytest.raises(ValueError, match="hours"):
        client.get(hours=-1)


def test_invalid_query_limit_rejected():
    client = NewsClient(provider=FakeProvider([]))
    with pytest.raises(ValueError, match="query_limit"):
        client.get(query_limit=0)


def test_search_can_resolve_urls_opt_in():
    from pyfinews import URLResolutionResult

    article = NewsArticle("Headline", "https://news.google.com/rss/articles/example")
    provider = FakeProvider([article])

    class FakeResolver:
        def resolve(self, url):
            assert url == article.url
            return URLResolutionResult(
                rss_url=url,
                resolved_url="https://publisher.example/story",
                status="success",
            )

    client = NewsClient(provider=provider, url_resolver=FakeResolver())
    result = client.search("example", hours=None, resolve_urls=True)

    assert result[0].url == article.url
    assert result[0].resolved_url == "https://publisher.example/story"
    assert result[0].url_resolution_status == "success"


def test_resolution_failure_keeps_article():
    from pyfinews import URLResolutionResult

    article = NewsArticle("Headline", "https://news.google.com/rss/articles/example")

    class FakeResolver:
        def resolve(self, url):
            return URLResolutionResult(url, None, "resolution_failed", "not decodable")

    client = NewsClient(provider=FakeProvider([article]), url_resolver=FakeResolver())
    result = client.resolve_article_urls([article])

    assert len(result) == 1
    assert result[0].url == article.url
    assert result[0].resolved_url is None
    assert result[0].url_resolution_status == "resolution_failed"
    assert result[0].url_resolution_error == "not decodable"


def test_search_accepts_none_max_articles():
    articles = [NewsArticle("One", "https://example.com/1"), NewsArticle("Two", "https://example.com/2")]
    provider = FakeProvider(articles)
    client = NewsClient(provider=provider)
    assert client.search("example", hours=None, max_articles=None) == articles


def test_get_accepts_none_max_articles():
    articles = [NewsArticle("One", "https://example.com/1"), NewsArticle("Two", "https://example.com/2")]
    provider = FakeProvider(articles)
    domains = [{"id": "macro", "name": "Macro", "query_terms": ["inflation"]}]
    publishers = [{"id": "r", "name": "Reuters", "priority": 1}]
    client = NewsClient(provider=provider, taxonomy=domains, publishers=publishers, query_limit=1)
    result = client.get(hours=None, max_articles=None)

    assert result == articles


def test_get_extract_text_attaches_text_and_status(monkeypatch):
    from pyfinews import ArticleTextResult, ArticleTextStatus

    article = NewsArticle("Headline", "https://example.com/story")
    provider = FakeProvider([article])
    domains = [{"id": "macro", "name": "Macro", "query_terms": ["inflation"]}]
    publishers = [{"id": "r", "name": "Reuters", "priority": 1}]
    client = NewsClient(provider=provider, taxonomy=domains, publishers=publishers, query_limit=1)
    monkeypatch.setattr(
        client,
        "extract_articles_text",
        lambda articles, **kwargs: [ArticleTextResult(
            url=articles[0].url,
            text="Extracted article body",
            status=ArticleTextStatus.SUCCESS,
        )],
    )

    result = client.get(hours=None, extract_text=True)

    assert len(result) == 1
    assert result[0].text == "Extracted article body"
    assert result[0].text_extraction_status == ArticleTextStatus.SUCCESS


def test_get_extract_text_can_resolve_urls_first(monkeypatch):
    from pyfinews import ArticleTextResult, ArticleTextStatus, URLResolutionResult

    article = NewsArticle("Headline", "https://news.google.com/rss/articles/example")
    provider = FakeProvider([article])
    domains = [{"id": "macro", "name": "Macro", "query_terms": ["inflation"]}]
    publishers = [{"id": "r", "name": "Reuters", "priority": 1}]

    class FakeResolver:
        def resolve(self, url):
            return URLResolutionResult(url, "https://publisher.example/story", "success")

    client = NewsClient(
        provider=provider,
        taxonomy=domains,
        publishers=publishers,
        query_limit=1,
        url_resolver=FakeResolver(),
    )
    seen = []

    def fake_extract(articles, **kwargs):
        seen.extend(articles)
        return [ArticleTextResult(
            url=articles[0].resolved_url,
            text="Publisher body",
            status=ArticleTextStatus.SUCCESS,
        )]

    monkeypatch.setattr(client, "extract_articles_text", fake_extract)
    result = client.get(hours=None, resolve_urls=True, extract_text=True)

    assert seen[0].resolved_url == "https://publisher.example/story"
    assert result[0].url == article.url
    assert result[0].resolved_url == "https://publisher.example/story"
    assert result[0].text == "Publisher body"
