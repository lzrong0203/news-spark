"""NewsAPIScraper 測試"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scrapers.news_api import NewsAPIScraper


class TestNewsAPIScraper:
    def test_init_requires_api_key(self):
        with patch("src.scrapers.news_api.settings") as mock_settings:
            mock_settings.get_newsapi_key.return_value = None
            with pytest.raises(ValueError, match="NewsAPI key is required"):
                NewsAPIScraper()

    def test_init_with_explicit_key(self):
        scraper = NewsAPIScraper(api_key="test-key")
        assert scraper.api_key == "test-key"

    @patch("src.scrapers.news_api.rate_limit", new_callable=AsyncMock)
    async def test_search(self, mock_rate_limit):
        scraper = NewsAPIScraper(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "AI News",
                    "url": "https://example.com/ai",
                    "description": "AI is evolving",
                    "source": {"name": "TestSource"},
                    "publishedAt": "2025-01-30T10:00:00Z",
                    "author": "Author",
                },
            ],
        }
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.search("AI")

        assert len(results) == 1
        assert results[0].title == "AI News"
        assert results[0].source_type == "news"
        assert "NewsAPI:" in results[0].source_name

    @patch("src.scrapers.news_api.rate_limit", new_callable=AsyncMock)
    async def test_search_api_error(self, mock_rate_limit):
        scraper = NewsAPIScraper(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "error",
            "message": "API key invalid",
        }
        scraper._fetch = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="NewsAPI error"):
            await scraper.search("AI")

    @patch("src.scrapers.news_api.rate_limit", new_callable=AsyncMock)
    async def test_search_with_optional_params(self, mock_rate_limit):
        scraper = NewsAPIScraper(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "articles": []}
        scraper._fetch = AsyncMock(return_value=mock_response)

        await scraper.search(
            "AI",
            from_date="2025-01-01",
            to_date="2025-01-30",
            domains="example.com",
        )
        scraper._fetch.assert_awaited_once()

    @patch("src.scrapers.news_api.rate_limit", new_callable=AsyncMock)
    async def test_get_top_headlines(self, mock_rate_limit):
        scraper = NewsAPIScraper(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Headline",
                    "url": "https://example.com/hl",
                    "description": "desc",
                    "source": {"name": "BBC"},
                    "publishedAt": "2025-01-30T10:00:00Z",
                },
            ],
        }
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.get_top_headlines(category="technology")
        assert len(results) == 1

    def test_parse_articles_skips_removed(self):
        scraper = NewsAPIScraper(api_key="test-key")
        articles = [
            {"title": "[Removed]", "url": "https://example.com/removed"},
            {
                "title": "Valid",
                "url": "https://example.com/valid",
                "source": {"name": "S"},
            },
        ]
        results = scraper._parse_articles(articles)
        assert len(results) == 1
        assert results[0].title == "Valid"

    def test_parse_articles_invalid_date(self):
        scraper = NewsAPIScraper(api_key="test-key")
        articles = [
            {
                "title": "Bad Date",
                "url": "https://example.com/bd",
                "publishedAt": "not-a-date",
                "source": {"name": "S"},
            },
        ]
        results = scraper._parse_articles(articles)
        assert len(results) == 1
        assert results[0].published_at is None
