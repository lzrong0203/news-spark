"""新聞抓取代理

協調 NewsAPIScraper 和 GoogleNewsScraper，並行搜尋並彙整結果。
"""

import asyncio
import logging
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from src.agents.base import AgentContext, AgentResult, BaseAgent
from src.models.content import ContentItem
from src.scrapers.google_news import GoogleNewsScraper
from src.scrapers.news_api import NewsAPIScraper

logger = logging.getLogger(__name__)

_MIN_DATETIME = datetime.min.replace(tzinfo=timezone.utc)


class NewsScraperInput(BaseModel):
    """新聞抓取代理輸入"""

    queries: list[str] = Field(..., min_length=1, description="搜尋子查詢列表")
    language: str = Field(default="zh-TW", description="語言")
    max_results_per_source: int = Field(
        default=10, ge=1, le=50, description="每來源最大結果數"
    )


class NewsScraperOutput(BaseModel):
    """新聞抓取代理輸出"""

    items: list[ContentItem] = Field(default_factory=list, description="抓取到的內容")
    total_count: int = Field(default=0, description="總筆數")
    sources_used: list[str] = Field(default_factory=list, description="使用的來源")
    errors: list[str] = Field(default_factory=list, description="錯誤訊息")


class NewsScraperAgent(BaseAgent[NewsScraperInput, NewsScraperOutput]):
    """新聞抓取代理

    並行呼叫 NewsAPI 和 GoogleNews 爬蟲，彙整並去重結果。
    NewsAPI key 不存在時自動降級為僅用 GoogleNews。
    """

    name = "news_scraper"
    description = "新聞來源研究代理"

    def __init__(self) -> None:
        super().__init__()
        self._newsapi_key: str | None = None
        self._has_google: bool = False

    async def initialize(self) -> None:
        """初始化爬蟲設定"""
        try:
            scraper = NewsAPIScraper()
            self._newsapi_key = scraper.api_key
        except ValueError:
            logger.warning("NewsAPI key 未設定，將僅使用 Google News")
            self._newsapi_key = None

        self._has_google = True
        self._initialized = True

    async def run(
        self,
        input_data: NewsScraperInput,
        context: AgentContext | None = None,
    ) -> AgentResult[NewsScraperOutput]:
        """執行新聞抓取"""
        all_items: list[ContentItem] = []
        sources_used: list[str] = []
        errors: list[str] = []

        tasks = []
        for query in input_data.queries:
            tasks.extend(self._create_search_tasks(query, input_data))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
                logger.warning("爬蟲任務失敗: %s", result)
            elif isinstance(result, tuple):
                source_name, items = result
                all_items.extend(items)
                if source_name not in sources_used:
                    sources_used.append(source_name)

        # 依 URL 去重
        seen_urls: set[str] = set()
        unique_items: list[ContentItem] = []
        for item in all_items:
            url_str = str(item.url)
            if url_str not in seen_urls:
                seen_urls.add(url_str)
                unique_items.append(item)

        # 依 published_at 排序 (新的在前)
        unique_items.sort(
            key=lambda x: x.published_at or _MIN_DATETIME,
            reverse=True,
        )

        output = NewsScraperOutput(
            items=unique_items,
            total_count=len(unique_items),
            sources_used=sources_used,
            errors=errors,
        )
        return AgentResult(success=True, data=output)

    def _create_search_tasks(
        self,
        query: str,
        input_data: NewsScraperInput,
    ) -> list:
        """為單一查詢建立搜尋任務"""
        tasks = []

        if self._has_google:
            tasks.append(self._search_google_news(query, input_data))

        if self._newsapi_key:
            tasks.append(self._search_newsapi(query, input_data))

        return tasks

    async def _search_google_news(
        self,
        query: str,
        input_data: NewsScraperInput,
    ) -> tuple[str, list[ContentItem]]:
        """搜尋 Google News"""
        scraper = GoogleNewsScraper()
        async with scraper:
            items = await scraper.search(
                query=query,
                max_results=input_data.max_results_per_source,
                language=input_data.language,
            )
        return ("google_news", items)

    async def _search_newsapi(
        self,
        query: str,
        input_data: NewsScraperInput,
    ) -> tuple[str, list[ContentItem]]:
        """搜尋 NewsAPI"""
        lang_code = input_data.language.split("-")[0]  # "zh-TW" -> "zh"
        scraper = NewsAPIScraper(api_key=self._newsapi_key)
        async with scraper:
            items = await scraper.search(
                query=query,
                max_results=input_data.max_results_per_source,
                language=lang_code,
            )
        return ("newsapi", items)

    async def close(self) -> None:
        """關閉爬蟲（各任務自行管理 scraper 生命週期）"""
        pass
