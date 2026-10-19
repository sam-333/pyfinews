"""pyfinews: financial-news discovery through Google News RSS."""

from pyfinews.article_text import ArticleTextExtractor, ArticleTextResult
from pyfinews.client import NewsClient, Pyfinews
from pyfinews.deduplication import deduplicate_articles, normalize_title
from pyfinews.exceptions import NewsFetchError, NewsParseError, PyfinewsError
from pyfinews.filters import filter_by_lookback
from pyfinews.models import ArticleTextStatus, NewsArticle
from pyfinews.providers.google_news import GoogleNewsRSSProvider
from pyfinews.publishers.loader import PublisherLoadError, load_publishers
from pyfinews.queries.financial import FinancialQueryBuilder
from pyfinews.queries.google_news import GoogleNewsQuery
from pyfinews.taxonomy.loader import TaxonomyLoadError, load_taxonomy
from pyfinews.url_resolution import GoogleNewsURLResolver, URLResolutionResult

__version__ = "0.1.0"

__all__ = [
    "ArticleTextExtractor", "ArticleTextResult", "ArticleTextStatus", "FinancialQueryBuilder",
    "GoogleNewsQuery", "GoogleNewsRSSProvider", "GoogleNewsURLResolver",
    "NewsArticle", "NewsClient", "NewsFetchError", "NewsParseError", "PublisherLoadError",
    "Pyfinews", "PyfinewsError", "TaxonomyLoadError", "URLResolutionResult",
    "deduplicate_articles", "filter_by_lookback", "load_publishers", "load_taxonomy",
    "normalize_title",
]
