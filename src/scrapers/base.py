"""爬蟲基類模組

定義所有爬蟲的共同介面和基礎功能。
"""

import ipaddress
import logging
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.models.content import ContentItem

logger = logging.getLogger(__name__)

# 私有 IP 網段 (SSRF 防護)
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _validate_url(url: str) -> None:
    """驗證 URL 安全性，防止 SSRF 攻擊

    Args:
        url: 要驗證的 URL

    Raises:
        ValueError: URL 不安全
    """
    parsed = urlparse(url)

    # 僅允許 HTTP/HTTPS 協議
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"不允許的 URL 協議: {parsed.scheme}")

    if not parsed.hostname:
        raise ValueError("URL 缺少主機名稱")

    # 檢查是否為私有 IP
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        for network in _PRIVATE_NETWORKS:
            if ip in network:
                raise ValueError(f"不允許存取私有網路位址: {parsed.hostname}")
    except ValueError as e:
        if "不允許" in str(e):
            raise
        # 非 IP 格式 (域名)，檢查常見內部域名
        hostname_lower = parsed.hostname.lower()
        if hostname_lower in ("localhost", "localhost.localdomain"):
            raise ValueError(f"不允許存取內部主機: {parsed.hostname}")


class BaseScraper(ABC):
    """爬蟲基類

    所有資料來源爬蟲都應繼承此類別並實作 search 方法。
    """

    name: str = "base_scraper"
    source_type: str = "web"  # news, social, forum, web

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BaseScraper":
        """非同步上下文管理器進入"""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """非同步上下文管理器離開"""
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """確保 HTTP 客戶端存在"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                },
            )
        return self._client

    async def close(self) -> None:
        """關閉 HTTP 客戶端"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _fetch(self, url: str, **kwargs: Any) -> httpx.Response:
        """發送 HTTP GET 請求 (帶重試)"""
        _validate_url(url)
        client = await self._ensure_client()
        response = await client.get(url, **kwargs)
        response.raise_for_status()
        return response

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _post(self, url: str, **kwargs: Any) -> httpx.Response:
        """發送 HTTP POST 請求 (帶重試)"""
        _validate_url(url)
        client = await self._ensure_client()
        response = await client.post(url, **kwargs)
        response.raise_for_status()
        return response

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs: Any,
    ) -> list[ContentItem]:
        """搜尋內容

        Args:
            query: 搜尋關鍵字
            max_results: 最大結果數
            **kwargs: 額外參數

        Returns:
            ContentItem 列表
        """
        ...

    async def fetch_content(self, url: str) -> str:
        """抓取網頁內容

        Args:
            url: 網頁 URL

        Returns:
            網頁 HTML 內容
        """
        response = await self._fetch(url)
        return response.text
