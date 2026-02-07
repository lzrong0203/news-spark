"""社群媒體代理

協調 PTTScraper、ThreadsScraper、LinkedInScraper，並行搜尋並彙整結果。
"""

import asyncio
import logging

from pydantic import BaseModel, Field

from src.agents.base import AgentContext, AgentResult, BaseAgent
from src.models.content import ContentItem
from src.scrapers.linkedin import LinkedInScraper
from src.scrapers.ptt import PTTScraper
from src.scrapers.threads import ThreadsScraper

logger = logging.getLogger(__name__)


class SocialMediaInput(BaseModel):
    """社群媒體代理輸入"""

    queries: list[str] = Field(..., min_length=1, description="搜尋子查詢列表")
    platforms: list[str] = Field(
        default_factory=lambda: ["ptt", "threads"],
        description="要搜尋的平台",
    )
    linkedin_urls: list[str] = Field(
        default_factory=list,
        description="使用者提供的 LinkedIn URL",
    )
    language: str = Field(default="zh-TW", description="語言")
    max_results_per_source: int = Field(
        default=10, ge=1, le=50, description="每來源最大結果數"
    )
    ptt_boards: list[str] = Field(
        default_factory=lambda: ["Gossiping", "Stock", "Tech_Job"],
        description="PTT 看板列表",
    )


class SocialMediaOutput(BaseModel):
    """社群媒體代理輸出"""

    forum_items: list[ContentItem] = Field(
        default_factory=list, description="論壇內容 (PTT)"
    )
    social_items: list[ContentItem] = Field(
        default_factory=list, description="社群內容 (Threads + LinkedIn)"
    )
    total_count: int = Field(default=0, description="總筆數")
    sources_used: list[str] = Field(default_factory=list, description="使用的來源")
    errors: list[str] = Field(default_factory=list, description="錯誤訊息")


class SocialMediaAgent(BaseAgent[SocialMediaInput, SocialMediaOutput]):
    """社群媒體與論壇研究代理

    並行搜尋 PTT、Threads、LinkedIn 來源。
    各平台失敗不影響整體結果。
    """

    name = "social_media"
    description = "社群媒體與論壇研究代理"

    def __init__(self) -> None:
        super().__init__()

    async def run(
        self,
        input_data: SocialMediaInput,
        context: AgentContext | None = None,
    ) -> AgentResult[SocialMediaOutput]:
        """執行社群媒體抓取"""
        forum_items: list[ContentItem] = []
        social_items: list[ContentItem] = []
        sources_used: list[str] = []
        errors: list[str] = []

        tasks = []

        # PTT 任務
        if "ptt" in input_data.platforms:
            for query in input_data.queries:
                for board in input_data.ptt_boards:
                    tasks.append(
                        self._search_ptt(
                            query, board, input_data.max_results_per_source
                        )
                    )

        # Threads 任務
        if "threads" in input_data.platforms:
            for query in input_data.queries:
                tasks.append(
                    self._search_threads(query, input_data.max_results_per_source)
                )

        # LinkedIn 任務 (僅處理提供的 URL)
        if "linkedin" in input_data.platforms:
            for url in input_data.linkedin_urls:
                tasks.append(self._fetch_linkedin(url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
                logger.warning("社群抓取任務失敗: %s", result)
            elif isinstance(result, tuple):
                source_name, items, item_type = result
                if item_type == "forum":
                    forum_items.extend(items)
                else:
                    social_items.extend(items)
                if source_name not in sources_used:
                    sources_used.append(source_name)

        output = SocialMediaOutput(
            forum_items=forum_items,
            social_items=social_items,
            total_count=len(forum_items) + len(social_items),
            sources_used=sources_used,
            errors=errors,
        )
        return AgentResult(success=True, data=output)

    async def _search_ptt(
        self,
        query: str,
        board: str,
        max_results: int,
    ) -> tuple[str, list[ContentItem], str]:
        """搜尋 PTT 看板"""
        scraper = PTTScraper()
        try:
            async with scraper:
                items = await scraper.search(
                    query=query,
                    max_results=max_results,
                    board=board,
                )
            return (f"ptt:{board}", items, "forum")
        except Exception as e:
            logger.warning("PTT %s 搜尋失敗: %s", board, e)
            raise

    async def _search_threads(
        self,
        query: str,
        max_results: int,
    ) -> tuple[str, list[ContentItem], str]:
        """搜尋 Threads"""
        scraper = ThreadsScraper()
        try:
            async with scraper:
                items = await scraper.search(
                    query=query,
                    max_results=max_results,
                )
            return ("threads", items, "social")
        except Exception as e:
            logger.warning("Threads 搜尋失敗: %s", e)
            raise

    async def _fetch_linkedin(
        self,
        url: str,
    ) -> tuple[str, list[ContentItem], str]:
        """抓取 LinkedIn URL"""
        scraper = LinkedInScraper()
        try:
            async with scraper:
                item = await scraper.get_post(url)
            items = [item] if item else []
            return ("linkedin", items, "social")
        except Exception as e:
            logger.warning("LinkedIn 抓取失敗: %s", e)
            raise
