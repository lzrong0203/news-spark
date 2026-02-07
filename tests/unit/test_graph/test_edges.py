"""LangGraph 條件邊邏輯測試"""

from src.graph.edges import (
    should_continue_after_analysis,
    should_continue_after_scraping,
    should_continue_after_supervisor,
)


class TestSupervisorRouting:
    def test_routes_to_scraping_on_success(self):
        state = {"sub_queries": ["q1", "q2"]}
        assert should_continue_after_supervisor(state) == "news_scraper"

    def test_routes_to_error_on_error(self):
        state = {"error": "something failed", "sub_queries": ["q1"]}
        assert should_continue_after_supervisor(state) == "error_handler"

    def test_routes_to_error_on_empty_queries(self):
        state = {"sub_queries": []}
        assert should_continue_after_supervisor(state) == "error_handler"

    def test_routes_to_error_on_missing_queries(self):
        state = {}
        assert should_continue_after_supervisor(state) == "error_handler"


class TestScrapingRouting:
    def test_routes_to_analysis_with_news_results(self):
        state = {"news_results": [{"title": "test"}]}
        assert should_continue_after_scraping(state) == "deep_analyzer"

    def test_routes_to_analysis_with_forum_results(self):
        state = {"forum_results": [{"title": "test"}]}
        assert should_continue_after_scraping(state) == "deep_analyzer"

    def test_routes_to_analysis_with_social_results(self):
        state = {"social_results": [{"title": "test"}]}
        assert should_continue_after_scraping(state) == "deep_analyzer"

    def test_routes_to_error_with_no_results(self):
        state = {"news_results": [], "social_results": [], "forum_results": []}
        assert should_continue_after_scraping(state) == "error_handler"

    def test_routes_to_error_with_empty_state(self):
        state = {}
        assert should_continue_after_scraping(state) == "error_handler"


class TestAnalysisRouting:
    def test_routes_to_synthesis_on_success(self):
        state = {"analysis": {"topic": "test"}}
        assert should_continue_after_analysis(state) == "content_synthesizer"

    def test_routes_to_error_on_error(self):
        state = {"error": "failed", "analysis": {"topic": "test"}}
        assert should_continue_after_analysis(state) == "error_handler"

    def test_routes_to_error_on_missing_analysis(self):
        state = {}
        assert should_continue_after_analysis(state) == "error_handler"
