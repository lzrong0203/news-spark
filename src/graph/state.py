"""LangGraph 狀態定義

定義研究工作流的共享狀態結構。
"""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages

from src.models.content import AnalysisResult, ContentItem, ResearchRequest
from src.models.video_material import VideoMaterial


class ResearchState(TypedDict, total=False):
    """研究工作流狀態

    此狀態在 LangGraph 節點之間傳遞，包含研究過程的所有資料。
    """

    # === 輸入 ===
    request: ResearchRequest  # 原始研究請求

    # === 中間狀態 ===
    sub_queries: list[str]  # 分解後的子查詢
    news_results: list[ContentItem]  # 新聞來源結果
    social_results: list[ContentItem]  # 社群來源結果
    forum_results: list[ContentItem]  # 論壇來源結果
    web_results: list[ContentItem]  # 網頁搜尋結果

    # === 分析結果 ===
    analysis: AnalysisResult  # 深度分析結果

    # === 最終輸出 ===
    video_material: VideoMaterial  # 影片素材

    # === 對話歷史 (可選) ===
    messages: Annotated[list, add_messages]

    # === 錯誤處理 ===
    error: str | None  # 錯誤訊息
    current_step: str  # 目前步驟名稱

    # === 元數據 ===
    total_sources_scraped: int  # 已抓取來源數
    execution_log: list[str]  # 執行日誌
