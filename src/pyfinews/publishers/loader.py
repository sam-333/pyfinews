"""Load and validate pyfinews' publisher registry."""

from __future__ import annotations

import json
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path
from typing import Any


class PublisherLoadError(ValueError):
    """Raised when a publisher registry cannot be loaded or validated."""


def _read_publishers_text(path: str | Path | None) -> tuple[str, str]:
    if path is None:
        source = "<packaged default publishers>"
        try:
            text = (
                files("pyfinews.publishers")
                .joinpath("default_publishers.json")
                .read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError) as exc:
            raise PublisherLoadError(
                f"Unable to read publishers file {source}: {exc}"
            ) from exc
        return text, source

    source_path = Path(path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PublisherLoadError(
            f"Unable to read publisher file {source_path}: {exc}"
        ) from exc
    source = str(source_path)

    return text, str(source_path)


def load_publishers(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load the default publisher registry or a JSON file at *path*.

    The JSON document must have a top-level ``publishers`` array. Each
    publisher requires ``id`` and ``name``. ``enabled`` defaults to True;
    ``priority`` defaults to the publisher's position in the array.
    Additional fields (such as ``aliases`` and ``regions``) are preserved.
    """
    text, source = _read_publishers_text(path)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PublisherLoadError(
            f"Invalid JSON in publisher file {source}: {exc.msg}"
        ) from exc

    if not isinstance(payload, Mapping):
        raise PublisherLoadError("Publisher JSON must be an object")
    publishers = payload.get("publishers")
    if not isinstance(publishers, list):
        raise PublisherLoadError(
            "Publisher JSON must contain a 'publishers' array"
        )

    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for index, raw in enumerate(publishers):
        prefix = f"publishers[{index}]"
        if not isinstance(raw, Mapping):
            raise PublisherLoadError(f"{prefix} must be an object")

        publisher = dict(raw)
        publisher_id = publisher.get("id")
        name = publisher.get("name")
        enabled = publisher.get("enabled", True)
        priority = publisher.get("priority", index + 1)
        aliases = publisher.get("aliases", [])
        regions = publisher.get("regions", [])

        if not isinstance(publisher_id, str) or not publisher_id.strip():
            raise PublisherLoadError(
                f"{prefix}.id must be a non-empty string"
            )
        if publisher_id != publisher_id.strip():
            raise PublisherLoadError(
                f"{prefix}.id must not have surrounding whitespace"
            )
        if publisher_id in seen_ids:
            raise PublisherLoadError(f"Duplicate publisher id: {publisher_id!r}")
        seen_ids.add(publisher_id)

        if not isinstance(name, str) or not name.strip():
            raise PublisherLoadError(
                f"{prefix}.name must be a non-empty string"
            )
        if not isinstance(enabled, bool):
            raise PublisherLoadError(f"{prefix}.enabled must be a boolean")
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise PublisherLoadError(f"{prefix}.priority must be an integer")
        if not isinstance(aliases, list) or any(
            not isinstance(alias, str) or not alias.strip() for alias in aliases
        ):
            raise PublisherLoadError(
                f"{prefix}.aliases must be an array of non-empty strings"
            )
        if not isinstance(regions, list) or any(
            not isinstance(region, str) or not region.strip()
            for region in regions
        ):
            raise PublisherLoadError(
                f"{prefix}.regions must be an array of non-empty strings"
            )

        publisher["enabled"] = enabled
        publisher["priority"] = priority
        publisher["aliases"] = [alias.strip() for alias in aliases]
        publisher["regions"] = [region.strip() for region in regions]
        validated.append(publisher)

    # Keep registry output deterministic by ascending publisher priority.
    validated.sort(key=lambda item: item["priority"])

    return validated
