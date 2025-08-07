# backend/api/services/news_crawler.py

import requests
from readability import Document

def extract_article_text(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        doc = Document(response.text)
        article_html = doc.summary()
        title = doc.title()

        # Strip HTML tags to get plain text
        from bs4 import BeautifulSoup
        text = BeautifulSoup(article_html, "html.parser").get_text()
        return text.strip()

    except Exception as e:
        print(f"[Crawler] Failed to extract article from {url}: {e}")
        return ""