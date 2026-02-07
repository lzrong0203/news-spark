"""NewsAPI 爬蟲模組

使用 NewsAPI (https://newsapi.org) 抓取新聞內容。
需要 API Key，免費版每日有請求限制。
"""

from datetime import datetime
from typing import Any, Literal
from urllib.parse import urlencode

from src.models.content import ContentItem
from src.scrapers.base import BaseScraper
from src.utils.config import settings
from src.utils.rate_limiter import rate_limit

NEWSAPI_BASE_URL = "https://newsapi.org/v2"


class NewsAPIScraper(BaseScraper):
    """NewsAPI 爬蟲

    支援:
    - everything: 搜尋所有新聞
    - top-headlines: 頭條新聞
    """

    name = "newsapi"
    source_type = "news"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.api_key = api_key or settings.get_newsapi_key()
        if not self.api_key:
            raise ValueError("NewsAPI key is required. Set NEWSAPI_KEY in .env")

    async def search(
        self,
        query: str,
        max_results: int = 10,
        language: str = "zh",
        sort_by: Literal["relevancy", "popularity", "publishedAt"] = "publishedAt",
        **kwargs: Any,
    ) -> list[ContentItem]:
        """搜尋新聞

        Args:
            query: 搜尋關鍵字
            max_results: 最大結果數 (NewsAPI 免費版上限 100)
            language: 語言代碼 (zh, en, etc.)
            sort_by: 排序方式
            **kwargs: 額外參數 (from_date, to_date, domains, etc.)

        Returns:
            ContentItem 列表
        """
        await rate_limit("newsapi")

        params = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(max_results, 100),
        }

        # 可選參數
        if "from_date" in kwargs:
            params["from"] = kwargs["from_date"]
        if "to_date" in kwargs:
            params["to"] = kwargs["to_date"]
        if "domains" in kwargs:
            params["domains"] = kwargs["domains"]

        url = f"{NEWSAPI_BASE_URL}/everything?{urlencode(params)}"
        response = await self._fetch(url, headers={"X-Api-Key": self.api_key})
        data = response.json()

        if data.get("status") != "ok":
            error_msg = data.get("message", "Unknown error")
            raise RuntimeError(f"NewsAPI error: {error_msg}")

        return self._parse_articles(data.get("articles", []))

    async def get_top_headlines(
        self,
        country: str = "tw",
        category: str | None = None,
        max_results: int = 10,
        **kwargs: Any,
    ) -> list[ContentItem]:
        """取得頭條新聞

        Args:
            country: 國家代碼 (tw, us, etc.)
            category: 分類 (business, technology, etc.)
            max_results: 最大結果數

        Returns:
            ContentItem 列表
        """
        await rate_limit("newsapi")

        params: dict[str, Any] = {
            "country": country,
            "pageSize": min(max_results, 100),
        }

        if category:
            params["category"] = category

        if "query" in kwargs:
            params["q"] = kwargs["query"]

        url = f"{NEWSAPI_BASE_URL}/top-headlines?{urlencode(params)}"
        response = await self._fetch(url, headers={"X-Api-Key": self.api_key})
        data = response.json()

        if data.get("status") != "ok":
            error_msg = data.get("message", "Unknown error")
            raise RuntimeError(f"NewsAPI error: {error_msg}")

        return self._parse_articles(data.get("articles", []))

    def _parse_articles(self, articles: list[dict[str, Any]]) -> list[ContentItem]:
        """解析 NewsAPI 回應"""
        results: list[ContentItem] = []

        for article in articles:
            # 跳過被移除的文章
            if article.get("title") == "[Removed]":
                continue

            published_at = None
            if article.get("publishedAt"):
                try:
                    published_at = datetime.fromisoformat(
                        article["publishedAt"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            source_info = article.get("source", {})

            results.append(
                ContentItem(
                    title=article.get("title", ""),
                    url=article.get("url", ""),
                    content=article.get("description") or article.get("content") or "",
                    source_type="news",
                    source_name=f"NewsAPI:{source_info.get('name', 'Unknown')}",
                    source_url=article.get("url"),
                    author=article.get("author"),
                    published_at=published_at,
                    image_url=article.get("urlToImage"),
                    language="zh-TW",
                    raw_data=article,
                )
            )

        return results
