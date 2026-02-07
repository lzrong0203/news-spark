"""SQLiteStore 測試"""

import pytest

from src.memory.models.feedback import FeedbackType, UserFeedback
from src.memory.models.knowledge_graph import KnowledgeEdge, KnowledgeNode, NodeType
from src.memory.models.learned_correction import LearnedCorrection
from src.memory.models.user_profile import ContentStyle, UserProfile
from src.memory.storage.sqlite_store import SQLiteStore


@pytest.fixture
async def sqlite_store():
    store = SQLiteStore(":memory:")
    await store.initialize()
    yield store
    await store.close()


class TestUserCRUD:
    async def test_create_and_get_user(self, sqlite_store):
        profile = UserProfile(user_id="test-1")
        await sqlite_store.create_user(profile)

        result = await sqlite_store.get_user("test-1")
        assert result is not None
        assert result.user_id == "test-1"
        assert result.preferred_style == ContentStyle.CASUAL

    async def test_get_nonexistent_user_returns_none(self, sqlite_store):
        result = await sqlite_store.get_user("nonexistent")
        assert result is None

    async def test_update_user(self, sqlite_store):
        profile = UserProfile(user_id="test-2")
        await sqlite_store.create_user(profile)

        profile.preferred_style = ContentStyle.FORMAL
        await sqlite_store.update_user(profile)

        result = await sqlite_store.get_user("test-2")
        assert result.preferred_style == ContentStyle.FORMAL

    async def test_delete_user(self, sqlite_store):
        profile = UserProfile(user_id="test-del")
        await sqlite_store.create_user(profile)

        await sqlite_store.delete_user("test-del")

        result = await sqlite_store.get_user("test-del")
        assert result is None


class TestFeedbackCRUD:
    @pytest.fixture
    def sample_feedback(self):
        return UserFeedback(
            feedback_id="fb-1",
            user_id="test-1",
            session_id="sess-1",
            original_content="原始內容",
            original_analysis="原始分析",
            agent_type="deep_analyzer",
            feedback_type=FeedbackType.CORRECTION,
            user_correction="修正內容",
        )

    async def test_save_and_get_unprocessed(self, sqlite_store, sample_feedback):
        # 先建立使用者
        await sqlite_store.create_user(UserProfile(user_id="test-1"))

        await sqlite_store.save_feedback(sample_feedback)
        results = await sqlite_store.get_unprocessed_feedback("test-1")
        assert len(results) == 1
        assert results[0].feedback_id == "fb-1"
        assert results[0].feedback_type == FeedbackType.CORRECTION

    async def test_mark_processed(self, sqlite_store, sample_feedback):
        await sqlite_store.create_user(UserProfile(user_id="test-1"))
        await sqlite_store.save_feedback(sample_feedback)

        await sqlite_store.mark_feedback_processed("fb-1")
        results = await sqlite_store.get_unprocessed_feedback("test-1")
        assert len(results) == 0


class TestCorrectionsCRUD:
    @pytest.fixture
    def sample_correction(self):
        return LearnedCorrection(
            correction_id="corr-1",
            user_id="test-1",
            pattern="提到 AI 取代時",
            correction="應同時提及新創造的工作機會",
            context="AI 話題分析",
            confidence=0.7,
        )

    async def test_save_and_get(self, sqlite_store, sample_correction):
        await sqlite_store.create_user(UserProfile(user_id="test-1"))
        await sqlite_store.save_correction(sample_correction)

        results = await sqlite_store.get_corrections("test-1")
        assert len(results) == 1
        assert results[0].pattern == "提到 AI 取代時"
        assert results[0].confidence == 0.7

    async def test_update_stats_confirmed(self, sqlite_store, sample_correction):
        await sqlite_store.create_user(UserProfile(user_id="test-1"))
        await sqlite_store.save_correction(sample_correction)

        await sqlite_store.update_correction_stats("corr-1", confirmed=True)
        results = await sqlite_store.get_corrections("test-1")
        assert results[0].times_confirmed == 1
        assert results[0].times_applied == 1
        assert results[0].confidence == pytest.approx(0.75, abs=0.01)

    async def test_update_stats_rejected(self, sqlite_store, sample_correction):
        await sqlite_store.create_user(UserProfile(user_id="test-1"))
        await sqlite_store.save_correction(sample_correction)

        await sqlite_store.update_correction_stats("corr-1", confirmed=False)
        results = await sqlite_store.get_corrections("test-1")
        assert results[0].times_rejected == 1
        assert results[0].confidence == pytest.approx(0.6, abs=0.01)


class TestKnowledgeGraph:
    async def test_save_and_get_nodes(self, sqlite_store):
        await sqlite_store.create_user(UserProfile(user_id="test-1"))
        node = KnowledgeNode(
            node_id="node-1",
            user_id="test-1",
            node_type=NodeType.TOPIC,
            name="AI",
            description="人工智慧",
        )
        await sqlite_store.save_node(node)

        results = await sqlite_store.get_nodes("test-1")
        assert len(results) == 1
        assert results[0].name == "AI"
        assert results[0].node_type == NodeType.TOPIC

    async def test_filter_nodes_by_type(self, sqlite_store):
        await sqlite_store.create_user(UserProfile(user_id="test-1"))

        await sqlite_store.save_node(
            KnowledgeNode(
                node_id="n1", user_id="test-1", node_type=NodeType.TOPIC, name="AI"
            )
        )
        await sqlite_store.save_node(
            KnowledgeNode(
                node_id="n2",
                user_id="test-1",
                node_type=NodeType.PERSON,
                name="Sam Altman",
            )
        )

        topics = await sqlite_store.get_nodes("test-1", NodeType.TOPIC)
        assert len(topics) == 1
        assert topics[0].name == "AI"

    async def test_save_edge_and_get_related(self, sqlite_store):
        await sqlite_store.create_user(UserProfile(user_id="test-1"))

        await sqlite_store.save_node(
            KnowledgeNode(
                node_id="n1", user_id="test-1", node_type=NodeType.TOPIC, name="AI"
            )
        )
        await sqlite_store.save_node(
            KnowledgeNode(
                node_id="n2",
                user_id="test-1",
                node_type=NodeType.PERSON,
                name="Sam Altman",
            )
        )

        edge = KnowledgeEdge(
            edge_id="e1",
            user_id="test-1",
            source_node_id="n1",
            target_node_id="n2",
            relation_type="related_person",
        )
        await sqlite_store.save_edge(edge)

        related = await sqlite_store.get_related_nodes("n1")
        assert len(related) == 1
        node, relation = related[0]
        assert node.name == "Sam Altman"
        assert relation == "related_person"
