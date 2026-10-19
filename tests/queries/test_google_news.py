from urllib.parse import parse_qs, urlparse

import pytest

from pyfinews import GoogleNewsQuery


def test_url_encodes_query_and_omits_language_country():
    url = GoogleNewsQuery('"stock market" OR AAPL').to_url()
    parsed = urlparse(url)

    assert parsed.netloc == "news.google.com"
    assert parse_qs(parsed.query) == {"q": ['"stock market" OR AAPL']}


@pytest.mark.parametrize("query", ["", "  ", None])
def test_query_rejects_empty_or_non_string(query):
    with pytest.raises(ValueError):
        GoogleNewsQuery(query)
