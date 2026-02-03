"""News Spark - 影片素材產出展示頁面."""

import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="News Spark",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 深色科技感主題樣式
st.markdown(
    """
    <style>
    /* 全局深色背景 */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* 卡片樣式 */
    .card {
        background: linear-gradient(145deg, #1e1e2f 0%, #252538 100%);
        border: 1px solid #3d3d5c;
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .card-title {
        color: #e0e0ff;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Hook Line 特殊樣式 */
    .hook-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
        color: white;
        font-size: 1.4rem;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
    }

    /* 標籤樣式 */
    .tag {
        display: inline-block;
        background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        margin: 4px;
        font-size: 0.9rem;
        font-weight: 500;
    }

    .tag-emotion {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }

    /* 分數進度條 */
    .score-bar {
        background: #2d2d44;
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
        background: linear-gradient(90deg, #00b09b 0%, #96c93d 100%);
    }

    .score-medium {
        background: linear-gradient(90deg, #f7971e 0%, #ffd200 100%);
    }

    .score-low {
        background: linear-gradient(90deg, #ed213a 0%, #93291e 100%);
    }

    /* 平台卡片 */
    .platform-card {
        background: linear-gradient(145deg, #252538 0%, #2d2d44 100%);
        border: 1px solid #3d3d5c;
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
        background: rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
        color: #e0e0ff;
    }

    /* 視覺建議 */
    .visual-tip {
        background: rgba(0, 210, 255, 0.1);
        border-left: 4px solid #00d2ff;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
        color: #e0e0ff;
    }

    /* CTA 按鈕樣式 */
    .cta-box {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
        box-shadow: 0 4px 20px rgba(255, 65, 108, 0.4);
    }

    /* 來源卡片 */
    .source-item {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .source-type {
        background: #3d3d5c;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        color: #a0a0cc;
    }

    /* 隱藏 Streamlit 預設元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 側邊欄樣式 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }

    /* 標題樣式 */
    h1, h2, h3 {
        color: #e0e0ff !important;
    }

    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 8px;
    }

    .subtitle {
        color: #8888aa;
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 32px;
    }

    /* 指標卡片 */
    .metric-card {
        background: linear-gradient(145deg, #1e1e2f 0%, #252538 100%);
        border: 1px solid #3d3d5c;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .metric-label {
        color: #8888aa;
        font-size: 0.9rem;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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
        <div style="color: #a0a0cc; font-size: 0.9rem; margin-bottom: 4px;">{label}</div>
        <div class="score-bar">
            <div class="score-fill {color_class}" style="width: {score * 100}%;"></div>
        </div>
        <div style="color: #e0e0ff; font-size: 1.1rem; font-weight: 600;">{score:.0%}</div>
        """,
        unsafe_allow_html=True,
    )


def render_main_page() -> None:
    """渲染主頁面."""
    data = get_mock_data()

    # 標題區
    st.markdown('<div class="main-title">⚡ News Spark</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">AI 驅動的新聞分析與短片素材產生器</div>',
        unsafe_allow_html=True,
    )

    # 側邊欄 - 輸入區
    with st.sidebar:
        st.markdown("### 🔍 研究主題")
        _topic_input = st.text_input(
            "輸入你想研究的主題",
            value="AI 取代工作",
            label_visibility="collapsed",
        )

        st.markdown("### ⚙️ 設定")
        _platforms = st.multiselect(
            "目標平台",
            ["TikTok", "YouTube Shorts", "Instagram Reels"],
            default=["TikTok", "YouTube Shorts"],
        )

        _tone = st.select_slider(
            "內容調性",
            options=["嚴肅", "中性", "輕鬆", "幽默"],
            value="中性",
        )

        if st.button("🚀 開始分析", type="primary", use_container_width=True):
            st.toast("正在分析中...", icon="⚡")

        st.divider()
        st.markdown(
            f"""
            <div style="color: #666; font-size: 0.8rem;">
            📅 最後更新: {data['generated_at']}<br>
            🎯 信心度: {data['confidence_score']:.0%}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 主要內容區
    # 頂部指標卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{data['viral_score']:.0%}</div>
                <div class="metric-label">🔥 病毒傳播潛力</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(data['key_talking_points'])}</div>
                <div class="metric-label">💡 重點論述</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(data['sources'])}</div>
                <div class="metric-label">📚 資料來源</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(data['hashtag_suggestions'])}</div>
                <div class="metric-label"># Hashtags</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 主題與 Hook Line
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">🎯 研究主題</div>
            <div style="color: #e0e0ff; font-size: 1.1rem;">{data['topic']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">✨ 建議標題</div>
            <div style="color: #f0f0ff; font-size: 1.3rem; font-weight: 600;">{data['title_suggestion']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">🎬 開場 Hook（前 3 秒）</div>
            <div class="hook-box">{data['hook_line']}</div>
            <div style="color: #8888aa; font-size: 0.9rem; margin-top: 12px;">
                💡 目標情緒: <span class="tag tag-emotion">{data['target_emotion']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 論點與視覺建議（並排）
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">💬 關鍵論點</div>', unsafe_allow_html=True)
        for i, point in enumerate(data["key_talking_points"], 1):
            st.markdown(
                f'<div class="talking-point"><strong>{i}.</strong> {point}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🎨 視覺呈現建議</div>', unsafe_allow_html=True)
        for tip in data["visual_suggestions"]:
            st.markdown(f'<div class="visual-tip">{tip}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # CTA 與 Hashtags
    col_cta, col_tags = st.columns([1, 1])

    with col_cta:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">📣 行動呼籲 (CTA)</div>
                <div class="cta-box">{data['call_to_action']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_tags:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title"># 建議 Hashtags</div>', unsafe_allow_html=True)
        tags_html = "".join(
            [f'<span class="tag">{tag}</span>' for tag in data["hashtag_suggestions"]]
        )
        st.markdown(f'<div style="margin-top: 8px;">{tags_html}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 平台專屬建議
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
                [f"<li style='color: #a0a0cc; margin: 6px 0;'>{tip}</li>" for tip in variant["tips"]]
            )
            st.markdown(
                f"""
                <div class="platform-card">
                    <div class="platform-icon">{variant['icon']}</div>
                    <div style="color: #e0e0ff; font-size: 1.2rem; font-weight: 600;">
                        {variant['platform']}
                    </div>
                    <div style="color: #8888aa; font-size: 0.9rem; margin: 8px 0;">
                        ⏱️ {variant['duration']} | 📐 {variant['aspect_ratio']}
                    </div>
                    <ul style="padding-left: 20px; margin-top: 12px;">
                        {tips_html}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 資料來源
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
                <span style="font-size: 1.5rem;">{source_icon}</span>
                <div style="flex: 1;">
                    <div style="color: #e0e0ff; font-weight: 500;">{source['title']}</div>
                    <div style="color: #666; font-size: 0.8rem;">
                        {source.get('published_at', '')}
                    </div>
                </div>
                <span class="source-type">{source['source_type']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    render_main_page()
