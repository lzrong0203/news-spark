"""話題輸入元件"""

import streamlit as st

from src.models.content import ResearchRequest


def render_topic_input() -> ResearchRequest | None:
    """渲染話題輸入元件

    Returns:
        ResearchRequest 或 None (使用者未提交)
    """
    st.markdown("### 研究設定")

    topic = st.text_input(
        "研究主題",
        value="",
        placeholder="例: AI 取代工作、台積電營收、加密貨幣趨勢",
        help="輸入你想深入研究的話題",
    )

    sources = st.multiselect(
        "資料來源",
        options=["news", "social", "forum"],
        default=["news", "social", "forum"],
        format_func=lambda x: {"news": "新聞", "social": "社群", "forum": "論壇"}[x],
    )

    tone = st.select_slider(
        "內容調性",
        options=["嚴肅", "中性", "輕鬆", "幽默"],
        value="中性",
    )

    depth = st.slider(
        "研究深度", min_value=1, max_value=5, value=2, help="1=快速掃描, 5=深度研究"
    )

    max_results = st.slider("每來源最大結果數", min_value=5, max_value=30, value=10)

    # 儲存 tone 到 session state 供後續使用
    st.session_state["research_tone"] = tone

    if st.button("開始分析", type="primary", use_container_width=True):
        if not topic.strip():
            st.warning("請輸入研究主題")
            return None
        return ResearchRequest(
            topic=topic.strip(),
            sources=sources,
            depth=depth,
            max_results_per_source=max_results,
            tone=tone,
        )

    return None
