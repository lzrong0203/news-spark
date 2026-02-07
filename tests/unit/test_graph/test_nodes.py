"""LangGraph 節點測試"""

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.base import AgentResult
from src.agents.supervisor import SubQueryPlan, SupervisorOutput
from src.graph.nodes import (
    content_synthesizer_node,
    deep_analyzer_node,
    news_scraper_node,
    social_media_node,
    supervisor_node,
)
from src.models.content import AnalysisResult, ContentItem, ResearchRequest


@pytest.fixture
def base_state():
    return {
        "request": ResearchRequest(
            topic="AI 趨勢",
            user_id="test-user",
            sources=["news", "social", "forum"],
        ),
        "execution_log": [],
    }


@pytest.fixture
def sample_items():
    return [
        ContentItem(
            title="AI News",
            url="https://example.com/ai",
            content="AI content",
            source_type="news",
            source_name="TestSource",
        )
    ]


class TestSupervisorNode:
    async def test_success(self, base_state):
        plan = SubQueryPlan(
            sub_queries=["AI 最新新聞", "AI 公眾反應"],
            search_strategy="先搜新聞再搜社群",
            recommended_sources=["news", "forum"],
        )
        mock_result = AgentResult(
            success=True,
            data=SupervisorOutput(
                plan=plan,
                original_request=base_state["request"],
            ),
        )

        with patch("src.graph.nodes.SupervisorAgent") as MockAgent:
            MockAgent.return_value = AsyncMock(return_value=mock_result)

            result = await supervisor_node(base_state)

        assert result["current_step"] == "queries_decomposed"
        assert len(result["sub_queries"]) == 2

    async def test_failure(self, base_state):
        mock_result = AgentResult(
            success=False,
            error="LLM connection error",
        )

        with patch("src.graph.nodes.SupervisorAgent") as MockAgent:
            MockAgent.return_value = AsyncMock(return_value=mock_result)

            result = await supervisor_node(base_state)

        assert result["current_step"] == "supervisor_failed"
        assert "LLM connection error" in result["error"]


class TestNewsScraperNode:
    async def test_success(self, base_state, sample_items):
        from src.agents.news_scraper import NewsScraperOutput

        base_state["sub_queries"] = ["AI 最新新聞"]
        output = NewsScraperOutput(
            items=sample_items,
            total_count=1,
            sources_used=["google_news"],
            errors=[],
        )
        mock_result = AgentResult(success=True, data=output)

        with patch("src.graph.nodes.NewsScraperAgent") as MockAgent:
            MockAgent.return_value = AsyncMock(return_value=mock_result)

            result = await news_scraper_node(base_state)

        assert result["current_step"] == "news_scraped"
        assert len(result["news_results"]) == 1


class TestSocialMediaNode:
    async def test_success(self, base_state, sample_items):
        from src.agents.social_media import SocialMediaOutput

        base_state["sub_queries"] = ["AI 公眾反應"]
        output = SocialMediaOutput(
            forum_items=sample_items,
            social_items=[],
            total_count=1,
            sources_used=["ptt:Gossiping"],
            errors=[],
        )
        mock_result = AgentResult(success=True, data=output)

        with patch("src.graph.nodes.SocialMediaAgent") as MockAgent:
            MockAgent.return_value = AsyncMock(return_value=mock_result)

            result = await social_media_node(base_state)

        assert result["current_step"] == "social_scraped"
        assert len(result["forum_results"]) == 1


class TestDeepAnalyzerNode:
    async def test_success(self, base_state, sample_items):
        base_state["news_results"] = sample_items
        base_state["social_results"] = []
        base_state["forum_results"] = []

        analysis = AnalysisResult(
            topic="AI 趨勢",
            key_insights=["insight 1"],
            sentiment_summary="positive",
            confidence_score=0.8,
            source_count=1,
        )
        mock_result = AgentResult(success=True, data=analysis)

        with patch("src.graph.nodes.DeepAnalyzerAgent") as MockAgent:
            MockAgent.return_value = AsyncMock(return_value=mock_result)

            result = await deep_analyzer_node(base_state)

        assert result["current_step"] == "analysis_complete"
        assert result["analysis"].confidence_score == 0.8

    async def test_failure(self, base_state):
        base_state["news_results"] = []
        base_state["social_results"] = []
        base_state["forum_results"] = []

        mock_result = AgentResult(success=False, error="Analysis failed")

        with patch("src.graph.nodes.DeepAnalyzerAgent") as MockAgent:
            MockAgent.return_value = AsyncMock(return_value=mock_result)

            result = await deep_analyzer_node(base_state)

        assert result["current_step"] == "analysis_failed"
        assert "Analysis failed" in result["error"]


class TestContentSynthesizerNode:
    async def test_success(self, base_state, sample_items, sample_video_material):
        base_state["news_results"] = sample_items
        base_state["social_results"] = []
        base_state["forum_results"] = []
        base_state["analysis"] = AnalysisResult(
            topic="AI 趨勢",
            key_insights=["insight"],
            sentiment_summary="positive",
            confidence_score=0.8,
            source_count=1,
        )

        mock_result = AgentResult(success=True, data=sample_video_material)

        with patch("src.graph.nodes.ContentSynthesizerAgent") as MockAgent:
            MockAgent.return_value = AsyncMock(return_value=mock_result)

            result = await content_synthesizer_node(base_state)

        assert result["current_step"] == "complete"
        assert result["video_material"] is not None

    async def test_failure(self, base_state):
        base_state["news_results"] = []
        base_state["social_results"] = []
        base_state["forum_results"] = []
        base_state["analysis"] = AnalysisResult(
            topic="AI 趨勢",
            key_insights=[],
            sentiment_summary="neutral",
            confidence_score=0.5,
            source_count=0,
        )

        mock_result = AgentResult(success=False, error="Synthesis failed")

        with patch("src.graph.nodes.ContentSynthesizerAgent") as MockAgent:
            MockAgent.return_value = AsyncMock(return_value=mock_result)

            result = await content_synthesizer_node(base_state)

        assert result["current_step"] == "synthesis_failed"
