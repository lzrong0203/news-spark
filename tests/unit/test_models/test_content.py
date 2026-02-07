"""ContentItem, ResearchRequest, AnalysisResult 模型測試"""

import pytest
from pydantic import ValidationError

from src.models.content import (
    AnalysisResult,
    ContentItem,
    EngagementMetrics,
    ResearchRequest,
)


class TestContentItem:
    def test_create_minimal(self):
        item = ContentItem(
            title="Test",
            url="https://example.com",
            source_type="news",
            source_name="Test",
        )
        assert item.title == "Test"
        assert item.content == ""
        assert item.language == "zh-TW"

    def test_create_with_engagement(self):
        item = ContentItem(
            title="Test",
            url="https://example.com",
            source_type="forum",
            source_name="PTT",
            engagement=EngagementMetrics(likes=100, comments=20),
        )
        assert item.engagement.likes == 100

    def test_source_type_validation(self):
        with pytest.raises(ValidationError):
            ContentItem(
                title="Test",
                url="https://example.com",
                source_type="invalid",
                source_name="Test",
            )


class TestResearchRequest:
    def test_defaults(self):
        req = ResearchRequest(topic="AI")
        assert req.depth == 2
        assert req.language == "zh-TW"
        assert "news" in req.sources

    def test_depth_validation(self):
        with pytest.raises(ValidationError):
            ResearchRequest(topic="AI", depth=0)
        with pytest.raises(ValidationError):
            ResearchRequest(topic="AI", depth=6)

    def test_empty_topic_rejected(self):
        with pytest.raises(ValidationError):
            ResearchRequest(topic="")


class TestAnalysisResult:
    def test_defaults(self):
        result = AnalysisResult(topic="AI")
        assert result.key_insights == []
        assert result.confidence_score == 0.0

    def test_confidence_validation(self):
        with pytest.raises(ValidationError):
            AnalysisResult(topic="AI", confidence_score=1.5)
