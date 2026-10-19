"""Load and validate pyfinews' financial-domain taxonomy."""

from __future__ import annotations

import json
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path
from typing import Any


class TaxonomyLoadError(ValueError):
    """Raised when a taxonomy file cannot be loaded or validated."""


def _read_taxonomy_text(path: str | Path | None) -> tuple[str, str]:
    if path is None:
        source = "<packaged default taxonomy>"
        try:
            text = (
                files("pyfinews.taxonomy")
                .joinpath("default_taxonomy.json")
                .read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError) as exc:
            raise TaxonomyLoadError(
                f"Unable to read taxonomy file {source}: {exc}"
            ) from exc
        return text, source

    source_path = Path(path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise TaxonomyLoadError(
            f"Unable to read taxonomy file {source_path}: {exc}"
        ) from exc

    return text, str(source_path)


def load_taxonomy(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load the default taxonomy or a JSON file at *path*.

    The JSON document must have a top-level ``domains`` array. Each domain
    requires ``id``, ``name``, and ``query_terms``; ``enabled`` defaults to
    True. Additional fields (for example ``description``) are preserved.
    """
    text, source = _read_taxonomy_text(path)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TaxonomyLoadError(
            f"Invalid JSON in taxonomy file {source}: {exc.msg}"
        ) from exc

    if not isinstance(payload, Mapping):
        raise TaxonomyLoadError("Taxonomy JSON must be an object")
    domains = payload.get("domains")
    if not isinstance(domains, list):
        raise TaxonomyLoadError("Taxonomy JSON must contain a 'domains' array")

    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for index, raw in enumerate(domains):
        prefix = f"domains[{index}]"
        if not isinstance(raw, Mapping):
            raise TaxonomyLoadError(f"{prefix} must be an object")

        domain = dict(raw)
        domain_id = domain.get("id")
        name = domain.get("name")
        terms = domain.get("query_terms")
        enabled = domain.get("enabled", True)

        if not isinstance(domain_id, str) or not domain_id.strip():
            raise TaxonomyLoadError(f"{prefix}.id must be a non-empty string")
        if domain_id != domain_id.strip():
            raise TaxonomyLoadError(f"{prefix}.id must not have surrounding whitespace")
        if domain_id in seen_ids:
            raise TaxonomyLoadError(f"Duplicate domain id: {domain_id!r}")
        seen_ids.add(domain_id)

        if not isinstance(name, str) or not name.strip():
            raise TaxonomyLoadError(f"{prefix}.name must be a non-empty string")
        if not isinstance(terms, list) or not terms:
            raise TaxonomyLoadError(f"{prefix}.query_terms must be a non-empty array")
        if any(not isinstance(term, str) or not term.strip() for term in terms):
            raise TaxonomyLoadError(
                f"{prefix}.query_terms must contain only non-empty strings"
            )
        if not isinstance(enabled, bool):
            raise TaxonomyLoadError(f"{prefix}.enabled must be a boolean")

        domain["enabled"] = enabled
        domain["query_terms"] = [term.strip() for term in terms]
        validated.append(domain)

    return validated
