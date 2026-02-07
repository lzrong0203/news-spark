"""SocialMediaAgent 測試"""

from unittest.mock import AsyncMock, MagicMock, patch


from src.agents.social_media import SocialMediaAgent, SocialMediaInput
from src.models.content import ContentItem


def _make_item(title: str, url: str, source_type: str = "forum") -> ContentItem:
    return ContentItem(
        title=title,
        url=url,
        content="content",
        source_type=source_type,
        source_name="TestSource",
    )


class TestSocialMediaAgent:
    async def test_ptt_search(self):
        """PTT 搜尋"""
        ptt_items = [_make_item("PTT Post", "https://ptt.cc/test")]

        mock_scraper = MagicMock()
        mock_scraper.search = AsyncMock(return_value=ptt_items)
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)

        with patch("src.agents.social_media.PTTScraper", return_value=mock_scraper):
            agent = SocialMediaAgent()
            result = await agent.run(
                SocialMediaInput(
                    queries=["AI"],
                    platforms=["ptt"],
                    ptt_boards=["Gossiping"],
                )
            )

        assert result.success
        assert len(result.data.forum_items) == 1
        assert "ptt:Gossiping" in result.data.sources_used

    async def test_threads_search(self):
        """Threads 搜尋"""
        threads_items = [
            _make_item("Thread Post", "https://threads.net/test", "social")
        ]

        mock_scraper = MagicMock()
        mock_scraper.search = AsyncMock(return_value=threads_items)
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)

        with patch("src.agents.social_media.ThreadsScraper", return_value=mock_scraper):
            agent = SocialMediaAgent()
            result = await agent.run(
                SocialMediaInput(queries=["AI"], platforms=["threads"])
            )

        assert result.success
        assert len(result.data.social_items) == 1
        assert "threads" in result.data.sources_used

    async def test_linkedin_fetch(self):
        """LinkedIn URL 抓取"""
        linkedin_item = _make_item(
            "LinkedIn Post", "https://linkedin.com/posts/test", "social"
        )

        mock_scraper = MagicMock()
        mock_scraper.get_post = AsyncMock(return_value=linkedin_item)
        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.agents.social_media.LinkedInScraper", return_value=mock_scraper
        ):
            agent = SocialMediaAgent()
            result = await agent.run(
                SocialMediaInput(
                    queries=["AI"],
                    platforms=["linkedin"],
                    linkedin_urls=["https://linkedin.com/posts/test"],
                )
            )

        assert result.success
        assert len(result.data.social_items) == 1

    async def test_error_tolerance(self):
        """單一平台失敗不影響其他平台"""
        ptt_items = [_make_item("PTT Post", "https://ptt.cc/ok")]

        mock_ptt = MagicMock()
        mock_ptt.search = AsyncMock(return_value=ptt_items)
        mock_ptt.__aenter__ = AsyncMock(return_value=mock_ptt)
        mock_ptt.__aexit__ = AsyncMock(return_value=None)

        mock_threads = MagicMock()
        mock_threads.search = AsyncMock(side_effect=Exception("Threads down"))
        mock_threads.__aenter__ = AsyncMock(return_value=mock_threads)
        mock_threads.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("src.agents.social_media.PTTScraper", return_value=mock_ptt),
            patch("src.agents.social_media.ThreadsScraper", return_value=mock_threads),
        ):
            agent = SocialMediaAgent()
            result = await agent.run(
                SocialMediaInput(
                    queries=["AI"],
                    platforms=["ptt", "threads"],
                    ptt_boards=["Gossiping"],
                )
            )

        assert result.success
        assert len(result.data.forum_items) == 1
        assert len(result.data.errors) > 0

    async def test_empty_platforms(self):
        """空平台列表"""
        agent = SocialMediaAgent()
        result = await agent.run(SocialMediaInput(queries=["AI"], platforms=[]))

        assert result.success
        assert result.data.total_count == 0

    async def test_multiple_boards(self):
        """多看板搜尋"""
        items_g = [_make_item("Gossiping", "https://ptt.cc/g")]
        items_s = [_make_item("Stock", "https://ptt.cc/s")]

        call_count = 0

        def make_scraper():
            nonlocal call_count
            mock = MagicMock()

            async def search_side_effect(**kwargs):
                nonlocal call_count
                call_count += 1
                return items_g if call_count == 1 else items_s

            mock.search = AsyncMock(side_effect=search_side_effect)
            mock.__aenter__ = AsyncMock(return_value=mock)
            mock.__aexit__ = AsyncMock(return_value=None)
            return mock

        with patch(
            "src.agents.social_media.PTTScraper",
            side_effect=lambda: make_scraper(),
        ):
            agent = SocialMediaAgent()
            result = await agent.run(
                SocialMediaInput(
                    queries=["AI"],
                    platforms=["ptt"],
                    ptt_boards=["Gossiping", "Stock"],
                )
            )

        assert result.success
        assert result.data.total_count == 2
