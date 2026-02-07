"""Google News RSS 爬蟲模組

使用 Google News RSS feed 抓取新聞，無需 API Key。
"""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

import feedparser

from src.models.content import ContentItem
from src.scrapers.base import BaseScraper
from src.utils.rate_limiter import rate_limit

GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss"


class GoogleNewsScraper(BaseScraper):
    """Google News RSS 爬蟲

    支援:
    - 關鍵字搜尋
    - 地區/語言篩選
    - 話題訂閱
    """

    name = "google_news"
    source_type = "news"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        language: str = "zh-TW",
        region: str = "TW",
        **kwargs: Any,
    ) -> list[ContentItem]:
        """搜尋新聞

        Args:
            query: 搜尋關鍵字
            max_results: 最大結果數
            language: 語言代碼 (zh-TW, en-US, etc.)
            region: 地區代碼 (TW, US, etc.)

        Returns:
            ContentItem 列表
        """
        await rate_limit("google_news")

        # 建構 RSS URL
        encoded_query = quote_plus(query)
        url = f"{GOOGLE_NEWS_RSS_BASE}/search?q={encoded_query}&hl={language}&gl={region}&ceid={region}:{language.split('-')[0]}"

        response = await self._fetch(url)
        feed = feedparser.parse(response.text)

        return self._parse_feed(feed, max_results, language)

    async def get_top_stories(
        self,
        language: str = "zh-TW",
        region: str = "TW",
        max_results: int = 10,
    ) -> list[ContentItem]:
        """取得頭條新聞

        Args:
            language: 語言代碼
            region: 地區代碼
            max_results: 最大結果數

        Returns:
            ContentItem 列表
        """
        await rate_limit("google_news")

        url = f"{GOOGLE_NEWS_RSS_BASE}?hl={language}&gl={region}&ceid={region}:{language.split('-')[0]}"

        response = await self._fetch(url)
        feed = feedparser.parse(response.text)

        return self._parse_feed(feed, max_results, language)

    async def get_topic(
        self,
        topic: str,
        language: str = "zh-TW",
        region: str = "TW",
        max_results: int = 10,
    ) -> list[ContentItem]:
        """取得特定話題新聞

        Args:
            topic: 話題 ID (WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH)
            language: 語言代碼
            region: 地區代碼
            max_results: 最大結果數

        Returns:
            ContentItem 列表
        """
        await rate_limit("google_news")

        topic_map = {
            "world": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FucG9MVUZXR2dKVVZ5Z0FQAQ",
            "nation": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FucG9MVUZXR2dKVVZ5Z0FQAQ",
            "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FucG9MVUZXR2dKVVZ5Z0FQAQ",
            "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FucG9MVUZXR2dKVVZ5Z0FQAQ",
            "entertainment": "CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FuaG9MVUZXR2dKVVZ5Z0FQAQ",
            "sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FuaG9MVUZXR2dKVVZ5Z0FQAQ",
            "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FuaG9MVUZXR2dKVVZ5Z0FQAQ",
            "health": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR3QwTlRFU0FuaG9MVUZXR2dKVVZ5Z0FQAQ",
        }

        topic_id = topic_map.get(topic.lower(), topic)
        url = f"{GOOGLE_NEWS_RSS_BASE}/topics/{topic_id}?hl={language}&gl={region}&ceid={region}:{language.split('-')[0]}"

        response = await self._fetch(url)
        feed = feedparser.parse(response.text)

        return self._parse_feed(feed, max_results, language)

    def _parse_feed(
        self,
        feed: feedparser.FeedParserDict,
        max_results: int,
        language: str,
    ) -> list[ContentItem]:
        """解析 RSS feed"""
        results: list[ContentItem] = []

        for entry in feed.entries[:max_results]:
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass

            # Google News RSS 的連結是 Google 轉址，需要解析出原始來源
            # 格式: https://news.google.com/rss/articles/...
            source_name = "Unknown"
            if hasattr(entry, "source") and entry.source:
                source_name = entry.source.get("title", "Unknown")

            # 從標題中提取內容摘要 (Google News RSS 通常沒有 summary)
            content = ""
            if hasattr(entry, "summary"):
                content = entry.summary

            results.append(
                ContentItem(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    content=content,
                    source_type="news",
                    source_name=f"GoogleNews:{source_name}",
                    source_url=entry.get("link"),
                    published_at=published_at,
                    language=language,
                    raw_data=dict(entry),
                )
            )

        return results
