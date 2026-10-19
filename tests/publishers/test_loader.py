import json

import pytest

from pyfinews.publishers import PublisherLoadError, load_publishers


def test_loads_packaged_default_publishers_in_priority_order():
    publishers = load_publishers()

    assert len(publishers) == 20
    assert len({publisher["id"] for publisher in publishers}) == 20
    assert [publisher["priority"] for publisher in publishers] == list(range(1, 21))
    assert all(isinstance(publisher["enabled"], bool) for publisher in publishers)


def test_defaults_optional_fields_and_sorts_by_priority(tmp_path):
    path = tmp_path / "publishers.json"
    path.write_text(json.dumps({
        "publishers": [
            {"id": "second", "name": "Second", "priority": 20},
            {"id": "first", "name": "First", "priority": 10},
        ]
    }), encoding="utf-8")

    result = load_publishers(path)

    assert [publisher["id"] for publisher in result] == ["first", "second"]
    assert result[0]["enabled"] is True
    assert result[0]["aliases"] == []
    assert result[0]["regions"] == []


@pytest.mark.parametrize("payload", [
    [],
    {},
    {"publishers": {}},
    {"publishers": [None]},
    {"publishers": [{"id": "", "name": "Publisher"}]},
    {"publishers": [{"id": "x", "name": ""}]},
    {"publishers": [{"id": "x", "name": "Publisher", "enabled": "yes"}]},
    {"publishers": [{"id": "x", "name": "Publisher", "priority": True}]},
    {"publishers": [{"id": "x", "name": "Publisher", "aliases": "Alias"}]},
    {"publishers": [{"id": "x", "name": "Publisher", "aliases": [" "]}]},
    {"publishers": [{"id": "x", "name": "Publisher", "regions": [1]}]},
    {"publishers": [
        {"id": "x", "name": "One"},
        {"id": "x", "name": "Two"},
    ]},
])
def test_rejects_invalid_publishers(tmp_path, payload):
    path = tmp_path / "publishers.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PublisherLoadError):
        load_publishers(path)


def test_rejects_invalid_json(tmp_path):
    path = tmp_path / "publishers.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(PublisherLoadError, match="Invalid JSON"):
        load_publishers(path)


def test_rejects_missing_file(tmp_path):
    with pytest.raises(PublisherLoadError, match="Unable to read"):
        load_publishers(tmp_path / "missing.json")
