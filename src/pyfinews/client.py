"""High-level client for financial news discovery."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, Self

from pyfinews.article_text import ArticleTextExtractor, ArticleTextResult
from pyfinews.deduplication import deduplicate_articles
from pyfinews.exceptions import NewsFetchError, NewsParseError, PyfinewsError
from pyfinews.filters import filter_by_lookback
from pyfinews.models import NewsArticle
from pyfinews.progress import run_with_progress
from pyfinews.providers.google_news import GoogleNewsRSSProvider
from pyfinews.publishers.loader import load_publishers
from pyfinews.queries.financial import FinancialQueryBuilder
from pyfinews.queries.google_news import GoogleNewsQuery
from pyfinews.taxonomy.loader import load_taxonomy
from pyfinews.url_resolution import GoogleNewsURLResolver


class NewsClient:
    """Discover financial news via Google News RSS.

    ``get`` provides market-wide or topic-specific discovery. Network calls only
    occur when ``get`` or ``search`` is called; use the context manager to make
    provider lifetime explicit (the default provider has no persistent connection).
    """

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        provider: GoogleNewsRSSProvider | None = None,
        taxonomy: list[dict[str, Any]] | None = None,
        publishers: list[dict[str, Any]] | None = None,
        query_limit: int = 30,
        article_timeout: float = 15.0,
        url_resolver: GoogleNewsURLResolver | None = None,
    ) -> None:
        self._provider = provider or GoogleNewsRSSProvider(timeout=timeout)
        self._taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
        self._publishers = publishers if publishers is not None else load_publishers()
        self._query_builder = FinancialQueryBuilder(
            self._taxonomy, self._publishers, query_limit=query_limit
        )
        self._query_limit = query_limit
        self._article_text_extractor = ArticleTextExtractor(timeout=article_timeout)
        self._url_resolver = url_resolver or GoogleNewsURLResolver()

    def search(
        self, query: str, *, hours: float | None = 24, max_articles: int | None = 20,
        resolve_urls: bool = False,
        show_progress: bool = True,
    ) -> list[NewsArticle]:
        """Search Google News; optionally resolve URLs with progress updates."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

        if max_articles is not None and (
            isinstance(max_articles, bool)
            or not isinstance(max_articles, int)
            or max_articles < 1
        ):
            raise ValueError("max_articles must be a positive integer or None")
        
        # Retrieve the feed candidates first; deduplication must precede the public cap.
        articles = self._provider.search(
            GoogleNewsQuery(query), lookback_hours=hours, max_articles=None
        )
        if hours is not None:
            articles = filter_by_lookback(articles, hours)
        articles = deduplicate_articles(articles)
        
        if max_articles is not None:
            articles = articles[:max_articles]
        
        return self.resolve_article_urls(articles, show_progress=show_progress) if resolve_urls else articles

    def get(
        self,
        *,
        topic: str | None = None,
        hours: float | None = 24,
        max_articles: int | None = 20,
        query_limit: int | None = None,
        resolve_urls: bool = False,
        extract_text: bool = False,
        show_progress: bool = True,
    ) -> list[NewsArticle]:
        """Get general financial news or news about a specific topic.

        Args:
            resolve_urls: Resolve publisher URLs after discovery; requires the optional extra.
            extract_text: Download article pages and attach extracted text and status.
            show_progress: Print progress updates for URL resolution and text extraction.
            topic: Optional ticker, company, sector, macro topic, or search phrase.
            hours: Lookback window. Use ``None`` to disable date filtering.
            max_articles: Maximum number of articles returned, or ``None`` for no maximum.
            query_limit: Maximum number of RSS searches; defaults to the client's
                configured query budget. Each attempted search counts as one request.
        """
        if max_articles is not None and (
            isinstance(max_articles, bool)
            or not isinstance(max_articles, int)
            or max_articles < 1
        ):
            raise ValueError("max_articles must be a positive integer or None")
        
        if hours is not None and (isinstance(hours, bool) or hours < 0):
            raise ValueError("hours must be non-negative or None")
        budget = self._query_limit if query_limit is None else query_limit
        
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
            raise ValueError("query_limit must be a positive integer")
        
        if topic is None:
            queries = self._query_builder.build_market_queries(query_limit=budget)
        else:
            queries = self._query_builder.build_topic_queries(topic, query_limit=budget)

        collected: list[NewsArticle] = []
        per_query_max_articles = (
            None if max_articles is None else max(max_articles, min(50, max_articles * 2))
        )
        for query in queries:
            collected.extend(self._provider.search(
                query, 
                lookback_hours=hours, 
                max_articles=per_query_max_articles
            ))
        articles = collected
        
        if hours is not None:
            articles = filter_by_lookback(articles, hours)
        articles.sort(key=lambda article: (
            article.published_at or datetime.min.replace(tzinfo=UTC)
        ), reverse=True)
        articles = deduplicate_articles(articles)
        
        if max_articles is not None:
            articles = articles[:max_articles]
        
        if resolve_urls:
            articles = self.resolve_article_urls(articles, show_progress=show_progress)
        
        if extract_text:
            results = self.extract_articles_text(articles, show_progress=show_progress)
            articles = [
                replace(
                    article,
                    text=result.text,
                    text_extraction_status=result.status,
                )
                for article, result in zip(articles, results, strict=True)
            ]
        
        return articles

    def resolve_article_url(self, article: NewsArticle) -> NewsArticle:
        """Resolve one article URL, preserving the RSS URL and metadata.

        Resolution is opt-in and requires the optional ``url-resolution`` extra.
        A failed resolution is recorded on the returned article; the original
        article is never discarded.
        """
        if not isinstance(article, NewsArticle):
            raise TypeError("article must be a NewsArticle")
        
        if article.resolved_url:
            return replace(
                article,
                url_resolution_status=article.url_resolution_status or "success",
            )
        result = self._url_resolver.resolve(article.url)
        
        return replace(
            article,
            resolved_url=result.resolved_url,
            url_resolution_status=result.status,
            url_resolution_error=result.error,
        )

    def resolve_article_urls(
        self, articles: list[NewsArticle], 
        *, 
        show_progress: bool = True
    ) -> list[NewsArticle]:
        """Resolve article URLs sequentially and report progress to stderr."""
        return run_with_progress(
            articles, 
            self.resolve_article_url, 
            label="Resolving URLs", 
            enabled=show_progress
        )

    def extract_article_text(self, article: NewsArticle | str) -> ArticleTextResult:
        """Download one article page and extract its main text with Trafilatura."""
        return self._article_text_extractor.extract(article)

    def extract_articles_text(
        self, articles: list[NewsArticle | str],
        *, 
        show_progress: bool = True
    ) -> list[ArticleTextResult]:
        """Extract article text sequentially, retaining one result per input item."""
        return run_with_progress(
            articles, 
            self.extract_article_text, 
            label="Extracting article text", 
            enabled=show_progress
        )

    def close(self) -> None:
        """Close the provider if it offers a close method."""
        close = getattr(self._provider, "close", None)
        if callable(close):
            close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


# Compatibility-friendly short name for users who prefer a package-level client name.
Pyfinews = NewsClient

__all__ = ["NewsClient", "NewsFetchError", "NewsParseError", "Pyfinews", "PyfinewsError"]
