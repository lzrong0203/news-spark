"""反饋收集元件"""

import html as html_module
from collections.abc import Callable

import streamlit as st

FEEDBACK_TYPE_OPTIONS = {
    "correction": "事實修正",
    "disagreement": "不同意分析",
    "preference": "風格偏好",
    "quality": "品質評分",
}


def render_feedback_panel(
    topic: str,
    on_submit: Callable[[str, str, str | None], None],
) -> None:
    """渲染反饋收集面板

    Args:
        topic: 目前的研究主題
        on_submit: 提交回呼 (feedback_type, correction, explanation)
    """
    with st.expander("💡 提供反饋", expanded=False):
        st.markdown(f"針對「{html_module.escape(topic)}」的研究結果提供反饋")

        feedback_type = st.selectbox(
            "反饋類型",
            options=list(FEEDBACK_TYPE_OPTIONS.keys()),
            format_func=lambda x: FEEDBACK_TYPE_OPTIONS[x],
        )

        correction = st.text_area(
            "您的修正/建議",
            placeholder="請描述哪裡需要修正，或您希望看到什麼改變...",
        )

        explanation = st.text_area(
            "補充說明 (可選)",
            placeholder="為什麼這樣修正會更好？",
        )

        if st.button("提交反饋", key="submit_feedback"):
            if not correction.strip():
                st.warning("請填寫修正/建議內容")
            else:
                on_submit(
                    feedback_type,
                    correction.strip(),
                    explanation.strip() if explanation.strip() else None,
                )
                st.success("感謝您的反饋！系統會學習並改善未來的結果。")
