"""GoogleNewsScraper 測試"""

from unittest.mock import AsyncMock, MagicMock, patch


from src.scrapers.google_news import GoogleNewsScraper


class FeedEntry(dict):
    """模擬 feedparser entry (dict subclass with attribute access)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


def _make_feed_entry(
    title="Test News", link="https://example.com/news", summary="Summary"
):
    entry = FeedEntry(
        title=title,
        link=link,
        summary=summary,
        published_parsed=(2025, 1, 30, 10, 0, 0, 3, 30, 0),
        source={"title": "TestSource"},
    )
    return entry


def _make_feed(entries):
    class Feed:
        pass

    feed = Feed()
    feed.entries = entries
    return feed


class TestGoogleNewsScraper:
    @patch("src.scrapers.google_news.rate_limit", new_callable=AsyncMock)
    async def test_search(self, mock_rate_limit):
        scraper = GoogleNewsScraper()

        mock_response = MagicMock()
        mock_response.text = "<rss>mock</rss>"
        scraper._fetch = AsyncMock(return_value=mock_response)

        entries = [
            _make_feed_entry(),
            _make_feed_entry("News 2", "https://example.com/2"),
        ]
        with patch(
            "src.scrapers.google_news.feedparser.parse",
            return_value=_make_feed(entries),
        ):
            results = await scraper.search("AI", max_results=10)

        assert len(results) == 2
        assert results[0].title == "Test News"
        assert results[0].source_type == "news"
        assert "GoogleNews:" in results[0].source_name

    @patch("src.scrapers.google_news.rate_limit", new_callable=AsyncMock)
    async def test_search_max_results(self, mock_rate_limit):
        scraper = GoogleNewsScraper()

        mock_response = MagicMock()
        mock_response.text = "<rss>mock</rss>"
        scraper._fetch = AsyncMock(return_value=mock_response)

        entries = [
            _make_feed_entry(f"News {i}", f"https://example.com/{i}") for i in range(20)
        ]
        with patch(
            "src.scrapers.google_news.feedparser.parse",
            return_value=_make_feed(entries),
        ):
            results = await scraper.search("AI", max_results=5)

        assert len(results) == 5

    @patch("src.scrapers.google_news.rate_limit", new_callable=AsyncMock)
    async def test_get_top_stories(self, mock_rate_limit):
        scraper = GoogleNewsScraper()

        mock_response = MagicMock()
        mock_response.text = "<rss>mock</rss>"
        scraper._fetch = AsyncMock(return_value=mock_response)

        entries = [_make_feed_entry("Top Story")]
        with patch(
            "src.scrapers.google_news.feedparser.parse",
            return_value=_make_feed(entries),
        ):
            results = await scraper.get_top_stories()

        assert len(results) == 1

    @patch("src.scrapers.google_news.rate_limit", new_callable=AsyncMock)
    async def test_get_topic(self, mock_rate_limit):
        scraper = GoogleNewsScraper()

        mock_response = MagicMock()
        mock_response.text = "<rss>mock</rss>"
        scraper._fetch = AsyncMock(return_value=mock_response)

        entries = [_make_feed_entry("Tech News")]
        with patch(
            "src.scrapers.google_news.feedparser.parse",
            return_value=_make_feed(entries),
        ):
            results = await scraper.get_topic("technology")

        assert len(results) == 1

    def test_parse_feed_no_published_date(self):
        scraper = GoogleNewsScraper()
        entry = _make_feed_entry()
        entry["published_parsed"] = None
        entry.published_parsed = None
        feed = _make_feed([entry])

        results = scraper._parse_feed(feed, 10, "zh-TW")
        assert len(results) == 1
        assert results[0].published_at is None

    def test_parse_feed_no_source(self):
        scraper = GoogleNewsScraper()
        entry = _make_feed_entry()
        del entry["source"]
        if hasattr(entry, "source"):
            delattr(entry, "source")
        feed = _make_feed([entry])

        results = scraper._parse_feed(feed, 10, "zh-TW")
        assert "Unknown" in results[0].source_name
