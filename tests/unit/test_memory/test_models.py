"""記憶系統資料模型測試"""

import pytest
from pydantic import ValidationError

from src.memory.models.feedback import FeedbackSeverity, FeedbackType, UserFeedback
from src.memory.models.knowledge_graph import KnowledgeEdge, KnowledgeNode, NodeType
from src.memory.models.learned_correction import LearnedCorrection
from src.memory.models.user_profile import (
    AnalysisDepth,
    ContentStyle,
    SourceTrust,
    TopicPreference,
    UserProfile,
)


class TestUserProfile:
    def test_defaults(self):
        profile = UserProfile(user_id="test")
        assert profile.preferred_style == ContentStyle.CASUAL
        assert profile.analysis_depth == AnalysisDepth.STANDARD
        assert profile.language == "zh-TW"
        assert profile.auto_learn_from_feedback is True

    def test_topic_preferences(self):
        profile = UserProfile(
            user_id="test",
            topic_preferences={
                "AI": TopicPreference(topic="AI", interest_level=0.9),
            },
        )
        assert profile.topic_preferences["AI"].interest_level == 0.9

    def test_feedback_weight_validation(self):
        with pytest.raises(ValidationError):
            UserProfile(user_id="test", feedback_weight=0.0)
        with pytest.raises(ValidationError):
            UserProfile(user_id="test", feedback_weight=1.5)


class TestSourceTrust:
    def test_defaults(self):
        trust = SourceTrust(source_name="PTT")
        assert trust.trust_level == 0.5

    def test_trust_level_validation(self):
        with pytest.raises(ValidationError):
            SourceTrust(source_name="PTT", trust_level=1.5)


class TestUserFeedback:
    def test_create(self):
        fb = UserFeedback(
            feedback_id="fb-1",
            user_id="user-1",
            session_id="sess-1",
            original_content="content",
            original_analysis="analysis",
            agent_type="deep_analyzer",
            feedback_type=FeedbackType.CORRECTION,
            user_correction="correction",
        )
        assert fb.processed is False
        assert fb.severity == FeedbackSeverity.MODERATE


class TestLearnedCorrection:
    def test_create(self):
        c = LearnedCorrection(
            correction_id="c-1",
            user_id="user-1",
            pattern="pattern",
            correction="correction",
            context="context",
        )
        assert c.confidence == 0.5
        assert c.times_applied == 0

    def test_confidence_validation(self):
        with pytest.raises(ValidationError):
            LearnedCorrection(
                correction_id="c-1",
                user_id="user-1",
                pattern="p",
                correction="c",
                context="ctx",
                confidence=1.5,
            )


class TestKnowledgeNode:
    def test_create(self):
        node = KnowledgeNode(
            node_id="n-1",
            user_id="user-1",
            node_type=NodeType.TOPIC,
            name="AI",
        )
        assert node.user_sentiment == 0.0
        assert node.interaction_count == 0


class TestKnowledgeEdge:
    def test_create(self):
        edge = KnowledgeEdge(
            edge_id="e-1",
            user_id="user-1",
            source_node_id="n-1",
            target_node_id="n-2",
            relation_type="related_to",
        )
        assert edge.weight == 0.5
        assert edge.user_confirmed is False
