"""Unit test shared fixtures"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.content import (
    AnalysisResult,
    ContentItem,
    EngagementMetrics,
    ResearchRequest,
)
from src.models.video_material import PlatformVariant, SourceItem, VideoMaterial


@pytest.fixture
def sample_content_item() -> ContentItem:
    return ContentItem(
        title="測試新聞標題",
        url="https://example.com/test",
        content="這是測試內容，用於驗證系統功能。",
        source_type="news",
        source_name="TestSource",
        published_at=datetime(2025, 1, 30, 10, 0),
    )


@pytest.fixture
def sample_content_items() -> list[ContentItem]:
    return [
        ContentItem(
            title="AI 最新進展",
            url="https://example.com/ai",
            content="AI 技術持續發展",
            source_type="news",
            source_name="NewsAPI:TestSource",
            published_at=datetime(2025, 1, 30, 10, 0),
        ),
        ContentItem(
            title="PTT 測試文章",
            url="https://ptt.cc/test",
            content="PTT 討論內容",
            source_type="forum",
            source_name="PTT:Gossiping",
            engagement=EngagementMetrics(likes=50, comments=10),
        ),
        ContentItem(
            title="Threads 測試貼文",
            url="https://threads.net/@test/123",
            content="Threads 社群貼文",
            source_type="social",
            source_name="Threads:@test",
        ),
    ]


@pytest.fixture
def sample_research_request() -> ResearchRequest:
    return ResearchRequest(
        topic="AI 取代工作",
        user_id="test-user",
        sources=["news", "social", "forum"],
        depth=2,
        max_results_per_source=10,
    )


@pytest.fixture
def sample_analysis_result() -> AnalysisResult:
    return AnalysisResult(
        topic="AI 取代工作",
        key_insights=["洞察 1: AI 正在影響多個產業", "洞察 2: 新職缺同時在增加"],
        controversies=["爭議: 政府是否應該管制 AI"],
        trending_angles=["角度: 教育體系如何適應"],
        sentiment_summary="整體偏向焦慮但帶有期待",
        recommended_hooks=["你的工作會被 AI 取代嗎？", "3 個 AI 無法取代的技能"],
        source_count=3,
        confidence_score=0.8,
    )


@pytest.fixture
def sample_video_material() -> VideoMaterial:
    return VideoMaterial(
        topic="AI 取代工作",
        title_suggestion="AI 正在取代這 5 種工作！你的在列嗎？",
        hook_line="「未來 5 年，40% 的工作將被 AI 取代」——你準備好了嗎？",
        key_talking_points=["論點 1", "論點 2", "論點 3"],
        visual_suggestions=["🤖 AI 機器人畫面", "📊 趨勢圖表"],
        viral_score=0.85,
        target_emotion="震驚",
        call_to_action="留言告訴我你覺得哪些工作最危險！",
        hashtag_suggestions=["AI", "未來工作"],
        platform_variants=[
            PlatformVariant(platform="TikTok", duration="15-60 秒"),
        ],
        sources=[
            SourceItem(title="Test", url="https://example.com", source_type="news"),
        ],
        generated_at="2025-01-30 10:00",
        confidence_score=0.8,
    )


@pytest.fixture
def mock_chat_model():
    """Mock LangChain ChatModel"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock()
    mock.with_structured_output = MagicMock(return_value=mock)
    return mock
