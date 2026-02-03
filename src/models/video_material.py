"""Video material data models for short-form video creation."""

from pydantic import BaseModel, Field


class PlatformVariant(BaseModel):
    """Platform-specific video variant configuration."""

    platform: str = Field(description="平台名稱")
    duration: str = Field(description="建議時長")
    format: str = Field(default="vertical", description="影片格式")
    aspect_ratio: str = Field(default="9:16", description="長寬比")
    tips: list[str] = Field(default_factory=list, description="平台專屬建議")


class SourceItem(BaseModel):
    """Source reference for research content."""

    title: str = Field(description="來源標題")
    url: str = Field(description="來源連結")
    source_type: str = Field(description="來源類型（新聞/社群/論壇）")
    published_at: str | None = Field(default=None, description="發布時間")


class VideoMaterial(BaseModel):
    """Generated video material for short-form content creation."""

    # 核心內容
    topic: str = Field(description="研究主題")
    title_suggestion: str = Field(description="建議標題")
    hook_line: str = Field(description="開場 hook（前 0-3 秒吸引注意力）")
    key_talking_points: list[str] = Field(
        description="主要論點（3-5 個重點）"
    )

    # 視覺建議
    visual_suggestions: list[str] = Field(
        description="視覺呈現建議（鏡頭、特效、文字疊加）"
    )

    # 分析指標
    viral_score: float = Field(
        ge=0.0, le=1.0, description="病毒傳播潛力分數 (0-1)"
    )
    target_emotion: str = Field(
        description="目標情緒反應（幽默/震驚/啟發/憤怒/感動）"
    )
    controversy_level: str = Field(
        default="medium",
        description="爭議程度（low/medium/high）",
    )

    # 行動呼籲
    call_to_action: str = Field(description="行動呼籲文字")
    hashtag_suggestions: list[str] = Field(
        description="建議 hashtags"
    )

    # 多平台變體
    platform_variants: list[PlatformVariant] = Field(
        default_factory=list, description="各平台專屬版本"
    )

    # 來源參考
    sources: list[SourceItem] = Field(
        default_factory=list, description="資料來源"
    )

    # 額外元資料
    generated_at: str = Field(description="生成時間")
    confidence_score: float = Field(
        ge=0.0, le=1.0, default=0.8, description="內容信心度"
    )
