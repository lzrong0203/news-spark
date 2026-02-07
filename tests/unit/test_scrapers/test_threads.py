"""ThreadsScraper 測試"""

from unittest.mock import AsyncMock, MagicMock, patch


from src.scrapers.threads import ThreadsScraper


class TestThreadsScraper:
    @patch("src.scrapers.threads.rate_limit", new_callable=AsyncMock)
    async def test_search_hashtag(self, mock_rate_limit):
        scraper = ThreadsScraper()

        html = """
        <html>
        <script type="application/json">
        {"data": {"text": "AI is great", "user": {"username": "testuser"}, "id": "123", "like_count": 5, "reply_count": 2}}
        </script>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = html
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.search("#AI")
        assert len(results) == 1
        assert results[0].source_type == "social"

    @patch("src.scrapers.threads.rate_limit", new_callable=AsyncMock)
    async def test_search_username(self, mock_rate_limit):
        scraper = ThreadsScraper()

        html = """
        <html>
        <script type="application/json">
        {"text": "User post", "user": {"username": "testuser"}, "id": "456"}
        </script>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = html
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.search("@testuser")
        assert len(results) == 1

    @patch("src.scrapers.threads.rate_limit", new_callable=AsyncMock)
    async def test_search_plain_query(self, mock_rate_limit):
        scraper = ThreadsScraper()

        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.search("AI")
        assert isinstance(results, list)

    @patch("src.scrapers.threads.rate_limit", new_callable=AsyncMock)
    async def test_search_failure_returns_empty(self, mock_rate_limit):
        scraper = ThreadsScraper()
        scraper._fetch = AsyncMock(side_effect=Exception("Network error"))

        results = await scraper.search("#AI")
        assert results == []

    @patch("src.scrapers.threads.rate_limit", new_callable=AsyncMock)
    async def test_get_user_posts(self, mock_rate_limit):
        scraper = ThreadsScraper()

        html = """
        <html>
        <script type="application/json">
        {"text": "My post", "author": {"username": "user1"}, "id": "789", "taken_at": 1706612400}
        </script>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = html
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.get_user_posts("user1")
        assert len(results) == 1
        assert results[0].published_at is not None

    @patch("src.scrapers.threads.rate_limit", new_callable=AsyncMock)
    async def test_get_post(self, mock_rate_limit):
        scraper = ThreadsScraper()

        html = """
        <html>
        <script type="application/json">
        {"text": "Single post", "user": {"username": "poster"}, "id": "abc"}
        </script>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = html
        scraper._fetch = AsyncMock(return_value=mock_response)

        result = await scraper.get_post("https://threads.net/@poster/post/abc")
        assert result is not None
        assert "Single post" in result.content

    @patch("src.scrapers.threads.rate_limit", new_callable=AsyncMock)
    async def test_get_post_failure(self, mock_rate_limit):
        scraper = ThreadsScraper()
        scraper._fetch = AsyncMock(side_effect=Exception("Error"))

        result = await scraper.get_post("https://threads.net/@test/post/123")
        assert result is None

    def test_find_posts_in_json(self):
        scraper = ThreadsScraper()
        data = {
            "nodes": [
                {"text": "Post 1", "user": {"username": "u1"}, "id": "1"},
                {"text": "Post 2", "author": {"username": "u2"}, "id": "2"},
            ]
        }
        posts = scraper._find_posts_in_json(data)
        assert len(posts) == 2

    def test_find_posts_depth_limit(self):
        scraper = ThreadsScraper()
        posts = scraper._find_posts_in_json({"a": "b"}, depth=11)
        assert posts == []

    def test_json_to_content_item_empty_text(self):
        scraper = ThreadsScraper()
        result = scraper._json_to_content_item({}, "test")
        assert result is None

    def test_json_to_content_item_with_iso_date(self):
        scraper = ThreadsScraper()
        post = {
            "text": "Hello",
            "user": {"username": "u"},
            "id": "1",
            "created_at": "2025-01-30T10:00:00Z",
        }
        result = scraper._json_to_content_item(post, "test")
        assert result is not None
        assert result.published_at is not None

    def test_html_to_content_item_fallback(self):
        from bs4 import BeautifulSoup

        scraper = ThreadsScraper()
        html = '<div data-pressable-container="true"><span dir="auto">Hello world</span></div>'
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one("[data-pressable-container='true']")

        result = scraper._html_to_content_item(container, "test")
        assert result is not None
        assert result.content == "Hello world"

    def test_html_to_content_item_no_text(self):
        from bs4 import BeautifulSoup

        scraper = ThreadsScraper()
        html = '<div data-pressable-container="true"><img src="test.jpg"/></div>'
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one("[data-pressable-container='true']")

        result = scraper._html_to_content_item(container, "test")
        assert result is None
