"""內容資料模型

定義新聞和社群內容的統一資料結構。
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class EngagementMetrics(BaseModel):
    """互動指標"""

    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int | None = None


class ContentItem(BaseModel):
    """統一內容項目模型

    用於表示來自不同來源的內容（新聞、社群、論壇）。
    """

    # 基本資訊
    title: str = Field(..., description="標題")
    url: HttpUrl | str = Field(..., description="原始連結")
    content: str = Field(default="", description="內容摘要或全文")
    summary: str | None = Field(default=None, description="AI 生成摘要")

    # 來源資訊
    source_type: Literal["news", "social", "forum", "web"] = Field(
        ..., description="來源類型"
    )
    source_name: str = Field(..., description="來源名稱 (如: NewsAPI, PTT, Threads)")
    source_url: HttpUrl | str | None = Field(default=None, description="來源網站")

    # 作者資訊
    author: str | None = Field(default=None, description="作者名稱")
    author_url: HttpUrl | str | None = Field(default=None, description="作者連結")

    # 時間
    published_at: datetime | None = Field(default=None, description="發布時間")
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="抓取時間"
    )

    # 互動指標
    engagement: EngagementMetrics | None = Field(
        default=None, description="互動指標 (社群來源)"
    )

    # 分類標籤
    categories: list[str] = Field(default_factory=list, description="分類")
    tags: list[str] = Field(default_factory=list, description="標籤")

    # 語言和地區
    language: str = Field(default="zh-TW", description="語言")
    region: str | None = Field(default=None, description="地區")

    # 附加媒體
    image_url: HttpUrl | str | None = Field(default=None, description="圖片連結")
    video_url: HttpUrl | str | None = Field(default=None, description="影片連結")

    # 元數據
    raw_data: dict | None = Field(default=None, description="原始資料 (除錯用)")


class ResearchRequest(BaseModel):
    """研究請求模型"""

    topic: str = Field(..., min_length=1, description="研究話題")
    user_id: str = Field(default="anonymous", description="使用者 ID")
    language: str = Field(default="zh-TW", description="語言")
    sources: list[str] = Field(
        default_factory=lambda: ["news", "social", "forum"],
        description="資料來源類型",
    )
    depth: int = Field(default=2, ge=1, le=5, description="研究深度 (1-5)")
    max_results_per_source: int = Field(
        default=10, ge=1, le=50, description="每個來源最大結果數"
    )
    tone: str = Field(default="中性", description="內容調性 (嚴肅/中性/輕鬆/幽默)")


class AnalysisResult(BaseModel):
    """分析結果模型"""

    topic: str = Field(..., description="分析話題")
    key_insights: list[str] = Field(default_factory=list, description="關鍵洞察")
    controversies: list[str] = Field(default_factory=list, description="爭議點")
    trending_angles: list[str] = Field(default_factory=list, description="熱門角度")
    sentiment_summary: str = Field(default="", description="情緒摘要")
    recommended_hooks: list[str] = Field(default_factory=list, description="建議開場白")
    source_count: int = Field(default=0, description="來源數量")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="信心分數")
