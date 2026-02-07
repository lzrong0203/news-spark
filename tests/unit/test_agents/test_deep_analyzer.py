"""DeepAnalyzerAgent 測試"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.deep_analyzer import DeepAnalyzerAgent, DeepAnalyzerInput
from src.models.content import AnalysisResult


class TestDeepAnalyzerAgent:
    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        structured_llm = MagicMock()
        structured_llm.ainvoke = AsyncMock(
            return_value=AnalysisResult(
                topic="AI",
                key_insights=["insight 1", "insight 2"],
                sentiment_summary="neutral",
                confidence_score=0.9,
            )
        )
        llm.with_structured_output.return_value = structured_llm
        return llm

    async def test_analyze_returns_result(self, mock_llm, sample_content_items):
        agent = DeepAnalyzerAgent(llm=mock_llm)
        result = await agent(
            DeepAnalyzerInput(topic="AI", content_items=sample_content_items)
        )

        assert result.success
        assert result.data.topic == "AI"
        assert len(result.data.key_insights) == 2
        assert result.data.source_count == 3  # 自動修正為實際來源數

    async def test_analyze_empty_items(self, mock_llm):
        agent = DeepAnalyzerAgent(llm=mock_llm)
        result = await agent(DeepAnalyzerInput(topic="AI", content_items=[]))

        assert result.success

    async def test_analyze_llm_error(self, sample_content_items):
        llm = MagicMock()
        structured_llm = MagicMock()
        structured_llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))
        llm.with_structured_output.return_value = structured_llm

        agent = DeepAnalyzerAgent(llm=llm)
        result = await agent(
            DeepAnalyzerInput(topic="AI", content_items=sample_content_items)
        )

        assert not result.success
        assert "深度分析失敗" in result.error

    def test_format_content_summary(self, sample_content_items):
        agent = DeepAnalyzerAgent()
        summary = agent._format_content_summary(sample_content_items)

        assert "AI 最新進展" in summary
        assert "PTT 測試文章" in summary
        assert "[news]" in summary
        assert "[forum]" in summary

    def test_format_empty_items(self):
        agent = DeepAnalyzerAgent()
        summary = agent._format_content_summary([])
        assert "無來源資料" in summary
