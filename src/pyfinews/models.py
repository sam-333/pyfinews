"""Public data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class ArticleTextStatus(StrEnum):
    """Status of optional article-text extraction."""

    SUCCESS = "success"
    FETCH_FAILED = "fetch_failed"
    EXTRACTION_FAILED = "extraction_failed"


@dataclass(frozen=True, slots=True)
class NewsArticle:
    """Normalized article metadata, preserving the feed URL and optional publisher URL."""

    title: str
    url: str
    source: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime | None = None
    summary: str | None = None
    query: str | None = None
    text: str | None = None
    text_extraction_status: ArticleTextStatus | None = None
    resolved_url: str | None = None
    url_resolution_status: str | None = None
    url_resolution_error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string")
        if not isinstance(self.url, str) or not self.url.strip():
            raise ValueError("url must be a non-empty string")
        if self.text is not None and not isinstance(self.text, str):
            raise ValueError("text must be a string or None")
        if self.text_extraction_status is not None and not isinstance(
            self.text_extraction_status, ArticleTextStatus
        ):
            try:
                object.__setattr__(
                    self,
                    "text_extraction_status",
                    ArticleTextStatus(self.text_extraction_status),
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "text_extraction_status must be a valid ArticleTextStatus or None"
                ) from exc

        if self.resolved_url is not None:
            if not isinstance(self.resolved_url, str) or not self.resolved_url.strip():
                raise ValueError("resolved_url must be a non-empty string or None")
            if not self.resolved_url.strip().startswith(("http://", "https://")):
                raise ValueError("resolved_url must use http or https")

            object.__setattr__(self, "resolved_url", self.resolved_url.strip())

        if self.url_resolution_status is not None and self.url_resolution_status not in {
            "success", "resolution_failed"
        }:
            raise ValueError("url_resolution_status must be 'success', 'resolution_failed', or None")
        
        if self.url_resolution_error is not None and not isinstance(self.url_resolution_error, str):
            raise ValueError("url_resolution_error must be a string or None")
        
        for field_name in ("published_at", "retrieved_at"):
            value = getattr(self, field_name)

            if value is not None:
                if value.tzinfo is None or value.utcoffset() is None:
                    raise ValueError(f"{field_name} must be timezone-aware")
                
                object.__setattr__(self, field_name, value.astimezone(timezone.utc))
        
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "url", self.url.strip())


__all__ = ["ArticleTextStatus", "NewsArticle"]
