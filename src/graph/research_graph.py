"""主研究工作流

使用 LangGraph StateGraph 建構完整的研究管線。

流程:
supervisor -> news_scraper -> social_media -> deep_analyzer -> content_synthesizer -> END
                                                                                      |
              error_handler <-- (任何節點失敗) ----------------------------------------+-> END
"""

from langgraph.graph import END, StateGraph

from src.graph.edges import (
    error_handler_node,
    should_continue_after_analysis,
    should_continue_after_scraping,
    should_continue_after_supervisor,
)
from src.graph.nodes import (
    content_synthesizer_node,
    deep_analyzer_node,
    news_scraper_node,
    social_media_node,
    supervisor_node,
)
from src.graph.state import ResearchState


def build_research_graph() -> StateGraph:
    """建構研究工作流圖"""
    graph = StateGraph(ResearchState)

    # 新增節點
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("news_scraper", news_scraper_node)
    graph.add_node("social_media", social_media_node)
    graph.add_node("deep_analyzer", deep_analyzer_node)
    graph.add_node("content_synthesizer", content_synthesizer_node)
    graph.add_node("error_handler", error_handler_node)

    # 設定入口
    graph.set_entry_point("supervisor")

    # 主管 -> 新聞抓取 或 錯誤
    graph.add_conditional_edges(
        "supervisor",
        should_continue_after_supervisor,
        {
            "news_scraper": "news_scraper",
            "error_handler": "error_handler",
        },
    )

    # 新聞抓取 -> 社群抓取
    graph.add_edge("news_scraper", "social_media")

    # 社群抓取 -> 深度分析 或 錯誤
    graph.add_conditional_edges(
        "social_media",
        should_continue_after_scraping,
        {
            "deep_analyzer": "deep_analyzer",
            "error_handler": "error_handler",
        },
    )

    # 深度分析 -> 內容合成 或 錯誤
    graph.add_conditional_edges(
        "deep_analyzer",
        should_continue_after_analysis,
        {
            "content_synthesizer": "content_synthesizer",
            "error_handler": "error_handler",
        },
    )

    # 合成 -> 結束
    graph.add_edge("content_synthesizer", END)
    graph.add_edge("error_handler", END)

    return graph


def create_research_workflow():
    """建立可執行的研究工作流

    Returns:
        已編譯的 LangGraph 工作流
    """
    graph = build_research_graph()
    return graph.compile()


async def run_research(initial_state: dict) -> dict:
    """執行完整研究流程

    Args:
        initial_state: 包含 ResearchRequest 的初始狀態，例如:
            {
                "request": ResearchRequest(topic="AI 趨勢"),
                "execution_log": [],
            }

    Returns:
        最終的 ResearchState dict
    """
    workflow = create_research_workflow()
    result = await workflow.ainvoke(initial_state)
    return result
