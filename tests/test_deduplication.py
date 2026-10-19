from pyfinews import NewsArticle, deduplicate_articles, normalize_title


def test_normalize_title_ignores_case_and_whitespace():
    assert normalize_title("  Apple   Reports Earnings ") == "apple reports earnings"


def test_deduplicate_uses_title_only_and_keeps_first():
    first = NewsArticle(
        "Apple Reports Earnings", 
        "https://example.com/one"
    )
    same_title_other_url = NewsArticle(
        " apple reports earnings ", 
        "https://example.com/two"
    )
    different_title_same_url = NewsArticle(
        "Apple Reports Revenue", 
        "https://example.com/one"
    )

    assert deduplicate_articles([first, same_title_other_url, different_title_same_url]) == [
        first, different_title_same_url
    ]
