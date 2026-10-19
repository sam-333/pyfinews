import pytest

from pyfinews import FinancialQueryBuilder, load_publishers, load_taxonomy


def _builder(query_limit=30):
    return FinancialQueryBuilder(
        load_taxonomy(), 
        load_publishers(), 
        query_limit=query_limit
    )


def test_market_queries_respect_query_limit():
    queries = _builder(query_limit=15).build_market_queries()

    assert len(queries) == 15


def test_market_queries_prioritize_publishers_then_domains():
    domains = [
        {"id": "macro", "name": "Macro", "query_terms": ["inflation", "economic growth"]},
        {"id": "markets", "name": "Markets", "query_terms": ["equities", "stock market"]},
    ]
    publishers = [
        {"id": "b", "name": "B Outlet", "priority": 2, "regions": ["asia"]},
        {"id": "a", "name": "A Outlet", "priority": 1, "regions": ["europe"]},
    ]
    queries = FinancialQueryBuilder(domains, publishers, query_limit=4).build_market_queries()
    
    assert len(queries) == 4
    assert all('"A Outlet"' in query.query for query in queries[:2])
    assert all('"B Outlet"' in query.query for query in queries[2:])
    assert '"inflation" OR "economic growth"' in queries[0].query
    assert '"equities" OR "stock market"' in queries[1].query


def test_market_queries_only_include_publisher_combinations():
    domains = [{"id": "macro", "name": "Macro", "query_terms": ["inflation", "GDP"]}]
    publishers = [{"id": "r", "name": "Reuters", "priority": 1, "regions": []}]
    queries = FinancialQueryBuilder(
        domains, 
        publishers, 
        query_limit=2
    ).build_market_queries()

    assert len(queries) == 1
    assert queries[0].query == '("inflation" OR "GDP") "Reuters"'


def test_disabled_publishers_are_not_used():
    domains = [{"id": "macro", "name": "Macro", "query_terms": ["inflation"]}]
    publishers = [{"id": "p1", "name": "Publisher One", "enabled": False, "priority": 1}]
    builder = FinancialQueryBuilder(domains, publishers)

    with pytest.raises(ValueError, match="At least one enabled publisher"):
        builder.build_market_queries()


def test_topic_queries_start_with_topic_then_publishers_by_priority():
    publishers = [
        {"id": "b", "name": "B Outlet", "priority": 2},
        {"id": "a", "name": "A Outlet", "priority": 1},
    ]
    queries = FinancialQueryBuilder(
        [], 
        publishers, 
        query_limit=3
    ).build_topic_queries("AAPL")

    assert len(queries) == 2
    assert queries[0].query == '(AAPL) "A Outlet"'
    assert queries[1].query == '(AAPL) "B Outlet"'


def test_invalid_query_limit_rejected():
    with pytest.raises(ValueError, match="query_limit"):
        _builder().build_market_queries(query_limit=0)
    with pytest.raises(ValueError, match="query_limit"):
        FinancialQueryBuilder([], [], query_limit=True)
