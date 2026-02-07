"""使用者檔案資料模型"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ContentStyle(str, Enum):
    """內容風格"""

    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    SIMPLIFIED = "simplified"


class AnalysisDepth(str, Enum):
    """分析深度"""

    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class TopicPreference(BaseModel):
    """使用者對特定話題的偏好"""

    topic: str
    interest_level: float = Field(ge=0.0, le=1.0, default=0.5)
    perspective_notes: str = ""
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceTrust(BaseModel):
    """使用者對新聞來源的信任度"""

    source_name: str
    source_url: str | None = None
    trust_level: float = Field(ge=0.0, le=1.0, default=0.5)
    notes: str = ""


class UserProfile(BaseModel):
    """完整的使用者檔案"""

    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 基本偏好
    display_name: str | None = None
    language: str = "zh-TW"
    timezone: str = "Asia/Taipei"

    # 內容偏好
    preferred_style: ContentStyle = ContentStyle.CASUAL
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD

    # 話題偏好
    topic_preferences: dict[str, TopicPreference] = Field(default_factory=dict)

    # 來源偏好
    trusted_sources: list[SourceTrust] = Field(default_factory=list)
    blocked_sources: list[str] = Field(default_factory=list)

    # 觀點元數據
    professional_background: str | None = None
    areas_of_expertise: list[str] = Field(default_factory=list)

    # 學習設定
    auto_learn_from_feedback: bool = True
    feedback_weight: float = Field(ge=0.1, le=1.0, default=0.7)
