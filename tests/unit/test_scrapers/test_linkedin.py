"""LinkedInScraper 測試"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scrapers.linkedin import LinkedInScraper, LinkedInURLHandler


ARTICLE_HTML = """
<html>
<head>
    <meta property="og:title" content="LinkedIn Article Title"/>
    <meta property="og:description" content="Article description"/>
    <meta property="og:image" content="https://example.com/img.jpg"/>
</head>
<body>
    <article>
        <h1>LinkedIn Article Title</h1>
        <div class="article-content">This is the full article content about AI.</div>
        <div class="author-info__name">Author Name</div>
    </article>
</body>
</html>
"""

POST_HTML = """
<html>
<head>
    <meta property="og:title" content="Post Title"/>
</head>
<body>
    <div class="feed-shared-update-v2__description">This is a LinkedIn post about AI trends.</div>
    <div class="update-components-actor__name">Post Author</div>
</body>
</html>
"""

OG_ONLY_HTML = """
<html>
<head>
    <meta property="og:title" content="OG Title"/>
    <meta property="og:description" content="OG Description"/>
</head>
<body></body>
</html>
"""

EMPTY_HTML = """
<html><head></head><body></body></html>
"""

COMPANY_HTML = """
<html>
<body>
    <div class="org-top-card-summary__title">Test Company</div>
    <div class="feed-shared-update-v2">
        <div class="feed-shared-update-v2__description">Company post content here.</div>
    </div>
    <div class="feed-shared-update-v2">
        <div class="feed-shared-update-v2__description">Another company post.</div>
    </div>
</body>
</html>
"""


class TestLinkedInScraper:
    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_search_with_url(self, mock_rate_limit):
        scraper = LinkedInScraper()

        mock_response = MagicMock()
        mock_response.text = ARTICLE_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.search("https://www.linkedin.com/posts/test")
        assert len(results) == 1

    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_search_without_url(self, mock_rate_limit):
        scraper = LinkedInScraper()
        results = await scraper.search("AI news")
        assert results == []

    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_get_post_article(self, mock_rate_limit):
        scraper = LinkedInScraper()

        mock_response = MagicMock()
        mock_response.text = ARTICLE_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        result = await scraper.get_post("https://www.linkedin.com/pulse/test")
        assert result is not None
        assert result.title == "LinkedIn Article Title"
        assert "full article content" in result.content
        assert result.author == "Author Name"

    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_get_post_feed(self, mock_rate_limit):
        scraper = LinkedInScraper()

        mock_response = MagicMock()
        mock_response.text = POST_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        result = await scraper.get_post("https://www.linkedin.com/posts/test")
        assert result is not None
        assert "LinkedIn post about AI" in result.content

    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_get_post_og_fallback(self, mock_rate_limit):
        scraper = LinkedInScraper()

        mock_response = MagicMock()
        mock_response.text = OG_ONLY_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        result = await scraper.get_post("https://www.linkedin.com/posts/test")
        assert result is not None
        assert result.title == "OG Title"
        assert result.content == "OG Description"

    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_get_post_empty_page(self, mock_rate_limit):
        scraper = LinkedInScraper()

        mock_response = MagicMock()
        mock_response.text = EMPTY_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        result = await scraper.get_post("https://www.linkedin.com/posts/test")
        assert result is None

    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_get_post_fetch_error(self, mock_rate_limit):
        scraper = LinkedInScraper()
        scraper._fetch = AsyncMock(side_effect=Exception("Network error"))

        result = await scraper.get_post("https://www.linkedin.com/posts/test")
        assert result is None

    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_get_company_posts(self, mock_rate_limit):
        scraper = LinkedInScraper()

        mock_response = MagicMock()
        mock_response.text = COMPANY_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.get_company_posts(
            "https://www.linkedin.com/company/test"
        )
        assert len(results) == 2
        assert "LinkedIn:Test Company" in results[0].source_name

    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_get_company_posts_error(self, mock_rate_limit):
        scraper = LinkedInScraper()
        scraper._fetch = AsyncMock(side_effect=Exception("Error"))

        results = await scraper.get_company_posts(
            "https://www.linkedin.com/company/test"
        )
        assert results == []

    def test_is_linkedin_url(self):
        scraper = LinkedInScraper()
        assert scraper._is_linkedin_url("https://www.linkedin.com/posts/test")
        assert scraper._is_linkedin_url("https://linkedin.com/in/user")
        assert not scraper._is_linkedin_url("https://example.com")
        assert not scraper._is_linkedin_url("not a url")


class TestLinkedInURLHandler:
    @patch("src.scrapers.linkedin.rate_limit", new_callable=AsyncMock)
    async def test_process_valid_url(self, mock_rate_limit):
        handler = LinkedInURLHandler()

        mock_response = MagicMock()
        mock_response.text = ARTICLE_HTML
        handler.scraper._fetch = AsyncMock(return_value=mock_response)

        result = await handler.process_url("https://www.linkedin.com/posts/test")
        assert result is not None

    async def test_process_invalid_url(self):
        handler = LinkedInURLHandler()
        with pytest.raises(ValueError, match="Invalid LinkedIn URL"):
            await handler.process_url("https://example.com/not-linkedin")

    async def test_close(self):
        handler = LinkedInURLHandler()
        handler.scraper.close = AsyncMock()
        await handler.close()
        handler.scraper.close.assert_awaited_once()
