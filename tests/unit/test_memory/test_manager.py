"""MemoryManager 測試"""

from unittest.mock import AsyncMock, MagicMock


from src.memory.manager import MemoryManager
from src.memory.models.feedback import FeedbackType, UserFeedback
from src.memory.models.knowledge_graph import KnowledgeNode, NodeType
from src.memory.models.learned_correction import LearnedCorrection
from src.memory.models.user_profile import (
    ContentStyle,
    TopicPreference,
    UserProfile,
)
from src.memory.storage.sqlite_store import SQLiteStore


def _make_mock_stores():
    """建立 mock SQLiteStore 和 VectorStore"""
    sqlite = MagicMock(spec=SQLiteStore)
    sqlite.initialize = AsyncMock()
    sqlite.close = AsyncMock()
    sqlite.get_user = AsyncMock(return_value=None)
    sqlite.create_user = AsyncMock()
    sqlite.update_user = AsyncMock()
    sqlite.delete_user = AsyncMock()
    sqlite.save_feedback = AsyncMock()
    sqlite.get_unprocessed_feedback = AsyncMock(return_value=[])
    sqlite.mark_feedback_processed = AsyncMock()
    sqlite.save_correction = AsyncMock()
    sqlite.get_corrections = AsyncMock(return_value=[])
    sqlite.save_node = AsyncMock()
    sqlite.get_nodes = AsyncMock(return_value=[])

    vector = MagicMock()
    vector.initialize = AsyncMock()
    vector.store_correction = AsyncMock()
    vector.search_corrections = AsyncMock(return_value=[])
    vector.search_conversations = AsyncMock(return_value=[])
    vector.delete_user_data = AsyncMock()

    return sqlite, vector


class TestMemoryManagerInit:
    async def test_initialize_with_injected_stores(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        sqlite.initialize.assert_awaited_once()
        vector.initialize.assert_awaited_once()

    async def test_close(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()
        await manager.close()

        sqlite.close.assert_awaited_once()


class TestUserManagement:
    async def test_get_or_create_new_user(self):
        sqlite, vector = _make_mock_stores()
        sqlite.get_user.return_value = None

        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        profile = await manager.get_or_create_user("new-user")
        assert profile.user_id == "new-user"
        sqlite.create_user.assert_awaited_once()

    async def test_get_existing_user(self):
        sqlite, vector = _make_mock_stores()
        existing = UserProfile(user_id="existing", preferred_style=ContentStyle.FORMAL)
        sqlite.get_user.return_value = existing

        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        profile = await manager.get_or_create_user("existing")
        assert profile.preferred_style == ContentStyle.FORMAL
        sqlite.create_user.assert_not_awaited()

    async def test_user_cache(self):
        sqlite, vector = _make_mock_stores()
        sqlite.get_user.return_value = UserProfile(user_id="cached")

        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        await manager.get_or_create_user("cached")
        await manager.get_or_create_user("cached")

        # 第二次應從快取讀取，不再呼叫 sqlite
        assert sqlite.get_user.await_count == 1

    async def test_update_user_profile(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        profile = UserProfile(user_id="update-test")
        await manager.update_user_profile(profile)

        sqlite.update_user.assert_awaited_once()


class TestFeedbackManagement:
    async def test_store_feedback(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        feedback = UserFeedback(
            feedback_id="fb-1",
            user_id="user-1",
            session_id="sess-1",
            original_content="content",
            original_analysis="analysis",
            agent_type="deep_analyzer",
            feedback_type=FeedbackType.CORRECTION,
            user_correction="correction",
        )
        await manager.store_feedback(feedback)
        sqlite.save_feedback.assert_awaited_once_with(feedback)

    async def test_get_unprocessed_feedback(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        await manager.get_unprocessed_feedback("user-1")
        sqlite.get_unprocessed_feedback.assert_awaited_once_with("user-1")

    async def test_mark_feedback_processed(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        await manager.mark_feedback_processed("fb-1")
        sqlite.mark_feedback_processed.assert_awaited_once_with("fb-1")


class TestCorrectionManagement:
    async def test_store_correction(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        correction = LearnedCorrection(
            correction_id="c-1",
            user_id="user-1",
            pattern="p",
            correction="c",
            context="ctx",
        )
        await manager.store_correction(correction)

        sqlite.save_correction.assert_awaited_once_with(correction)
        vector.store_correction.assert_awaited_once()

    async def test_get_relevant_corrections(self):
        sqlite, vector = _make_mock_stores()
        vector.search_corrections.return_value = [{"pattern": "test"}]
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        results = await manager.get_relevant_corrections("user-1", "AI", limit=5)
        assert len(results) == 1
        vector.search_corrections.assert_awaited_once_with("user-1", "AI", 5)

    async def test_get_corrections(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        await manager.get_corrections("user-1", limit=10)
        sqlite.get_corrections.assert_awaited_once_with("user-1", 10)


class TestTopicContext:
    async def test_get_topic_context(self):
        sqlite, vector = _make_mock_stores()
        profile = UserProfile(
            user_id="user-1",
            topic_preferences={
                "AI": TopicPreference(topic="AI", interest_level=0.9),
            },
        )
        sqlite.get_user.return_value = profile
        sqlite.get_nodes.return_value = [
            KnowledgeNode(
                node_id="n1",
                user_id="user-1",
                node_type=NodeType.TOPIC,
                name="AI",
            )
        ]
        vector.search_conversations.return_value = [{"content": "past convo"}]

        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        ctx = await manager.get_topic_context("user-1", "AI")
        assert ctx["topic_preference"] is not None
        assert ctx["topic_preference"]["interest_level"] == 0.9
        assert len(ctx["related_knowledge"]) == 1
        assert len(ctx["related_conversations"]) == 1

    async def test_update_topic_preference(self):
        sqlite, vector = _make_mock_stores()
        sqlite.get_user.return_value = UserProfile(user_id="user-1")

        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        await manager.update_topic_preference("user-1", "AI", 0.9, "很有興趣")
        sqlite.update_user.assert_awaited_once()


class TestKnowledgeGraph:
    async def test_save_knowledge_node(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        node = KnowledgeNode(
            node_id="n1",
            user_id="user-1",
            node_type=NodeType.TOPIC,
            name="AI",
        )
        await manager.save_knowledge_node(node)
        sqlite.save_node.assert_awaited_once_with(node)


class TestGDPR:
    async def test_export_user_data(self):
        sqlite, vector = _make_mock_stores()
        sqlite.get_user.return_value = UserProfile(user_id="user-1")
        sqlite.get_corrections.return_value = []
        sqlite.get_nodes.return_value = []

        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        data = await manager.export_user_data("user-1")
        assert "profile" in data
        assert "corrections" in data
        assert "knowledge_nodes" in data

    async def test_delete_user_data(self):
        sqlite, vector = _make_mock_stores()
        manager = MemoryManager(sqlite_store=sqlite, vector_store=vector)
        await manager.initialize()

        # Pre-populate cache
        sqlite.get_user.return_value = UserProfile(user_id="user-del")
        await manager.get_or_create_user("user-del")

        result = await manager.delete_user_data("user-del")
        assert result is True
        sqlite.delete_user.assert_awaited_once_with("user-del")
        vector.delete_user_data.assert_awaited_once_with("user-del")
