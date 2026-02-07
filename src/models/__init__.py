"""Data models for News Spark."""

from src.models.content import (
    AnalysisResult,
    ContentItem,
    EngagementMetrics,
    ResearchRequest,
)
from src.models.video_material import (
    PlatformVariant,
    SourceItem,
    VideoMaterial,
)

__all__ = [
    # content.py
    "AnalysisResult",
    "ContentItem",
    "EngagementMetrics",
    "ResearchRequest",
    # video_material.py
    "PlatformVariant",
    "SourceItem",
    "VideoMaterial",
]
