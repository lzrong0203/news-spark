"""LangGraph 圖節點實作

每個節點是一個函式，接收 ResearchState 並回傳部分更新的 dict。
"""

import logging

from src.agents.content_synthesizer import (
    ContentSynthesizerAgent,
    ContentSynthesizerInput,
)
from src.agents.deep_analyzer import DeepAnalyzerAgent, DeepAnalyzerInput
from src.agents.news_scraper import NewsScraperAgent, NewsScraperInput
from src.agents.social_media import SocialMediaAgent, SocialMediaInput
from src.agents.supervisor import SupervisorAgent, SupervisorInput
from src.graph.state import ResearchState

logger = logging.getLogger(__name__)


async def supervisor_node(state: ResearchState) -> dict:
    """主管節點: 分解查詢"""
    request = state["request"]
    agent = SupervisorAgent()
    result = await agent(SupervisorInput(request=request))

    if not result.success:
        return {
            "error": result.error,
            "current_step": "supervisor_failed",
            "execution_log": state.get("execution_log", [])
            + [f"Supervisor failed: {result.error}"],
        }

    plan = result.data.plan
    return {
        "sub_queries": plan.sub_queries,
        "current_step": "queries_decomposed",
        "execution_log": state.get("execution_log", [])
        + [f"Decomposed into {len(plan.sub_queries)} sub-queries: {plan.sub_queries}"],
    }


async def news_scraper_node(state: ResearchState) -> dict:
    """新聞抓取節點"""
    request = state["request"]

    if "news" not in request.sources:
        return {
            "news_results": [],
            "current_step": "news_scraped",
            "execution_log": state.get("execution_log", [])
            + ["News: skipped (not in selected sources)"],
        }

    agent = NewsScraperAgent()
    result = await agent(
        NewsScraperInput(
            queries=state["sub_queries"],
            max_results_per_source=request.max_results_per_source,
            language=request.language,
        )
    )

    news_items = result.data.items if result.success else []
    errors = result.data.errors if result.success and result.data.errors else []

    log_entries = [
        f"News: {len(news_items)} items from {result.data.sources_used if result.success else []}"
    ]
    if errors:
        log_entries.extend([f"News error: {e}" for e in errors])

    return {
        "news_results": news_items,
        "current_step": "news_scraped",
        "total_sources_scraped": state.get("total_sources_scraped", 0)
        + len(news_items),
        "execution_log": state.get("execution_log", []) + log_entries,
    }


async def social_media_node(state: ResearchState) -> dict:
    """社群媒體抓取節點"""
    request = state["request"]
    agent = SocialMediaAgent()

    platforms = []
    if "social" in request.sources:
        platforms.append("threads")
    if "forum" in request.sources:
        platforms.append("ptt")

    if not platforms:
        return {
            "forum_results": [],
            "social_results": [],
            "current_step": "social_scraped",
            "execution_log": state.get("execution_log", [])
            + ["Social: skipped (not in selected sources)"],
        }

    result = await agent(
        SocialMediaInput(
            queries=state["sub_queries"],
            platforms=platforms,
            language=request.language,
            max_results_per_source=request.max_results_per_source,
        )
    )

    forum_items = result.data.forum_items if result.success else []
    social_items = result.data.social_items if result.success else []
    errors = result.data.errors if result.success and result.data.errors else []

    log_entries = [
        f"Social: {len(social_items)} items, Forum: {len(forum_items)} items"
    ]
    if errors:
        log_entries.extend([f"Social error: {e}" for e in errors])

    return {
        "forum_results": forum_items,
        "social_results": social_items,
        "current_step": "social_scraped",
        "total_sources_scraped": state.get("total_sources_scraped", 0)
        + len(forum_items)
        + len(social_items),
        "execution_log": state.get("execution_log", []) + log_entries,
    }


async def deep_analyzer_node(state: ResearchState) -> dict:
    """深度分析節點"""
    all_items = (
        state.get("news_results", [])
        + state.get("social_results", [])
        + state.get("forum_results", [])
    )

    request = state["request"]
    agent = DeepAnalyzerAgent()
    result = await agent(
        DeepAnalyzerInput(
            topic=request.topic,
            content_items=all_items,
            depth=request.depth,
            language=request.language,
        )
    )

    if not result.success:
        return {
            "error": result.error,
            "current_step": "analysis_failed",
            "execution_log": state.get("execution_log", [])
            + [f"Analysis failed: {result.error}"],
        }

    return {
        "analysis": result.data,
        "current_step": "analysis_complete",
        "execution_log": state.get("execution_log", [])
        + [
            f"Analysis complete: {len(result.data.key_insights)} insights, confidence={result.data.confidence_score}"
        ],
    }


async def content_synthesizer_node(state: ResearchState) -> dict:
    """內容合成節點"""
    all_items = (
        state.get("news_results", [])
        + state.get("social_results", [])
        + state.get("forum_results", [])
    )

    request = state["request"]
    agent = ContentSynthesizerAgent()
    result = await agent(
        ContentSynthesizerInput(
            topic=request.topic,
            analysis=state["analysis"],
            content_items=all_items,
            tone=request.tone,
        )
    )

    if not result.success:
        return {
            "error": result.error,
            "current_step": "synthesis_failed",
            "execution_log": state.get("execution_log", [])
            + [f"Synthesis failed: {result.error}"],
        }

    return {
        "video_material": result.data,
        "current_step": "complete",
        "execution_log": state.get("execution_log", [])
        + [f"Synthesis complete: {result.data.title_suggestion}"],
    }
