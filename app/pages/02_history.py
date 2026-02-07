"""研究歷史頁面 — 完整研究細節檢視"""

import html as html_module
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st  # noqa: E402

from components.history_store import load_history  # noqa: E402

st.set_page_config(page_title="News Spark - 歷史", page_icon="📚", layout="wide")

st.title("📚 研究歷史")
st.markdown("查看過去的研究記錄。")

history = load_history()

# --- Controversy level display mapping ---
_CONTROVERSY_LABELS: dict[str, str] = {
    "low": "🟢 低",
    "medium": "🟡 中",
    "high": "🔴 高",
}

# --- Source type badge mapping ---
_SOURCE_BADGES: dict[str, str] = {
    "新聞": "📰",
    "社群": "💬",
    "論壇": "🗣️",
    "news": "📰",
    "social": "💬",
    "forum": "🗣️",
}


def _render_material(material: dict) -> list[str]:
    """Render a single VideoMaterial dict inside an expander."""

    # ── 1. Header metrics row ──────────────────────────────────────────
    viral_score = material.get("viral_score", 0)
    confidence_score = material.get("confidence_score", 0)
    target_emotion = material.get("target_emotion", "—")
    controversy_level = material.get("controversy_level", "medium")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("病毒分數", f"{viral_score:.0%}")
    col2.metric("信心度", f"{confidence_score:.0%}")
    col3.metric("目標情緒", html_module.escape(target_emotion))
    col4.metric(
        "爭議程度", _CONTROVERSY_LABELS.get(controversy_level, controversy_level)
    )

    st.divider()

    # ── 2. Title & Hook ────────────────────────────────────────────────
    title_suggestion = material.get("title_suggestion", "")
    hook_line = material.get("hook_line", "")

    if title_suggestion:
        st.markdown(
            f"**標題建議**: {html_module.escape(title_suggestion)}",
            unsafe_allow_html=True,
        )
    if hook_line:
        st.markdown(f"> {html_module.escape(hook_line)}")

    # ── 3. Key Talking Points ──────────────────────────────────────────
    talking_points: list[str] = material.get("key_talking_points", [])
    if talking_points:
        st.subheader("重點論述")
        for idx, point in enumerate(talking_points, 1):
            st.markdown(f"{idx}. {html_module.escape(point)}", unsafe_allow_html=True)

    # ── 4. Visual Suggestions ──────────────────────────────────────────
    visual_suggestions: list[str] = material.get("visual_suggestions", [])
    if visual_suggestions:
        st.subheader("視覺建議")
        for tip in visual_suggestions:
            st.markdown(f"- {html_module.escape(tip)}", unsafe_allow_html=True)

    # ── 5. CTA & Hashtags side by side ─────────────────────────────────
    cta = material.get("call_to_action", "")
    hashtags: list[str] = material.get("hashtag_suggestions", [])

    if cta or hashtags:
        left_col, right_col = st.columns(2)
        with left_col:
            st.subheader("行動呼籲")
            st.markdown(html_module.escape(cta) if cta else "—", unsafe_allow_html=True)
        with right_col:
            st.subheader("Hashtags")
            if hashtags:
                escaped_tags = [html_module.escape(tag) for tag in hashtags]
                st.markdown(", ".join(escaped_tags), unsafe_allow_html=True)
            else:
                st.markdown("—")

    # ── 6. Platform Variants ───────────────────────────────────────────
    variants: list[dict] = material.get("platform_variants", [])
    if variants:
        st.subheader("平台變體")
        variant_cols = st.columns(len(variants))
        for col, variant in zip(variant_cols, variants):
            with col:
                platform = html_module.escape(variant.get("platform", "—"))
                duration = html_module.escape(variant.get("duration", "—"))
                aspect_ratio = html_module.escape(variant.get("aspect_ratio", "—"))
                st.markdown(
                    f"**{platform}**  \n時長: {duration} · 比例: {aspect_ratio}",
                    unsafe_allow_html=True,
                )
                tips: list[str] = variant.get("tips", [])
                for tip in tips:
                    st.markdown(f"- {html_module.escape(tip)}", unsafe_allow_html=True)

    # ── 7. Sources ─────────────────────────────────────────────────────
    sources: list[dict] = material.get("sources", [])
    if sources:
        st.subheader("資料來源")
        for src in sources:
            source_type = src.get("source_type", "")
            badge = _SOURCE_BADGES.get(source_type, "🔗")
            title = html_module.escape(src.get("title", "未知來源"))
            url = src.get("url", "")
            published = src.get("published_at", "")

            label = f"{badge} **{html_module.escape(source_type)}** — "
            if url:
                escaped_url = html_module.escape(url)
                label += f"[{title}]({escaped_url})"
            else:
                label += title
            if published:
                label += f"  ({html_module.escape(published)})"

            st.markdown(label, unsafe_allow_html=True)

    # ── 8. Footer timestamps ───────────────────────────────────────────
    generated_at = material.get("generated_at", "")
    footer_parts: list[str] = []
    if generated_at:
        footer_parts.append(f"生成時間: {html_module.escape(generated_at)}")
    return footer_parts


# --- Main rendering loop ---
if not history:
    st.info("尚無研究記錄。前往「研究」頁面開始你的第一次研究。")
else:
    for i, record in enumerate(reversed(history)):
        topic = record.get("topic", "未知主題")
        executed_at = record.get("executed_at", "")
        record_index = len(history) - i

        expander_label = f"#{record_index}: {topic}"
        if executed_at:
            expander_label += f"  ({executed_at})"

        with st.expander(expander_label, expanded=i == 0):
            if record.get("video_material"):
                material = record["video_material"]
                footer_parts = _render_material(material)

                # Add executed_at to footer
                if executed_at:
                    footer_parts.append(f"執行時間: {html_module.escape(executed_at)}")

                if footer_parts:
                    st.caption(" | ".join(footer_parts))
            else:
                st.warning("此記錄無影片素材資料。")
