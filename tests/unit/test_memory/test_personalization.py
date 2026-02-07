"""PersonalizationEngine 測試"""

from unittest.mock import AsyncMock, MagicMock


from src.memory.models.user_profile import (
    UserProfile,
)
from src.memory.personalization import PersonalizationEngine


def _make_mock_manager(profile=None, corrections=None, topic_context=None):
    manager = MagicMock()
    manager.get_or_create_user = AsyncMock(
        return_value=profile or UserProfile(user_id="user-1")
    )
    manager.get_relevant_corrections = AsyncMock(return_value=corrections or [])
    manager.get_topic_context = AsyncMock(
        return_value=topic_context
        or {
            "topic_preference": None,
            "related_knowledge": [],
            "related_conversations": [],
            "user_style": "casual",
            "analysis_depth": "standard",
        }
    )
    return manager


class TestPersonalizationEngine:
    async def test_basic_prompt(self):
        engine = PersonalizationEngine(_make_mock_manager())
        result = await engine.get_personalized_prompt(
            "user-1", "分析以下話題", "AI", "deep_analyzer"
        )

        assert "分析以下話題" in result
        assert "使用者偏好" in result
        assert "casual" in result

    async def test_with_corrections(self):
        corrections = [
            {
                "pattern": "提到 AI 時",
                "correction": "注意新興工作",
                "context": "AI 分析",
            }
        ]
        engine = PersonalizationEngine(_make_mock_manager(corrections=corrections))
        result = await engine.get_personalized_prompt(
            "user-1", "base", "AI", "deep_analyzer"
        )

        assert "過去的修正" in result
        assert "提到 AI 時" in result
        assert "注意新興工作" in result

    async def test_with_topic_preference(self):
        topic_context = {
            "topic_preference": {
                "interest_level": 0.9,
                "perspective_notes": "關注 AI 對教育的影響",
            },
            "related_knowledge": [],
            "related_conversations": [],
            "user_style": "formal",
            "analysis_depth": "deep",
        }
        engine = PersonalizationEngine(_make_mock_manager(topic_context=topic_context))
        result = await engine.get_personalized_prompt(
            "user-1", "base", "AI", "deep_analyzer"
        )

        assert "使用者對此話題的觀點" in result
        assert "0.9" in result

    async def test_with_professional_background(self):
        profile = UserProfile(
            user_id="user-1",
            professional_background="軟體工程師",
            areas_of_expertise=["AI", "後端開發"],
        )
        engine = PersonalizationEngine(_make_mock_manager(profile=profile))
        result = await engine.get_personalized_prompt(
            "user-1", "base", "AI", "deep_analyzer"
        )

        assert "軟體工程師" in result
        assert "AI" in result

    async def test_with_blocked_sources(self):
        profile = UserProfile(
            user_id="user-1",
            blocked_sources=["unreliable_source"],
        )
        engine = PersonalizationEngine(_make_mock_manager(profile=profile))
        result = await engine.get_personalized_prompt(
            "user-1", "base", "AI", "deep_analyzer"
        )

        assert "避免引用的來源" in result
        assert "unreliable_source" in result
