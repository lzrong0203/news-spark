"""News Spark - AI 驅動的新聞分析與短片素材產生器."""

import sys
from pathlib import Path

# 確保專案根目錄在 sys.path，讓 pages 和 components 能匯入 src.*
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio  # noqa: E402
import html as html_module  # noqa: E402
import logging  # noqa: E402
from datetime import datetime  # noqa: E402

import streamlit as st  # noqa: E402

from components.feedback_panel import render_feedback_panel  # noqa: E402
from components.history_store import load_history, save_history  # noqa: E402
from components.progress_tracker import render_progress  # noqa: E402
from components.results_display import render_video_material  # noqa: E402
from components.topic_input import render_topic_input  # noqa: E402
from src.graph.research_graph import run_research  # noqa: E402

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run async coroutine, handling case where event loop already exists."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _esc(value: object) -> str:
    """HTML 轉義，防止 XSS"""
    return html_module.escape(str(value))


st.set_page_config(
    page_title="News Spark",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tech Innovation 主題樣式 (Electric Blue + Neon Cyan)
st.markdown(
    """
    <style>
    /* Tech Innovation 主題 - Electric Blue #0066ff, Neon Cyan #00ffff, Dark Gray #1e1e1e, White #ffffff */

    /* 全局深色背景 */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1e1e1e 50%, #141428 100%);
    }

    /* 卡片樣式 */
    .card {
        background: linear-gradient(145deg, #1a1a2a 0%, #222233 100%);
        border: 1px solid #0066ff33;
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
        box-shadow: 0 8px 32px rgba(0, 102, 255, 0.1);
    }

    .card-title {
        color: #ffffff;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Hook Line 特殊樣式 */
    .hook-box {
        background: linear-gradient(135deg, #0066ff 0%, #0044cc 100%);
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
        color: white;
        font-size: 1.4rem;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 102, 255, 0.4);
    }

    /* 標籤樣式 */
    .tag {
        display: inline-block;
        background: linear-gradient(135deg, #00ffff 0%, #0066ff 100%);
        color: #1e1e1e;
        padding: 6px 14px;
        border-radius: 20px;
        margin: 4px;
        font-size: 0.9rem;
        font-weight: 600;
    }

    .tag-emotion {
        background: linear-gradient(135deg, #00ffff 0%, #00cccc 100%);
        color: #1e1e1e;
    }

    /* 分數進度條 */
    .score-bar {
        background: #2a2a3a;
        border-radius: 10px;
        height: 12px;
        overflow: hidden;
        margin: 8px 0;
    }

    .score-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }

    .score-high {
        background: linear-gradient(90deg, #00ffff 0%, #0066ff 100%);
    }

    .score-medium {
        background: linear-gradient(90deg, #0066ff 0%, #4488ff 100%);
    }

    .score-low {
        background: linear-gradient(90deg, #334466 0%, #445577 100%);
    }

    /* 平台卡片 */
    .platform-card {
        background: linear-gradient(145deg, #1a1a2a 0%, #222233 100%);
        border: 1px solid #0066ff33;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }

    .platform-icon {
        font-size: 2rem;
        margin-bottom: 8px;
    }

    /* 論點列表 */
    .talking-point {
        background: rgba(0, 102, 255, 0.08);
        border-left: 4px solid #0066ff;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
        color: #ffffff;
    }

    /* 視覺建議 */
    .visual-tip {
        background: rgba(0, 255, 255, 0.06);
        border-left: 4px solid #00ffff;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
        color: #ffffff;
    }

    /* CTA 按鈕樣式 */
    .cta-box {
        background: linear-gradient(135deg, #0066ff 0%, #00ccff 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
        box-shadow: 0 4px 20px rgba(0, 102, 255, 0.4);
    }

    /* 來源卡片 */
    .source-item {
        background: rgba(0, 102, 255, 0.05);
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .source-type {
        background: #0066ff22;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        color: #00ffff;
    }

    /* 隱藏 Streamlit 預設元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 側邊欄樣式 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111118 0%, #1a1a2a 100%);
    }

    /* 標題樣式 */
    h1, h2, h3 {
        color: #ffffff !important;
    }

    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0066ff 0%, #00ffff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 8px;
    }

    .subtitle {
        color: #7788aa;
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 32px;
    }

    /* 指標卡片 */
    .metric-card {
        background: linear-gradient(145deg, #1a1a2a 0%, #222233 100%);
        border: 1px solid #0066ff33;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0066ff 0%, #00ffff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .metric-label {
        color: #7788aa;
        font-size: 0.9rem;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state 初始化 ─────────────────────────────────────────

if "research_result" not in st.session_state:
    st.session_state.research_result = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "research_history" not in st.session_state:
    st.session_state.research_history = load_history()


def _handle_feedback(
    feedback_type: str, correction: str, explanation: str | None
) -> None:
    """處理反饋提交"""
    if "feedback_history" not in st.session_state:
        st.session_state.feedback_history = []
    st.session_state.feedback_history = [
        *st.session_state.feedback_history,
        {
            "type": feedback_type,
            "correction": correction,
            "explanation": explanation,
        },
    ]


# ── Demo 模式的模擬資料與渲染函式 ────────────────────────────────


def get_mock_data() -> dict:
    """取得模擬的影片素材資料."""
    return {
        "topic": "AI 取代工作潮：2025 年職場生存指南",
        "title_suggestion": "🚨 這 5 種工作即將被 AI 取代！你的職業安全嗎？",
        "hook_line": "「你知道嗎？根據最新研究，未來 3 年內，有 40% 的工作將被 AI 取代...而你現在做的工作，可能就在名單上。」",
        "key_talking_points": [
            "OpenAI 最新報告：GPT-5 將具備完整的自主代理能力，能獨立完成複雜任務",
            "最危險的 5 種職業：客服、翻譯、基礎程式設計、數據輸入、內容審核",
            "反轉：創意工作、情感連結、複雜決策仍是人類優勢",
            "具體行動：學習 AI 協作、培養跨領域能力、建立個人品牌",
            "成功案例：某行銷人員轉型 AI 提示工程師，薪水翻倍",
        ],
        "visual_suggestions": [
            "📊 開場：快速剪輯各大科技公司裁員新聞畫面",
            "🤖 中段：AI 與人類並排工作的對比動畫",
            "📈 數據：動態圖表顯示 AI 採用率成長曲線",
            "💡 結尾：希望感的光芒效果 + 行動號召文字",
        ],
        "viral_score": 0.85,
        "target_emotion": "焦慮轉希望",
        "controversy_level": "medium",
        "call_to_action": "追蹤我，獲取更多 AI 時代生存技巧！留言告訴我你的職業，我幫你分析！",
        "hashtag_suggestions": [
            "#AI取代工作",
            "#職場生存",
            "#人工智慧",
            "#2025趨勢",
            "#職涯規劃",
            "#科技新聞",
            "#ChatGPT",
        ],
        "platform_variants": [
            {
                "platform": "TikTok",
                "icon": "🎵",
                "duration": "60 秒",
                "aspect_ratio": "9:16",
                "tips": [
                    "前 3 秒必須抓住注意力",
                    "使用熱門音樂增加曝光",
                    "文字要大、要清楚",
                    "結尾要有強烈 CTA",
                ],
            },
            {
                "platform": "YouTube Shorts",
                "icon": "📺",
                "duration": "≤60 秒",
                "aspect_ratio": "9:16",
                "tips": [
                    "標題要包含關鍵字",
                    "縮圖要吸睛",
                    "可以引導到長影片",
                    "善用置頂留言",
                ],
            },
            {
                "platform": "Instagram Reels",
                "icon": "📸",
                "duration": "30-90 秒",
                "aspect_ratio": "9:16",
                "tips": [
                    "視覺美感優先",
                    "善用 hashtag 策略",
                    "限時動態預熱",
                    "互動貼紙增加參與",
                ],
            },
        ],
        "sources": [
            {
                "title": "OpenAI 發布 GPT-5 功能預覽",
                "url": "https://example.com/openai-gpt5",
                "source_type": "新聞",
                "published_at": "2025-01-28",
            },
            {
                "title": "PTT 熱議：AI 時代該學什麼",
                "url": "https://example.com/ptt-ai",
                "source_type": "論壇",
                "published_at": "2025-01-30",
            },
            {
                "title": "LinkedIn：科技業裁員潮分析",
                "url": "https://example.com/linkedin-layoffs",
                "source_type": "社群",
                "published_at": "2025-01-29",
            },
        ],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "confidence_score": 0.88,
    }


def render_score_bar(score: float, label: str) -> None:
    """渲染分數進度條."""
    if score >= 0.7:
        color_class = "score-high"
    elif score >= 0.4:
        color_class = "score-medium"
    else:
        color_class = "score-low"

    st.markdown(
        f"""
        <div style="color: #a0a0cc; font-size: 0.9rem; margin-bottom: 4px;">{_esc(label)}</div>
        <div class="score-bar">
            <div class="score-fill {color_class}" style="width: {score * 100}%;"></div>
        </div>
        <div style="color: #e0e0ff; font-size: 1.1rem; font-weight: 600;">{score:.0%}</div>
        """,
        unsafe_allow_html=True,
    )


def _render_metric_cards(data: dict) -> None:
    """渲染頂部指標卡片."""
    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        (col1, f"{data['viral_score']:.0%}", "🔥 病毒傳播潛力"),
        (col2, str(len(data["key_talking_points"])), "💡 重點論述"),
        (col3, str(len(data["sources"])), "📚 資料來源"),
        (col4, str(len(data["hashtag_suggestions"])), "# Hashtags"),
    ]

    for col, value, label in metrics:
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{_esc(value)}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)


def _render_topic_and_hook(data: dict) -> None:
    """渲染主題、標題與 Hook Line."""
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">🎯 研究主題</div>
            <div style="color: #e0e0ff; font-size: 1.1rem;">{_esc(data["topic"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">✨ 建議標題</div>
            <div style="color: #f0f0ff; font-size: 1.3rem; font-weight: 600;">{_esc(data["title_suggestion"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">🎬 開場 Hook（前 3 秒）</div>
            <div class="hook-box">{_esc(data["hook_line"])}</div>
            <div style="color: #8888aa; font-size: 0.9rem; margin-top: 12px;">
                💡 目標情緒: <span class="tag tag-emotion">{_esc(data["target_emotion"])}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_talking_points_and_visuals(data: dict) -> None:
    """渲染論點與視覺建議."""
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">💬 關鍵論點</div>', unsafe_allow_html=True)
        for i, point in enumerate(data["key_talking_points"], 1):
            st.markdown(
                f'<div class="talking-point"><strong>{i}.</strong> {_esc(point)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-title">🎨 視覺呈現建議</div>', unsafe_allow_html=True
        )
        for tip in data["visual_suggestions"]:
            st.markdown(f'<div class="visual-tip">{_esc(tip)}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def _render_cta_and_hashtags(data: dict) -> None:
    """渲染 CTA 與 Hashtags."""
    col_cta, col_tags = st.columns([1, 1])

    with col_cta:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">📣 行動呼籲 (CTA)</div>
                <div class="cta-box">{_esc(data["call_to_action"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_tags:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-title"># 建議 Hashtags</div>', unsafe_allow_html=True
        )
        tags_html = "".join(
            [f'<span class="tag">{_esc(tag)}</span>' for tag in data["hashtag_suggestions"]]
        )
        st.markdown(
            f'<div style="margin-top: 8px;">{tags_html}</div>', unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


def _render_platform_variants(data: dict) -> None:
    """渲染平台專屬建議."""
    st.markdown(
        """
        <div class="card">
            <div class="card-title">📱 多平台專屬版本</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    platform_cols = st.columns(len(data["platform_variants"]))
    for col, variant in zip(platform_cols, data["platform_variants"]):
        with col:
            tips_html = "".join(
                [
                    f"<li style='color: #a0a0cc; margin: 6px 0;'>{_esc(tip)}</li>"
                    for tip in variant["tips"]
                ]
            )
            st.markdown(
                f"""
                <div class="platform-card">
                    <div class="platform-icon">{_esc(variant["icon"])}</div>
                    <div style="color: #e0e0ff; font-size: 1.2rem; font-weight: 600;">
                        {_esc(variant["platform"])}
                    </div>
                    <div style="color: #8888aa; font-size: 0.9rem; margin: 8px 0;">
                        ⏱️ {_esc(variant["duration"])} | 📐 {_esc(variant["aspect_ratio"])}
                    </div>
                    <ul style="padding-left: 20px; margin-top: 12px;">
                        {tips_html}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_sources(data: dict) -> None:
    """渲染資料來源."""
    st.markdown(
        """
        <div class="card">
            <div class="card-title">📚 資料來源</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for source in data["sources"]:
        source_icon = {"新聞": "📰", "論壇": "💬", "社群": "🔗"}.get(
            source["source_type"], "📄"
        )
        st.markdown(
            f"""
            <div class="source-item">
                <span style="font-size: 1.5rem;">{_esc(source_icon)}</span>
                <div style="flex: 1;">
                    <div style="color: #e0e0ff; font-weight: 500;">{_esc(source["title"])}</div>
                    <div style="color: #666; font-size: 0.8rem;">
                        {_esc(source.get("published_at", ""))}
                    </div>
                </div>
                <span class="source-type">{_esc(source["source_type"])}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── 主頁面 ──────────────────────────────────────────────────────

# 標題區
st.markdown('<div class="main-title">⚡ News Spark</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI 驅動的新聞分析與短片素材產生器</div>',
    unsafe_allow_html=True,
)

# 側邊欄 - 研究設定
with st.sidebar:
    request = render_topic_input()

# 執行研究
if request and not st.session_state.is_running:
    st.session_state.is_running = True
    st.session_state.research_result = None

    with st.spinner("研究進行中... 這可能需要一些時間"):
        try:
            result = _run_async(
                run_research(
                    {
                        "request": request,
                        "execution_log": [],
                        "total_sources_scraped": 0,
                    }
                )
            )
            st.session_state.research_result = result
            video_mat = result.get("video_material")
            st.session_state.research_history = [
                *st.session_state.research_history,
                {
                    "topic": request.topic,
                    "video_material": video_mat.model_dump()
                    if hasattr(video_mat, "model_dump")
                    else video_mat,
                    "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                },
            ]
            save_history(st.session_state.research_history)
        except Exception:
            logger.exception("研究流程失敗")
            st.error("研究失敗，請稍後再試。如果問題持續，請聯繫管理員。")
            st.session_state.research_result = {
                "error": "研究流程發生非預期錯誤",
                "current_step": "error",
            }

    st.session_state.is_running = False
    st.rerun()

# 顯示結果
result = st.session_state.research_result

if result is not None:
    # 研究結果模式
    render_progress(result.get("current_step"))
    st.divider()

    if result.get("video_material"):
        render_video_material(result["video_material"])
        st.divider()
        render_feedback_panel(
            topic=result["video_material"].topic,
            on_submit=_handle_feedback,
        )
        with st.expander("📋 執行日誌", expanded=False):
            for log in result.get("execution_log", []):
                st.text(log)

    elif result.get("error"):
        st.error("研究失敗，請稍後再試。")
        with st.expander("📋 執行日誌", expanded=True):
            for log in result.get("execution_log", []):
                st.text(log)
else:
    # Demo 模式 - 顯示模擬資料
    data = get_mock_data()
    _render_metric_cards(data)
    _render_topic_and_hook(data)
    _render_talking_points_and_visuals(data)
    _render_cta_and_hashtags(data)
    _render_platform_variants(data)
    _render_sources(data)
