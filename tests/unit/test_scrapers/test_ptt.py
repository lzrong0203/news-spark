"""PTTScraper 測試"""

from unittest.mock import AsyncMock, MagicMock, patch


from src.scrapers.ptt import PTTScraper


BOARD_HTML = """
<div class="r-ent">
    <div class="nrec"><span class="hl f3">10</span></div>
    <div class="title"><a href="/bbs/Gossiping/M.1234567890.A.ABC.html">[新聞] AI 測試新聞</a></div>
    <div class="author">testuser</div>
    <div class="date"> 1/30</div>
</div>
<div class="r-ent">
    <div class="nrec"><span class="hl f9">爆</span></div>
    <div class="title"><a href="/bbs/Gossiping/M.1234567891.A.DEF.html">[問卦] 為什麼 AI 這麼強</a></div>
    <div class="author">user2</div>
    <div class="date"> 1/30</div>
</div>
<div class="r-ent">
    <div class="nrec"></div>
    <div class="title">(本文已被刪除)</div>
    <div class="author">-</div>
    <div class="date"> 1/29</div>
</div>
<div class="btn-group btn-group-paging">
    <a class="btn wide" href="/bbs/Gossiping/index1234.html">‹ 上頁</a>
</div>
"""

ARTICLE_HTML = """
<div id="main-content" class="bbs-screen bbs-content">
    <div class="article-metaline"><span class="article-meta-tag">作者</span><span class="article-meta-value">testuser (暱稱)</span></div>
    <div class="article-metaline"><span class="article-meta-tag">標題</span><span class="article-meta-value">[新聞] AI 測試文章</span></div>
    <div class="article-metaline"><span class="article-meta-tag">時間</span><span class="article-meta-value">Thu Jan 30 10:00:00 2025</span></div>

這是文章正文內容。
AI 正在改變世界。

※ 發信站: 批踢踢實業坊
<div class="push"><span class="push-tag">推 </span><span class="push-userid">user1</span><span class="push-content">: 同意</span></div>
<div class="push"><span class="push-tag">推 </span><span class="push-userid">user2</span><span class="push-content">: +1</span></div>
<div class="push"><span class="push-tag">→ </span><span class="push-userid">user3</span><span class="push-content">: 不同意</span></div>
</div>
"""


class TestPTTScraper:
    @patch("src.scrapers.ptt.rate_limit", new_callable=AsyncMock)
    async def test_get_board_articles(self, mock_rate_limit):
        scraper = PTTScraper()

        mock_response = MagicMock()
        mock_response.text = BOARD_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.get_board_articles("Gossiping", pages=1)

        assert len(results) == 2  # 已刪除的不算
        assert "AI 測試新聞" in results[0].title
        assert results[0].source_type == "forum"
        assert "PTT:" in results[0].source_name

    @patch("src.scrapers.ptt.rate_limit", new_callable=AsyncMock)
    async def test_push_count_parsing(self, mock_rate_limit):
        scraper = PTTScraper()

        mock_response = MagicMock()
        mock_response.text = BOARD_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.get_board_articles("Gossiping", pages=1)

        # 第一篇: 10 推
        assert results[0].engagement.likes == 10
        # 第二篇: 爆 = 100
        assert results[1].engagement.likes == 100

    @patch("src.scrapers.ptt.rate_limit", new_callable=AsyncMock)
    async def test_search_filters_by_query(self, mock_rate_limit):
        scraper = PTTScraper()

        mock_response = MagicMock()
        mock_response.text = BOARD_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.search("AI", board="Gossiping")

        # 3 pages x 2 articles (both contain "AI") = 6 results, capped by max_results=10
        assert len(results) > 0
        assert all("AI" in r.title.upper() for r in results)

    @patch("src.scrapers.ptt.rate_limit", new_callable=AsyncMock)
    async def test_search_no_match(self, mock_rate_limit):
        scraper = PTTScraper()

        mock_response = MagicMock()
        mock_response.text = BOARD_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.search("完全不存在的關鍵字", board="Gossiping")

        assert len(results) == 0

    @patch("src.scrapers.ptt.rate_limit", new_callable=AsyncMock)
    async def test_get_article_content(self, mock_rate_limit):
        scraper = PTTScraper()

        mock_response = MagicMock()
        mock_response.text = ARTICLE_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        result = await scraper.get_article_content(
            "https://www.ptt.cc/bbs/Gossiping/M.123.html"
        )

        assert result is not None
        assert result.title == "[新聞] AI 測試文章"
        assert "testuser" in result.author
        assert result.engagement.comments == 3  # 3 pushes
        assert result.engagement.likes == 2  # 2 推

    def test_parse_date_valid(self):
        scraper = PTTScraper()
        result = scraper._parse_date("Thu Jan 30 10:00:00 2025")
        assert result is not None
        assert result.year == 2025

    def test_parse_date_invalid(self):
        scraper = PTTScraper()
        result = scraper._parse_date("invalid date")
        assert result is None

    @patch("src.scrapers.ptt.rate_limit", new_callable=AsyncMock)
    async def test_get_hot_articles(self, mock_rate_limit):
        scraper = PTTScraper()

        mock_response = MagicMock()
        mock_response.text = BOARD_HTML
        scraper._fetch = AsyncMock(return_value=mock_response)

        results = await scraper.get_hot_articles("Gossiping", min_pushes=50)

        # All "hot" articles have 爆 (100 pushes) >= 50
        assert len(results) > 0
        assert all(r.engagement.likes >= 50 for r in results)

    def test_parse_nrec_x(self):
        """X 開頭的噓文計數"""
        scraper = PTTScraper()
        from bs4 import BeautifulSoup

        html = """
        <div class="r-ent">
            <div class="nrec"><span class="hl f1">X3</span></div>
            <div class="title"><a href="/bbs/test/M.1.A.html">噓文多</a></div>
            <div class="author">user</div>
            <div class="date">1/30</div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.select_one("div.r-ent")
        result = scraper._parse_article_entry(article, "test")
        assert result is not None
        assert result.engagement.likes == 0  # max(0, -10) = 0
