"""Optional Google News RSS URL resolution."""

from __future__ import annotations

from dataclasses import dataclass
from googlenewsdecoder import gnewsdecoder
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class URLResolutionResult:
    """Outcome of resolving a Google News URL to its publisher URL."""

    rss_url: str
    resolved_url: str | None
    status: str
    error: str | None = None


class GoogleNewsURLResolver:
    """Resolve Google News RSS article URLs using ``googlenewsdecoder``."""

    def __init__(self, *, interval: float = 1.0, timeout: float = 15.0) -> None:
        if isinstance(interval, bool) or not isinstance(interval, (int, float)) or interval < 0:
            raise ValueError("interval must be non-negative")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        
        self.interval = float(interval)
        self.timeout = float(timeout)

    def resolve(self, url: str) -> URLResolutionResult:
        """Resolve one Google News URL; retain the input URL on failure."""
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must be a non-empty string")
        url = url.strip()
        parsed = urlparse(url)
        
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute HTTP(S) URL")

        try:
            decoded = gnewsdecoder(
                url, 
                interval=self.interval, 
                timeout=self.timeout
            )
        except Exception as exc:  # Keep a single resolver error from aborting a batch.
            return URLResolutionResult(
                rss_url=url,
                resolved_url=None,
                status="resolution_failed",
                error=str(exc) or type(exc).__name__,
            )

        if not isinstance(decoded, dict):
            return URLResolutionResult(
                url, 
                None, 
                "resolution_failed", 
                "Decoder returned an invalid result"
            )

        successful = decoded.get("success", decoded.get("status", False))
        candidate = decoded.get("decoded_url")
        if not successful or not isinstance(candidate, str):
            message = decoded.get("message") or decoded.get("error") or "Could not resolve URL"
            
            return URLResolutionResult(
                url, 
                None, 
                "resolution_failed", 
                str(message)
            )

        candidate = candidate.strip()
        candidate_parsed = urlparse(candidate)
        if candidate_parsed.scheme not in {"http", "https"} or not candidate_parsed.netloc:
            return URLResolutionResult(
                url, 
                None, 
                "resolution_failed", 
                "Decoder returned an invalid HTTP(S) URL"
            )

        if (candidate_parsed.hostname or "").lower() == "news.google.com":
            return URLResolutionResult(
                url, 
                None, 
                "resolution_failed", 
                "Resolved URL still points to Google News"
            )

        return URLResolutionResult(url, candidate, "success")

    def resolve_many(self, urls: list[str]) -> list[URLResolutionResult]:
        """Resolve URLs sequentially, preserving input order and duplicates."""
        return [self.resolve(url) for url in urls]


__all__ = ["GoogleNewsURLResolver", "URLResolutionResult"]
