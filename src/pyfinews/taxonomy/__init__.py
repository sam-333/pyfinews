"""Financial domain taxonomy configuration."""

from .loader import TaxonomyLoadError, load_taxonomy

__all__ = ["TaxonomyLoadError", "load_taxonomy"]
