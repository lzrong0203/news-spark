"""結果顯示元件

將 VideoMaterial 渲染為 Streamlit 卡片。
"""

import streamlit as st

from src.models.video_material import VideoMaterial


def render_video_material(material: VideoMaterial) -> None:
    """渲染完整的 VideoMaterial 結果"""
    render_metric_cards(material)
    st.divider()
    render_hook_section(material)
    st.divider()
    render_talking_points(material)
    st.divider()
    render_platform_variants(material)
    st.divider()
    render_hashtags(material)
    st.divider()
    render_sources(material)


def render_metric_cards(material: VideoMaterial) -> None:
    """渲染指標卡片"""
    cols = st.columns(4)
    with cols[0]:
        st.metric("病毒分數", f"{material.viral_score:.0%}")
    with cols[1]:
        st.metric("論點數", len(material.key_talking_points))
    with cols[2]:
        st.metric("來源數", len(material.sources))
    with cols[3]:
        st.metric("Hashtags", len(material.hashtag_suggestions))


def render_hook_section(material: VideoMaterial) -> None:
    """渲染 Hook 區段"""
    st.subheader(material.title_suggestion)
    st.markdown(f"**🎯 目標情緒**: {material.target_emotion}")
    st.markdown("**📢 Hook Line**:")
    st.info(material.hook_line)
    st.markdown(f"**💡 行動呼籲**: {material.call_to_action}")


def render_talking_points(material: VideoMaterial) -> None:
    """渲染論點和視覺建議"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💬 論點")
        for i, point in enumerate(material.key_talking_points, 1):
            st.markdown(f"{i}. {point}")

    with col2:
        st.markdown("### 🎨 視覺建議")
        for suggestion in material.visual_suggestions:
            st.markdown(f"- {suggestion}")


def render_platform_variants(material: VideoMaterial) -> None:
    """渲染平台變體"""
    if not material.platform_variants:
        return

    st.markdown("### 📱 平台建議")
    tabs = st.tabs([v.platform for v in material.platform_variants])

    for tab, variant in zip(tabs, material.platform_variants):
        with tab:
            st.markdown(f"**時長**: {variant.duration}")
            st.markdown(f"**格式**: {variant.format} ({variant.aspect_ratio})")
            if variant.tips:
                st.markdown("**建議**:")
                for tip in variant.tips:
                    st.markdown(f"- {tip}")


def render_hashtags(material: VideoMaterial) -> None:
    """渲染 Hashtag 建議"""
    st.markdown("### #️⃣ Hashtags")
    tags_html = " ".join(
        f"`#{tag.lstrip('#')}`" for tag in material.hashtag_suggestions
    )
    st.markdown(tags_html)


def render_sources(material: VideoMaterial) -> None:
    """渲染資料來源"""
    if not material.sources:
        return

    st.markdown("### 📚 資料來源")
    for source in material.sources:
        type_badge = {"news": "📰", "social": "💬", "forum": "🏛️", "web": "🌐"}.get(
            source.source_type, "📄"
        )
        published = f" ({source.published_at})" if source.published_at else ""
        st.markdown(f"{type_badge} [{source.title}]({source.url}){published}")
