"""研究進度追蹤元件"""

import streamlit as st


# 步驟定義
STEPS = [
    ("查詢分解", "queries_decomposed"),
    ("新聞抓取", "news_scraped"),
    ("社群抓取", "social_scraped"),
    ("深度分析", "analysis_complete"),
    ("素材生成", "complete"),
]


def render_progress(current_step: str | None) -> None:
    """渲染研究進度

    Args:
        current_step: 目前步驟 ID
    """
    if current_step is None:
        return

    step_ids = [s[1] for s in STEPS]

    # 找到目前步驟的索引
    if current_step == "error":
        current_idx = -1
    elif current_step in step_ids:
        current_idx = step_ids.index(current_step)
    else:
        current_idx = -1

    cols = st.columns(len(STEPS))
    for i, (label, _) in enumerate(STEPS):
        with cols[i]:
            if i < current_idx:
                st.markdown(f"✅ **{label}**")
            elif i == current_idx:
                st.markdown(f"🔄 **{label}**")
            else:
                st.markdown(f"⏳ {label}")

    if current_step == "error":
        st.error("研究流程中發生錯誤")

    # 進度條
    if current_idx >= 0:
        progress = (current_idx + 1) / len(STEPS)
        st.progress(progress)
