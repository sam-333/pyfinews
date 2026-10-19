"""Financial news publisher configuration."""

from .loader import PublisherLoadError, load_publishers

__all__ = ["PublisherLoadError", "load_publishers"]
