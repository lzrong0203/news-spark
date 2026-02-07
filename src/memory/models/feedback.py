"""使用者反饋資料模型"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    """反饋類型"""

    CORRECTION = "correction"
    DISAGREEMENT = "disagreement"
    PREFERENCE = "preference"
    RELEVANCE = "relevance"
    QUALITY = "quality"


class FeedbackSeverity(str, Enum):
    """反饋嚴重度"""

    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class UserFeedback(BaseModel):
    """單筆使用者反饋"""

    feedback_id: str
    user_id: str
    session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 上下文
    original_content: str
    original_analysis: str
    agent_type: str

    # 反饋詳情
    feedback_type: FeedbackType
    severity: FeedbackSeverity = FeedbackSeverity.MODERATE
    user_correction: str
    user_explanation: str | None = None

    # 學習元數據
    topics: list[str] = Field(default_factory=list)
    sources_mentioned: list[str] = Field(default_factory=list)

    # 處理狀態
    processed: bool = False
    learned_at: datetime | None = None
