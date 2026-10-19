"""Title-based article deduplication."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from pyfinews.models import NewsArticle


def normalize_title(title: str) -> str:
    """Normalize a headline for duplicate detection without using URLs."""
    normalized = unicodedata.normalize("NFKC", title).casefold()

    return re.sub(r"\s+", " ", normalized).strip()


def deduplicate_articles(articles: Iterable[NewsArticle]) -> list[NewsArticle]:
    """Keep the first article for each normalized title, preserving input order."""
    result: list[NewsArticle] = []
    seen: set[str] = set()

    for article in articles:
        key = normalize_title(article.title)

        if key not in seen:
            seen.add(key)
            result.append(article)

    return result


__all__ = ["deduplicate_articles", "normalize_title"]
