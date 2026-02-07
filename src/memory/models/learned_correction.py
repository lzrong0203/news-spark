"""學習到的修正資料模型"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class LearnedCorrection(BaseModel):
    """已處理的修正，成為系統知識的一部分"""

    correction_id: str
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 學習內容
    pattern: str = Field(..., description="要注意的模式")
    correction: str = Field(..., description="如何修正")
    context: str = Field(..., description="何時適用")

    # 學習元數據
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    times_applied: int = 0
    times_confirmed: int = 0
    times_rejected: int = 0

    # 向量嵌入鍵
    embedding_key: str | None = None
