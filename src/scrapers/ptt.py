"""PTT 論壇爬蟲模組

爬取 PTT (批踢踢實業坊) 論壇內容。
使用 PTT Web 版本進行爬取。
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.models.content import ContentItem, EngagementMetrics
from src.scrapers.base import BaseScraper
from src.utils.rate_limiter import rate_limit

PTT_WEB_BASE = "https://www.ptt.cc"

_TAIPEI_TZ = timezone(timedelta(hours=8))

# 熱門看板列表
POPULAR_BOARDS = {
    "gossiping": "八卦版",
    "stock": "股票版",
    "tech_job": "科技工作版",
    "movie": "電影版",
    "hatepolitics": "政黑版",
    "c_chat": "希洽版",
    "lifeismoney": "省錢版",
    "car": "汽車版",
    "home-sale": "房屋版",
    "japan_travel": "日旅版",
}


class PTTScraper(BaseScraper):
    """PTT 論壇爬蟲

    支援:
    - 看板文章列表
    - 文章內容抓取
    - 熱門文章篩選
    """

    name = "ptt"
    source_type = "forum"

    def __init__(self, timeout: float = 30.0) -> None:
        super().__init__(timeout=timeout)
        # PTT 需要 cookie 同意成人內容
        self._cookies = {"over18": "1"}

    async def _fetch(self, url: str, **kwargs: Any) -> Any:
        """覆寫 fetch 加入 cookies (保留 SSRF 驗證與重試)"""
        kwargs.setdefault("cookies", self._cookies)
        return await super()._fetch(url, **kwargs)

    async def search(
        self,
        query: str,
        max_results: int = 10,
        board: str = "Gossiping",
        **kwargs: Any,
    ) -> list[ContentItem]:
        """搜尋 PTT 文章

        Args:
            query: 搜尋關鍵字
            max_results: 最大結果數
            board: 看板名稱

        Returns:
            ContentItem 列表
        """
        # PTT 沒有好用的搜尋 API，所以先抓最新文章再篩選
        articles = await self.get_board_articles(board, pages=3)

        # 篩選包含任一關鍵字的文章（拆詞匹配）
        keywords = [kw for kw in query.lower().split() if kw]
        if not keywords:
            return []
        filtered = [
            article
            for article in articles
            if any(
                kw in article.title.lower() or kw in article.content.lower()
                for kw in keywords
            )
        ]

        return filtered[:max_results]

    async def get_board_articles(
        self,
        board: str,
        pages: int = 1,
        **kwargs: Any,
    ) -> list[ContentItem]:
        """取得看板文章列表

        Args:
            board: 看板名稱
            pages: 抓取頁數

        Returns:
            ContentItem 列表
        """
        await rate_limit("ptt")

        if not re.match(r"^[A-Za-z0-9_-]+$", board):
            raise ValueError(f"無效的看板名稱: {board}")

        results: list[ContentItem] = []
        url = f"{PTT_WEB_BASE}/bbs/{board}/index.html"

        for _ in range(pages):
            response = await self._fetch(url)
            soup = BeautifulSoup(response.text, "html.parser")

            # 解析文章列表
            articles = soup.select("div.r-ent")
            for article in articles:
                item = self._parse_article_entry(article, board)
                if item:
                    results.append(item)

            # 取得上一頁連結 (避免使用已棄用的 :contains)
            prev_links = soup.select("a.btn.wide")
            prev_link = next(
                (a for a in prev_links if "上頁" in a.text),
                None,
            )

            if prev_link and prev_link.get("href"):
                url = urljoin(PTT_WEB_BASE, prev_link["href"])
            else:
                break

        return results

    async def get_article_content(self, url: str) -> ContentItem | None:
        """取得文章完整內容

        Args:
            url: 文章 URL

        Returns:
            ContentItem 或 None
        """
        await rate_limit("ptt")

        response = await self._fetch(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # 取得文章元數據
        meta_lines = soup.select("div.article-metaline")
        author = ""
        title = ""
        date_str = ""

        for meta in meta_lines:
            tag = meta.select_one("span.article-meta-tag")
            value = meta.select_one("span.article-meta-value")
            if tag and value:
                tag_text = tag.text.strip()
                if tag_text == "作者":
                    author = value.text.strip()
                elif tag_text == "標題":
                    title = value.text.strip()
                elif tag_text == "時間":
                    date_str = value.text.strip()

        # 取得文章內容
        main_content = soup.select_one("div#main-content")
        if not main_content:
            return None

        # 移除元數據和推文，只保留正文
        content_text = main_content.text
        # 嘗試找到正文開始位置（在最後一個 metaline 之後）
        lines = content_text.split("\n")
        content_lines = []
        in_content = False
        for line in lines:
            if "時間" in line and not in_content:
                in_content = True
                continue
            if in_content:
                # 遇到推文區域停止
                if (
                    line.startswith("※")
                    or line.startswith("→")
                    or line.startswith("推")
                ):
                    break
                content_lines.append(line)

        content = "\n".join(content_lines).strip()

        # 計算推文數
        pushes = soup.select("div.push")
        push_count = len([p for p in pushes if "推" in p.text])
        # boo_count 可用於計算淨推文數，但目前僅記錄推數

        # 解析日期
        published_at = self._parse_date(date_str)

        return ContentItem(
            title=title,
            url=url,
            content=content[:2000],  # 限制內容長度
            source_type="forum",
            source_name="PTT",
            author=author.split("(")[0].strip() if author else None,
            published_at=published_at,
            language="zh-TW",
            region="TW",
            engagement=EngagementMetrics(
                likes=push_count,
                comments=len(pushes),
            ),
        )

    def _parse_article_entry(
        self,
        article: BeautifulSoup,
        board: str,
    ) -> ContentItem | None:
        """解析文章列表項目"""
        title_elem = article.select_one("div.title a")
        if not title_elem:
            return None

        title = title_elem.text.strip()
        href = title_elem.get("href", "")
        url = urljoin(PTT_WEB_BASE, href) if href else ""

        # 推文數
        nrec = article.select_one("div.nrec")
        push_count = 0
        if nrec:
            nrec_text = nrec.text.strip()
            if nrec_text == "爆":
                push_count = 100
            elif nrec_text.startswith("X"):
                push_count = -10
            elif nrec_text.isdigit():
                push_count = int(nrec_text)

        # 作者
        author_elem = article.select_one("div.author")
        author = author_elem.text.strip() if author_elem else None

        # 日期
        date_elem = article.select_one("div.date")
        date_str = date_elem.text.strip() if date_elem else ""

        return ContentItem(
            title=title,
            url=url,
            content="",  # 需要另外抓取完整內容
            source_type="forum",
            source_name=f"PTT:{board}",
            author=author,
            language="zh-TW",
            region="TW",
            engagement=EngagementMetrics(likes=max(0, push_count)),
            raw_data={"board": board, "date": date_str},
        )

    def _parse_date(self, date_str: str) -> datetime | None:
        """解析 PTT 日期格式"""
        # PTT 日期格式: "Mon Jan  1 12:34:56 2024"
        try:
            return datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y").replace(tzinfo=_TAIPEI_TZ)
        except ValueError:
            return None

    async def get_hot_articles(
        self,
        board: str = "Gossiping",
        min_pushes: int = 50,
        pages: int = 3,
    ) -> list[ContentItem]:
        """取得熱門文章 (依推文數篩選)

        Args:
            board: 看板名稱
            min_pushes: 最低推文數
            pages: 抓取頁數

        Returns:
            ContentItem 列表
        """
        articles = await self.get_board_articles(board, pages)

        # 篩選熱門文章
        hot = [a for a in articles if a.engagement and a.engagement.likes >= min_pushes]

        # 依推文數排序
        hot.sort(key=lambda x: x.engagement.likes if x.engagement else 0, reverse=True)

        return hot
