"""SupervisorAgent 測試"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.supervisor import SubQueryPlan, SupervisorAgent, SupervisorInput


class TestSupervisorAgent:
    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        structured_llm = MagicMock()
        structured_llm.ainvoke = AsyncMock(
            return_value=SubQueryPlan(
                sub_queries=["AI 取代工作 最新新聞", "AI 取代工作 公眾反應"],
                search_strategy="先搜尋新聞再搜尋社群",
                recommended_sources=["news", "forum"],
            )
        )
        llm.with_structured_output.return_value = structured_llm
        return llm

    async def test_decompose_query(self, mock_llm, sample_research_request):
        agent = SupervisorAgent(llm=mock_llm)
        result = await agent(SupervisorInput(request=sample_research_request))

        assert result.success
        assert len(result.data.plan.sub_queries) == 2
        assert result.data.original_request.topic == "AI 取代工作"

    async def test_llm_error_handled(self, sample_research_request):
        llm = MagicMock()
        structured_llm = MagicMock()
        structured_llm.ainvoke = AsyncMock(
            side_effect=Exception("LLM connection error")
        )
        llm.with_structured_output.return_value = structured_llm

        agent = SupervisorAgent(llm=llm)
        result = await agent(SupervisorInput(request=sample_research_request))

        assert not result.success
        assert "查詢分解失敗" in result.error
