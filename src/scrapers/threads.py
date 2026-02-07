"""Threads 爬蟲模組

抓取 Threads (Meta) 社群平台內容。
由於 Threads 沒有公開 API，使用網頁爬取方式。
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from src.models.content import ContentItem, EngagementMetrics
from src.scrapers.base import BaseScraper
from src.utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

THREADS_BASE_URL = "https://www.threads.net"


class ThreadsScraper(BaseScraper):
    """Threads 爬蟲

    注意事項:
    - Threads 反爬較嚴格，建議使用較低的請求頻率
    - 部分內容需要登入才能查看
    - 建議主要用於查看公開帳號的貼文
    """

    name = "threads"
    source_type = "social"

    def __init__(self, timeout: float = 30.0) -> None:
        super().__init__(timeout=timeout)

    async def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs: Any,
    ) -> list[ContentItem]:
        """搜尋 Threads 貼文

        Args:
            query: 搜尋關鍵字 (可以是 hashtag 或用戶名)
            max_results: 最大結果數

        Returns:
            ContentItem 列表

        Note:
            Threads 目前沒有公開的搜尋 API，
            此方法嘗試透過 hashtag 或用戶頁面抓取。
        """
        await rate_limit("threads")

        results: list[ContentItem] = []

        # 如果是 hashtag 格式
        if query.startswith("#"):
            tag = query[1:]
            results = await self._search_by_tag(tag, max_results)
        # 如果是用戶名格式
        elif query.startswith("@"):
            username = query[1:]
            results = await self.get_user_posts(username, max_results)
        else:
            # 嘗試當作 hashtag 搜尋
            results = await self._search_by_tag(query, max_results)

        return results[:max_results]

    async def _search_by_tag(
        self,
        tag: str,
        max_results: int = 10,
    ) -> list[ContentItem]:
        """透過 hashtag 搜尋

        注意: Threads 的 hashtag 頁面可能需要登入
        """
        try:
            url = f"{THREADS_BASE_URL}/search?q={tag}&serp_type=default"
            response = await self._fetch(url)

            # 嘗試從頁面 JSON 提取數據
            return self._extract_posts_from_html(response.text, f"search:{tag}")
        except Exception:
            logger.warning("Threads 標籤搜尋失敗: %s", tag, exc_info=True)
            # Threads 可能阻擋未登入的搜尋請求
            return []

    async def get_user_posts(
        self,
        username: str,
        max_results: int = 10,
    ) -> list[ContentItem]:
        """取得用戶貼文

        Args:
            username: 用戶名稱 (不含 @)
            max_results: 最大結果數

        Returns:
            ContentItem 列表
        """
        await rate_limit("threads")

        try:
            url = f"{THREADS_BASE_URL}/@{username}"
            response = await self._fetch(url)

            return self._extract_posts_from_html(
                response.text,
                username,
                max_results,
            )
        except Exception:
            logger.warning("Threads 用戶貼文抓取失敗: %s", username, exc_info=True)
            return []

    async def get_post(self, post_url: str) -> ContentItem | None:
        """取得單一貼文內容

        Args:
            post_url: 貼文 URL

        Returns:
            ContentItem 或 None
        """
        await rate_limit("threads")

        try:
            response = await self._fetch(post_url)
            posts = self._extract_posts_from_html(response.text, "single", 1)
            return posts[0] if posts else None
        except Exception:
            logger.warning("Threads 貼文抓取失敗: %s", post_url, exc_info=True)
            return None

    def _extract_posts_from_html(
        self,
        html: str,
        source_context: str,
        max_results: int = 10,
    ) -> list[ContentItem]:
        """從 HTML 中提取貼文資料

        Threads 的資料通常嵌入在 script 標籤的 JSON 中。
        """
        results: list[ContentItem] = []
        soup = BeautifulSoup(html, "html.parser")

        # 方法 1: 嘗試從 script 標籤提取 JSON 資料
        scripts = soup.find_all("script", type="application/json")
        for script in scripts:
            try:
                data = json.loads(script.string or "{}")
                posts = self._find_posts_in_json(data)
                for post in posts[:max_results]:
                    item = self._json_to_content_item(post, source_context)
                    if item:
                        results.append(item)
            except (json.JSONDecodeError, TypeError):
                logger.debug("Threads JSON 解析失敗，跳過此 script 標籤", exc_info=True)
                continue

        # 方法 2: 如果 JSON 解析失敗，嘗試從 HTML 結構提取
        if not results:
            # 尋找可能的貼文容器
            post_containers = soup.select("[data-pressable-container='true']")
            for container in post_containers[:max_results]:
                item = self._html_to_content_item(container, source_context)
                if item:
                    results.append(item)

        return results

    def _find_posts_in_json(self, data: Any, depth: int = 0) -> list[dict]:
        """遞歸搜尋 JSON 中的貼文資料"""
        if depth > 10:  # 防止無限遞歸
            return []

        posts = []

        if isinstance(data, dict):
            # 檢查是否為貼文物件
            if "text" in data and ("user" in data or "author" in data):
                posts.append(data)

            # 遞歸搜尋
            for value in data.values():
                posts.extend(self._find_posts_in_json(value, depth + 1))

        elif isinstance(data, list):
            for item in data:
                posts.extend(self._find_posts_in_json(item, depth + 1))

        return posts

    def _json_to_content_item(
        self,
        post: dict,
        source_context: str,
    ) -> ContentItem | None:
        """將 JSON 貼文資料轉換為 ContentItem"""
        try:
            text = post.get("text", "") or post.get("caption", "")
            if not text:
                return None

            user = post.get("user", {}) or post.get("author", {})
            username = user.get("username", "unknown")

            # 互動數據
            likes = post.get("like_count", 0) or post.get("likes", {}).get("count", 0)
            comments = post.get("reply_count", 0) or post.get("comments", {}).get(
                "count", 0
            )
            shares = post.get("repost_count", 0) or post.get("shares", {}).get(
                "count", 0
            )

            # 時間
            timestamp = post.get("taken_at") or post.get("created_at")
            published_at = None
            if timestamp:
                if isinstance(timestamp, (int, float)):
                    published_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                elif isinstance(timestamp, str):
                    try:
                        published_at = datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

            post_id = post.get("id", "") or post.get("pk", "")
            url = f"{THREADS_BASE_URL}/@{username}/post/{post_id}" if post_id else ""

            return ContentItem(
                title=text[:100] + "..." if len(text) > 100 else text,
                url=url,
                content=text,
                source_type="social",
                source_name=f"Threads:@{username}",
                author=username,
                author_url=f"{THREADS_BASE_URL}/@{username}",
                published_at=published_at,
                engagement=EngagementMetrics(
                    likes=likes,
                    comments=comments,
                    shares=shares,
                ),
                language="zh-TW",
                raw_data=post,
            )
        except Exception:
            logger.debug("Threads JSON 貼文解析失敗", exc_info=True)
            return None

    def _html_to_content_item(
        self,
        container: BeautifulSoup,
        source_context: str,
    ) -> ContentItem | None:
        """從 HTML 容器提取貼文資料 (備用方法)"""
        try:
            # 嘗試找到文字內容
            text_elem = container.select_one("[dir='auto']")
            if not text_elem:
                return None

            text = text_elem.get_text(strip=True)
            if not text:
                return None

            return ContentItem(
                title=text[:100] + "..." if len(text) > 100 else text,
                url="",
                content=text,
                source_type="social",
                source_name=f"Threads:{source_context}",
                language="zh-TW",
            )
        except Exception:
            logger.debug("Threads HTML 貼文解析失敗", exc_info=True)
            return None
