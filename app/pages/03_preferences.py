"""使用者偏好設定頁面"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st  # noqa: E402

from src.memory.models.user_profile import AnalysisDepth, ContentStyle  # noqa: E402

st.set_page_config(page_title="News Spark - 偏好", page_icon="⚙️", layout="wide")

st.title("⚙️ 使用者偏好設定")
st.markdown("設定你的研究偏好，系統會學習並提供更符合你需求的結果。")

# 初始化 session state
if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = {
        "preferred_style": ContentStyle.CASUAL.value,
        "analysis_depth": AnalysisDepth.STANDARD.value,
        "preferred_topics": [],
        "avoided_topics": [],
        "blocked_sources": [],
        "professional_background": "",
    }

prefs = st.session_state.user_preferences

col1, col2 = st.columns(2)

with col1:
    st.subheader("內容偏好")

    style = st.selectbox(
        "內容風格",
        options=[s.value for s in ContentStyle],
        index=[s.value for s in ContentStyle].index(prefs["preferred_style"]),
        format_func=lambda x: {
            "formal": "正式",
            "casual": "隨性",
            "technical": "技術",
            "simplified": "簡化",
        }[x],
    )

    depth = st.selectbox(
        "分析深度",
        options=[d.value for d in AnalysisDepth],
        index=[d.value for d in AnalysisDepth].index(prefs["analysis_depth"]),
        format_func=lambda x: {
            "brief": "簡要",
            "standard": "標準",
            "detailed": "詳細",
            "comprehensive": "全面",
        }[x],
    )

    background = st.text_input(
        "專業背景",
        value=prefs.get("professional_background", ""),
        placeholder="例: 軟體工程師、金融分析師、行銷主管",
    )

with col2:
    st.subheader("話題偏好")

    preferred_topics = st.text_area(
        "偏好話題 (每行一個)",
        value="\n".join(prefs.get("preferred_topics", [])),
        placeholder="AI\n半導體\n加密貨幣",
    )

    avoided_topics = st.text_area(
        "避開話題 (每行一個)",
        value="\n".join(prefs.get("avoided_topics", [])),
        placeholder="政治\n八卦",
    )

    blocked_sources = st.text_area(
        "封鎖的來源 (每行一個)",
        value="\n".join(prefs.get("blocked_sources", [])),
        placeholder="example.com\nspam-news.tw",
    )

st.divider()

if st.button("儲存設定", type="primary", use_container_width=True):
    st.session_state.user_preferences = {
        "preferred_style": style,
        "analysis_depth": depth,
        "professional_background": background,
        "preferred_topics": [
            t.strip() for t in preferred_topics.split("\n") if t.strip()
        ],
        "avoided_topics": [t.strip() for t in avoided_topics.split("\n") if t.strip()],
        "blocked_sources": [
            s.strip() for s in blocked_sources.split("\n") if s.strip()
        ],
    }
    st.success("偏好設定已儲存！")
