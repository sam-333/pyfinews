
"""Download financial news articles and extract their text."""

import json
from pathlib import Path

from pyfinews import NewsClient


def main() -> None:
    client = NewsClient(query_limit=30)

    articles = client.get(
        max_articles=30,
        resolve_urls=True,
        extract_text=True,
    )

    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "articles.json"

    records = [
        {
            "title": article.title,
            "url": article.url,
            "resolved_url": article.resolved_url,
            "url_resolution_status": article.url_resolution_status,
            "url_resolution_error": article.url_resolution_error,
            "source": article.source,
            "published_at": (
                article.published_at.isoformat()
                if article.published_at
                else None
            ),
            "text": article.text,
            "text_extraction_status": (
                article.text_extraction_status.value
                if article.text_extraction_status
                else None
            ),
        }
        for article in articles
    ]

    output_path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    successful = sum(
        bool(article.text and article.text.strip())
        for article in articles
    )

    print(f"Saved {len(records)} articles to {output_path}")
    print(f"Successfully extracted text for {successful} articles")

    if articles:
        print(f"Text extraction success rate: {successful / len(articles):.1%}")
    else:
        print("No articles were returned.")


if __name__ == "__main__":
    main()
