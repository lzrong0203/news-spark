"""ContentSynthesizerAgent 測試"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.content_synthesizer import (
    ContentSynthesizerAgent,
    ContentSynthesizerInput,
    LLMPlatformTips,
    LLMVideoOutput,
)


class TestContentSynthesizerAgent:
    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        structured_llm = MagicMock()
        structured_llm.ainvoke = AsyncMock(
            return_value=LLMVideoOutput(
                topic="AI 取代工作",
                title_suggestion="AI 正在取代這 5 種工作！",
                hook_line="你的工作會被 AI 取代嗎？",
                key_talking_points=["論點 1", "論點 2"],
                visual_suggestions=["🤖 AI 畫面", "📊 圖表"],
                viral_score=0.85,
                target_emotion="震驚",
                controversy_level="medium",
                call_to_action="留言分享你的想法！",
                hashtag_suggestions=["AI", "未來工作"],
                platform_tips=LLMPlatformTips(
                    tiktok=["用 AI 濾鏡展示變臉效果", "搭配熱門 AI 音樂", "加入工作消失的倒數計時特效"],
                    youtube_shorts=["標題放「5 種工作即將消失」衝點擊", "結尾加訂閱鈴鐺提醒", "描述欄連結完整分析影片"],
                    instagram_reels=["限動加入投票：你的工作安全嗎？", "用輪播圖列出 5 種工作", "導流到個人主頁看完整懶人包"],
                ),
            )
        )
        llm.with_structured_output.return_value = structured_llm
        return llm

    async def test_synthesize_returns_video_material(
        self, mock_llm, sample_analysis_result, sample_content_items
    ):
        agent = ContentSynthesizerAgent(llm=mock_llm)
        result = await agent(
            ContentSynthesizerInput(
                topic="AI 取代工作",
                analysis=sample_analysis_result,
                content_items=sample_content_items,
            )
        )

        assert result.success
        assert result.data.topic == "AI 取代工作"
        assert result.data.viral_score == 0.85
        assert len(result.data.sources) == 3  # 從 content_items 轉換
        assert len(result.data.platform_variants) == 3  # 預設 3 平台
        assert result.data.generated_at  # 有生成時間

    async def test_synthesize_with_custom_platforms(
        self, mock_llm, sample_analysis_result
    ):
        agent = ContentSynthesizerAgent(llm=mock_llm)
        result = await agent(
            ContentSynthesizerInput(
                topic="AI",
                analysis=sample_analysis_result,
                target_platforms=["tiktok"],
            )
        )

        assert result.success
        assert len(result.data.platform_variants) == 1
        assert result.data.platform_variants[0].platform == "TikTok"

    def test_build_sources(self, sample_content_items):
        agent = ContentSynthesizerAgent()
        sources = agent._build_sources(sample_content_items)

        assert len(sources) == 3
        assert sources[0].title == "AI 最新進展"
        assert sources[0].source_type == "news"
        assert sources[0].published_at == "2025-01-30 10:00"
        assert sources[1].published_at is None  # PTT 沒有 published_at
