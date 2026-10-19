import json

import pytest

from pyfinews.taxonomy import TaxonomyLoadError, load_taxonomy


def test_loads_packaged_default_taxonomy():
    domains = load_taxonomy()

    assert len(domains) == 12
    assert len({domain["id"] for domain in domains}) == 12
    assert all(domain["query_terms"] for domain in domains)
    assert all(isinstance(domain["enabled"], bool) for domain in domains)


def test_preserves_additional_fields_and_normalizes_terms(tmp_path):
    path = tmp_path / "taxonomy.json"
    path.write_text(json.dumps({
        "domains": [{
            "id": "macro",
            "name": "Macroeconomics",
            "description": "Economic conditions",
            "query_terms": [" inflation ", "growth"],
        }]
    }), encoding="utf-8")

    result = load_taxonomy(path)

    assert result == [{
        "id": "macro",
        "name": "Macroeconomics",
        "description": "Economic conditions",
        "query_terms": ["inflation", "growth"],
        "enabled": True,
    }]


@pytest.mark.parametrize("payload", [
    [],
    {},
    {"domains": {}},
    {"domains": [None]},
    {"domains": [{"id": "", "name": "Macro", "query_terms": ["inflation"]}]},
    {"domains": [{"id": "x", "name": "", "query_terms": ["inflation"]}]},
    {"domains": [{"id": "x", "name": "Macro", "query_terms": []}]},
    {"domains": [{"id": "x", "name": "Macro", "query_terms": [" "]}]},
    {"domains": [{"id": "x", "name": "Macro", "query_terms": ["inflation"], "enabled": "yes"}]},
    {"domains": [
        {"id": "x", "name": "A", "query_terms": ["a"]},
        {"id": "x", "name": "B", "query_terms": ["b"]},
    ]},
])
def test_rejects_invalid_taxonomy(tmp_path, payload):
    path = tmp_path / "taxonomy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(TaxonomyLoadError):
        load_taxonomy(path)


def test_rejects_invalid_json(tmp_path):
    path = tmp_path / "taxonomy.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(TaxonomyLoadError, match="Invalid JSON"):
        load_taxonomy(path)


def test_rejects_missing_file(tmp_path):
    with pytest.raises(TaxonomyLoadError, match="Unable to read"):
        load_taxonomy(tmp_path / "missing.json")
