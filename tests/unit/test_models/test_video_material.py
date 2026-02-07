"""VideoMaterial 模型測試"""

import pytest
from pydantic import ValidationError

from src.models.video_material import PlatformVariant, SourceItem, VideoMaterial


class TestVideoMaterial:
    def test_create_full(self, sample_video_material):
        assert sample_video_material.topic == "AI 取代工作"
        assert sample_video_material.viral_score == 0.85
        assert len(sample_video_material.platform_variants) == 1
        assert len(sample_video_material.sources) == 1

    def test_viral_score_validation(self):
        with pytest.raises(ValidationError):
            VideoMaterial(
                topic="test",
                title_suggestion="test",
                hook_line="test",
                key_talking_points=["a"],
                visual_suggestions=["a"],
                viral_score=1.5,
                target_emotion="test",
                call_to_action="test",
                hashtag_suggestions=["a"],
                generated_at="2025-01-01",
            )


class TestPlatformVariant:
    def test_defaults(self):
        variant = PlatformVariant(platform="TikTok", duration="15-60s")
        assert variant.format == "vertical"
        assert variant.aspect_ratio == "9:16"


class TestSourceItem:
    def test_create(self):
        source = SourceItem(
            title="Test Source",
            url="https://example.com",
            source_type="news",
        )
        assert source.published_at is None
