"""LinkedIn 爬蟲模組

抓取 LinkedIn 公開內容。

注意事項:
- LinkedIn 反爬機制嚴格
- 大部分內容需要登入
- 建議主要用於處理用戶提供的 URL
- 過度抓取可能導致 IP 被封鎖
"""

import logging
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.models.content import ContentItem
from src.scrapers.base import BaseScraper
from src.utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

LINKEDIN_BASE_URL = "https://www.linkedin.com"


class LinkedInScraper(BaseScraper):
    """LinkedIn 爬蟲

    由於 LinkedIn 的反爬機制，此爬蟲主要用於:
    1. 處理用戶手動提供的 LinkedIn URL
    2. 抓取公開可見的內容
    3. 公司頁面的公開資訊

    建議使用方式:
    - 用戶輸入特定 LinkedIn 文章 URL
    - 系統抓取該文章內容進行分析
    """

    name = "linkedin"
    source_type = "social"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs: Any,
    ) -> list[ContentItem]:
        """搜尋 LinkedIn 內容

        Args:
            query: 搜尋關鍵字或 LinkedIn URL
            max_results: 最大結果數

        Returns:
            ContentItem 列表

        Note:
            LinkedIn 不允許未認證的搜尋。
            如果 query 是 URL，會嘗試直接抓取該頁面。
        """
        await rate_limit("linkedin")

        # 檢查是否為 LinkedIn URL
        if self._is_linkedin_url(query):
            post = await self.get_post(query)
            return [post] if post else []

        # LinkedIn 搜尋需要認證，返回空結果
        # 可以考慮整合 LinkedIn API (需要 OAuth)
        return []

    async def get_post(self, url: str) -> ContentItem | None:
        """取得 LinkedIn 貼文/文章內容

        Args:
            url: LinkedIn 貼文或文章 URL

        Returns:
            ContentItem 或 None
        """
        await rate_limit("linkedin")

        try:
            response = await self._fetch(url)
            return self._parse_linkedin_page(response.text, url)
        except Exception:
            logger.warning("LinkedIn 貼文抓取失敗: %s", url, exc_info=True)
            return None

    async def get_company_posts(
        self,
        company_url: str,
        max_results: int = 10,
    ) -> list[ContentItem]:
        """取得公司頁面貼文

        Args:
            company_url: 公司 LinkedIn 頁面 URL
            max_results: 最大結果數

        Returns:
            ContentItem 列表

        Note:
            此功能可能需要登入才能正常運作。
        """
        await rate_limit("linkedin")

        try:
            response = await self._fetch(company_url)
            return self._parse_company_page(response.text, company_url, max_results)
        except Exception:
            logger.warning("LinkedIn 公司頁面抓取失敗: %s", company_url, exc_info=True)
            return []

    def _is_linkedin_url(self, text: str) -> bool:
        """檢查是否為 LinkedIn URL"""
        try:
            parsed = urlparse(text)
            return parsed.netloc in ["www.linkedin.com", "linkedin.com"]
        except Exception:
            logger.debug("LinkedIn URL 解析失敗: %s", text, exc_info=True)
            return False

    def _parse_linkedin_page(self, html: str, url: str) -> ContentItem | None:
        """解析 LinkedIn 頁面內容"""
        soup = BeautifulSoup(html, "html.parser")

        # 嘗試多種選擇器來提取內容
        content = ""
        title = ""
        author = ""

        # 文章頁面
        article = soup.select_one("article")
        if article:
            title_elem = article.select_one("h1")
            title = title_elem.get_text(strip=True) if title_elem else ""

            content_elem = article.select_one(".article-content")
            if content_elem:
                content = content_elem.get_text(strip=True)

            author_elem = soup.select_one(".author-info__name")
            if author_elem:
                author = author_elem.get_text(strip=True)

        # 貼文頁面
        if not content:
            # 嘗試找到貼文內容
            post_content = soup.select_one(".feed-shared-update-v2__description")
            if post_content:
                content = post_content.get_text(strip=True)
                title = content[:100] + "..." if len(content) > 100 else content

            author_elem = soup.select_one(".update-components-actor__name")
            if author_elem:
                author = author_elem.get_text(strip=True)

        # 從 meta 標籤提取
        if not title:
            og_title = soup.select_one('meta[property="og:title"]')
            if og_title:
                title = og_title.get("content", "")

        if not content:
            og_desc = soup.select_one('meta[property="og:description"]')
            if og_desc:
                content = og_desc.get("content", "")

        # 圖片
        image_url = None
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image:
            image_url = og_image.get("content")

        if not title and not content:
            return None

        return ContentItem(
            title=title or content[:100],
            url=url,
            content=content,
            source_type="social",
            source_name="LinkedIn",
            author=author or None,
            image_url=image_url,
            language="zh-TW",
        )

    def _parse_company_page(
        self,
        html: str,
        url: str,
        max_results: int,
    ) -> list[ContentItem]:
        """解析公司頁面"""
        soup = BeautifulSoup(html, "html.parser")
        results: list[ContentItem] = []

        # 公司名稱
        company_name = ""
        name_elem = soup.select_one(".org-top-card-summary__title")
        if name_elem:
            company_name = name_elem.get_text(strip=True)

        # 嘗試找到貼文
        posts = soup.select(".feed-shared-update-v2")
        for post in posts[:max_results]:
            content_elem = post.select_one(".feed-shared-update-v2__description")
            if not content_elem:
                continue

            content = content_elem.get_text(strip=True)
            if not content:
                continue

            results.append(
                ContentItem(
                    title=content[:100] + "..." if len(content) > 100 else content,
                    url=url,
                    content=content,
                    source_type="social",
                    source_name=f"LinkedIn:{company_name}",
                    language="zh-TW",
                )
            )

        return results


class LinkedInURLHandler:
    """LinkedIn URL 處理器

    專門處理用戶提供的 LinkedIn URL。
    提供更友善的錯誤處理和提示。
    """

    def __init__(self) -> None:
        self.scraper = LinkedInScraper()

    async def process_url(self, url: str) -> ContentItem | None:
        """處理 LinkedIn URL

        Args:
            url: LinkedIn URL

        Returns:
            ContentItem 或 None

        Raises:
            ValueError: 如果 URL 無效
        """
        if not self.scraper._is_linkedin_url(url):
            raise ValueError(f"Invalid LinkedIn URL: {url}")

        return await self.scraper.get_post(url)

    async def close(self) -> None:
        """關閉爬蟲"""
        await self.scraper.close()
