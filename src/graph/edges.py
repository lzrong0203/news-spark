"""LangGraph 條件邊邏輯

定義節點之間的路由決策。
"""

from src.graph.state import ResearchState


def should_continue_after_supervisor(state: ResearchState) -> str:
    """主管節點後的路由"""
    if state.get("error"):
        return "error_handler"
    if not state.get("sub_queries"):
        return "error_handler"
    return "news_scraper"


def should_continue_after_scraping(state: ResearchState) -> str:
    """抓取完成後的路由"""
    total = (
        len(state.get("news_results", []))
        + len(state.get("social_results", []))
        + len(state.get("forum_results", []))
    )
    if total == 0:
        return "error_handler"
    return "deep_analyzer"


def should_continue_after_analysis(state: ResearchState) -> str:
    """分析完成後的路由"""
    if state.get("error"):
        return "error_handler"
    if not state.get("analysis"):
        return "error_handler"
    return "content_synthesizer"


async def error_handler_node(state: ResearchState) -> dict:
    """錯誤處理節點"""
    error_msg = state.get("error", "未知錯誤: 無資料或處理失敗")
    return {
        "current_step": "error",
        "execution_log": state.get("execution_log", []) + [f"ERROR: {error_msg}"],
    }
