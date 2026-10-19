"""Optional article-page downloading and main-text extraction with Trafilatura."""

from __future__ import annotations

from dataclasses import dataclass
from pyfinews.models import ArticleTextStatus, NewsArticle


@dataclass(frozen=True, slots=True)
class ArticleTextResult:
    """Text-extraction outcome for one article URL.

    ``status`` is ``"success"``, ``"fetch_failed"``, or ``"extraction_failed"``.
    ``text`` is ``None`` when no article body could be extracted.
    """

    url: str
    text: str | None
    status: ArticleTextStatus
    error: str | None = None


class ArticleTextExtractor:
    """Download article HTML and extract its main text using Trafilatura.

    Trafilatura is an optional dependency. Install it with
    ``uv add 'pyfinews[article-text]'`` when using a published package, or
    ``uv sync --extra article-text`` from a source checkout.
    """

    def __init__(self, *, timeout: float = 15.0, user_agent: str = "pyfinews/0.1.0") -> None:
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self.timeout = float(timeout)
        self.user_agent = user_agent

    def extract(self, article: NewsArticle | str) -> ArticleTextResult:
        """Extract the main text from a ``NewsArticle`` or a URL.

        Network and extraction failures are returned as a result instead of
        raised, so callers can process a batch without losing other articles.
        """
        if (
            isinstance(article, NewsArticle)
            and article.url_resolution_status == "resolution_failed"
            and not article.resolved_url
        ):
            return ArticleTextResult(
                article.url,
                None,
                ArticleTextStatus.FETCH_FAILED,
                article.url_resolution_error or "Publisher URL resolution failed",
            )

        url = (article.resolved_url or article.url) if isinstance(article, NewsArticle) else article
        if not isinstance(url, str) or not url.strip():
            raise ValueError("article must be a NewsArticle or a non-empty URL string")
        
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            raise ValueError("article URL must use http or https")

        try:
            import trafilatura
        except ImportError as exc:
            raise ImportError(
                "Article text extraction requires the optional 'article-text' extra. "
                "Install it with `uv sync --extra article-text` or `uv add trafilatura`."
            ) from exc

        try:
            from trafilatura.settings import use_config

            config = use_config()
            config.set("DEFAULT", "DOWNLOAD_TIMEOUT", str(int(self.timeout)))
            config.set("DEFAULT", "USER_AGENTS", self.user_agent)

            html = trafilatura.fetch_url(
                url,
                config=config,
            )
        except Exception as exc:  # Keep one problematic page from aborting a batch.
            return ArticleTextResult(
                url, 
                None, 
                ArticleTextStatus.FETCH_FAILED, 
                str(exc) or type(exc).__name__
            )
        if html is None:
            return ArticleTextResult(
                url, 
                None, 
                ArticleTextStatus.FETCH_FAILED, 
                "Download failed"
            )

        try:
            text = trafilatura.extract(html, url=url, include_comments=False)
        except Exception as exc:  # Keep one problematic page from aborting a batch.
            return ArticleTextResult(
                url, 
                None, 
                ArticleTextStatus.EXTRACTION_FAILED, 
                str(exc) or type(exc).__name__
            )

        if not isinstance(text, str) or not text.strip():
            return ArticleTextResult(
                url, 
                None, 
                ArticleTextStatus.EXTRACTION_FAILED, 
                "No main article text found"
            )
        
        return ArticleTextResult(url, text.strip(), ArticleTextStatus.SUCCESS)

    def extract_many(self, articles: list[NewsArticle | str]) -> list[ArticleTextResult]:
        """Extract text sequentially, preserving input order and duplicate URLs."""
        return [self.extract(article) for article in articles]


__all__ = ["ArticleTextExtractor", "ArticleTextResult", "ArticleTextStatus"]
