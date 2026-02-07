"""NewsScraperAgent 測試"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.news_scraper import NewsScraperAgent, NewsScraperInput
from src.models.content import ContentItem


def _make_item(title: str, url: str, published_at=None) -> ContentItem:
    return ContentItem(
        title=title,
        url=url,
        content="content",
        source_type="news",
        source_name="TestSource",
        published_at=published_at,
    )


def _mock_scraper(items=None, side_effect=None):
    """建立 mock scraper，支援 async context manager"""
    scraper = MagicMock()
    if side_effect:
        scraper.search = AsyncMock(side_effect=side_effect)
    else:
        scraper.search = AsyncMock(return_value=items or [])
    scraper.__aenter__ = AsyncMock(return_value=scraper)
    scraper.__aexit__ = AsyncMock(return_value=None)
    return scraper


class TestNewsScraperAgent:
    async def test_search_with_google_news_only(self):
        """NewsAPI 不可用時，僅用 GoogleNews"""
        items = [
            _make_item("News 1", "https://example.com/1", datetime(2025, 1, 30, tzinfo=timezone.utc)),
            _make_item("News 2", "https://example.com/2", datetime(2025, 1, 29, tzinfo=timezone.utc)),
        ]

        agent = NewsScraperAgent()
        agent._initialized = True
        agent._has_google = True
        agent._newsapi_key = None

        with patch("src.agents.news_scraper.GoogleNewsScraper", return_value=_mock_scraper(items)):
            result = await agent.run(NewsScraperInput(queries=["AI"]))

        assert result.success
        assert result.data.total_count == 2
        assert "google_news" in result.data.sources_used

    async def test_deduplication_by_url(self):
        """相同 URL 應被去重"""
        item1 = _make_item("News 1", "https://example.com/same", datetime(2025, 1, 30, tzinfo=timezone.utc))
        item2 = _make_item("News 1 dup", "https://example.com/same", datetime(2025, 1, 29, tzinfo=timezone.utc))
        item3 = _make_item("News 2", "https://example.com/other", datetime(2025, 1, 28, tzinfo=timezone.utc))

        agent = NewsScraperAgent()
        agent._initialized = True
        agent._has_google = True
        agent._newsapi_key = None

        with patch("src.agents.news_scraper.GoogleNewsScraper", return_value=_mock_scraper([item1, item2, item3])):
            result = await agent.run(NewsScraperInput(queries=["AI"]))

        assert result.data.total_count == 2  # 去重後

    async def test_sort_by_published_at(self):
        """結果應依 published_at 降序排列"""
        old = _make_item("Old", "https://example.com/old", datetime(2025, 1, 1, tzinfo=timezone.utc))
        new = _make_item("New", "https://example.com/new", datetime(2025, 1, 30, tzinfo=timezone.utc))

        agent = NewsScraperAgent()
        agent._initialized = True
        agent._has_google = True
        agent._newsapi_key = None

        with patch("src.agents.news_scraper.GoogleNewsScraper", return_value=_mock_scraper([old, new])):
            result = await agent.run(NewsScraperInput(queries=["AI"]))

        assert result.data.items[0].title == "New"
        assert result.data.items[1].title == "Old"

    async def test_exception_handling(self):
        """爬蟲錯誤應被記錄但不中斷流程"""
        agent = NewsScraperAgent()
        agent._initialized = True
        agent._has_google = True
        agent._newsapi_key = None

        with patch(
            "src.agents.news_scraper.GoogleNewsScraper",
            return_value=_mock_scraper(side_effect=Exception("Network error")),
        ):
            result = await agent.run(NewsScraperInput(queries=["AI"]))

        assert result.success
        assert result.data.total_count == 0
        assert len(result.data.errors) > 0

    async def test_both_sources(self):
        """同時使用 GoogleNews 和 NewsAPI"""
        google_items = [_make_item("Google", "https://example.com/g")]
        newsapi_items = [_make_item("NewsAPI", "https://example.com/n")]

        agent = NewsScraperAgent()
        agent._initialized = True
        agent._has_google = True
        agent._newsapi_key = "test-key"

        with (
            patch("src.agents.news_scraper.GoogleNewsScraper", return_value=_mock_scraper(google_items)),
            patch("src.agents.news_scraper.NewsAPIScraper", return_value=_mock_scraper(newsapi_items)),
        ):
            result = await agent.run(NewsScraperInput(queries=["AI"]))

        assert result.success
        assert result.data.total_count == 2
        assert len(result.data.sources_used) == 2

    async def test_multiple_queries(self):
        """多個查詢應各自搜尋"""
        items_q1 = [_make_item("Q1", "https://example.com/q1")]
        items_q2 = [_make_item("Q2", "https://example.com/q2")]
        call_count = 0

        async def mock_search(**kwargs):
            nonlocal call_count
            call_count += 1
            return items_q1 if call_count <= 1 else items_q2

        def make_scraper():
            return _mock_scraper(side_effect=mock_search)

        agent = NewsScraperAgent()
        agent._initialized = True
        agent._has_google = True
        agent._newsapi_key = None

        with patch("src.agents.news_scraper.GoogleNewsScraper", side_effect=lambda: make_scraper()):
            result = await agent.run(NewsScraperInput(queries=["AI", "機器學習"]))

        assert result.data.total_count == 2

    async def test_close(self):
        """close() 應正常完成（各任務自行管理 scraper 生命週期）"""
        agent = NewsScraperAgent()
        await agent.close()  # 應為 no-op，不拋錯
