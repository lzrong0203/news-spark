# News Spark - AI 新聞深度研究系統設計計劃

## 專案概述

**News Spark** 是一個多代理 AI 系統，能夠對新聞和社群媒體內容進行深度研究，並產生適合短影片的素材。系統使用 LangGraph 協調專門代理，實現持久記憶系統以學習使用者偏好，並提供 Streamlit 介面進行互動。

## 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                          │
│  [話題輸入] → [研究進度] → [結果展示] → [反饋收集]                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LangGraph 協調層                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 研究主管     │→ │ 查詢分解     │→ │ 結果彙整     │          │
│  │ Supervisor   │  │ Decomposer   │  │ Aggregator   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────┐          │
│  │          並行代理執行池                            │          │
│  │  [新聞代理] [社群代理] [網頁代理] [分析代理]      │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  記憶與個人化層                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 使用者偏好   │  │ 對話記憶     │  │ 知識圖譜     │          │
│  │ (SQLite)     │  │ (Vector)     │  │ (SQLite)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## 專案目錄結構

```
AI_News/
├── app/
│   ├── main.py                      # Streamlit 主入口
│   ├── pages/
│   │   ├── 01_research.py           # 話題研究介面
│   │   ├── 02_history.py            # 研究歷史
│   │   └── 03_preferences.py        # 使用者偏好設定
│   └── components/
│       ├── topic_input.py           # 話題輸入元件
│       ├── progress_tracker.py      # 進度顯示
│       ├── results_display.py       # 結果卡片
│       └── feedback_panel.py        # 反饋收集
│
├── src/
│   ├── agents/
│   │   ├── base.py                  # 代理基類
│   │   ├── supervisor.py            # 研究主管代理
│   │   ├── news_scraper.py          # 新聞抓取代理
│   │   ├── social_media.py          # 社群媒體代理
│   │   ├── deep_analyzer.py         # 深度分析代理
│   │   └── content_synthesizer.py   # 內容合成代理
│   │
│   ├── graph/
│   │   ├── state.py                 # LangGraph 狀態定義
│   │   ├── nodes.py                 # 圖節點實作
│   │   ├── edges.py                 # 條件邊邏輯
│   │   └── research_graph.py        # 主研究工作流
│   │
│   ├── scrapers/
│   │   ├── base.py                  # 爬蟲基類
│   │   ├── news_api.py              # NewsAPI 整合
│   │   ├── google_news.py           # Google News RSS
│   │   ├── linkedin.py              # LinkedIn 爬蟲
│   │   ├── ptt.py                   # PTT 論壇爬蟲 (台灣)
│   │   ├── threads.py               # Threads 社群爬蟲
│   │   └── general_web.py           # 通用網頁爬蟲
│   │
│   ├── memory/
│   │   ├── models/                  # 記憶資料模型
│   │   │   ├── user_profile.py      # 使用者檔案
│   │   │   ├── feedback.py          # 反饋模型
│   │   │   ├── conversation.py      # 對話記錄
│   │   │   └── knowledge_graph.py   # 知識圖譜
│   │   ├── storage/
│   │   │   ├── sqlite_store.py      # SQLite 儲存
│   │   │   └── vector_store.py      # 向量儲存
│   │   ├── manager.py               # 記憶管理器
│   │   ├── feedback_processor.py    # 反饋處理
│   │   ├── personalization.py       # 個人化引擎
│   │   └── service.py               # 記憶服務 API
│   │
│   ├── models/
│   │   ├── research.py              # 研究請求/回應模型
│   │   ├── content.py               # 內容項目模型
│   │   ├── analysis.py              # 分析結果模型
│   │   └── video_material.py        # 影片素材模型
│   │
│   └── utils/
│       ├── config.py                # 設定管理
│       ├── llm_factory.py           # LLM 工廠
│       └── rate_limiter.py          # 速率限制
│
├── data/
│   ├── memory/                      # 記憶持久化
│   │   ├── memory.db                # SQLite 資料庫
│   │   └── vectorstore/             # 向量儲存
│   └── cache/                       # API 快取
│
└── tests/                           # 測試套件
```

## 實作階段

### 第一階段：基礎建設 (Phase 1)
**目標**：建立核心資料模型與基礎設施

| 步驟 | 檔案 | 說明 |
|------|------|------|
| 1.1 | `src/models/*.py` | 實作 Pydantic 資料模型 |
| 1.2 | `src/utils/config.py` | 設定管理 (環境變數) |
| 1.3 | `src/utils/llm_factory.py` | LLM 客戶端工廠 |
| 1.4 | `src/agents/base.py` | 代理基類 |
| 1.5 | `src/graph/state.py` | LangGraph 狀態定義 |

### 第二階段：資料收集層 (Phase 2)
**目標**：實作網頁爬蟲與 API 整合（新聞與社群平衡發展）

| 步驟 | 檔案 | 說明 | 優先級 |
|------|------|------|--------|
| 2.1 | `src/scrapers/base.py` | 爬蟲介面定義 | 高 |
| 2.2 | `src/scrapers/news_api.py` | NewsAPI 整合 | 高 |
| 2.3 | `src/scrapers/google_news.py` | Google News RSS | 高 |
| 2.4 | `src/scrapers/ptt.py` | PTT 論壇爬蟲 (台灣熱門討論) | 高 |
| 2.5 | `src/scrapers/threads.py` | Threads 社群內容抓取 | 中 |
| 2.6 | `src/scrapers/linkedin.py` | LinkedIn 內容抓取 | 中 |
| 2.7 | `src/scrapers/general_web.py` | 通用網頁爬蟲 | 中 |
| 2.8 | `src/utils/rate_limiter.py` | 速率限制工具 | 高 |

### 第三階段：AI 代理 (Phase 3)
**目標**：實作專門 AI 代理

| 步驟 | 檔案 | 說明 |
|------|------|------|
| 3.1 | `src/agents/news_scraper.py` | 新聞抓取代理 |
| 3.2 | `src/agents/social_media.py` | 社群媒體代理 |
| 3.3 | `src/agents/deep_analyzer.py` | 深度分析代理 |
| 3.4 | `src/agents/content_synthesizer.py` | 內容合成代理 |
| 3.5 | `src/agents/supervisor.py` | 研究主管代理 |

### 第四階段：LangGraph 工作流 (Phase 4)
**目標**：建構研究工作流圖

| 步驟 | 檔案 | 說明 |
|------|------|------|
| 4.1 | `src/graph/nodes.py` | 圖節點實作 |
| 4.2 | `src/graph/edges.py` | 條件邊邏輯 |
| 4.3 | `src/graph/research_graph.py` | 主研究工作流 |

### 第五階段：記憶系統 (Phase 5)
**目標**：實作個人化記憶系統

| 步驟 | 檔案 | 說明 |
|------|------|------|
| 5.1 | `src/memory/models/*.py` | 記憶資料模型 |
| 5.2 | `src/memory/storage/sqlite_store.py` | SQLite 儲存層 |
| 5.3 | `src/memory/storage/vector_store.py` | 向量儲存 (Chroma) |
| 5.4 | `src/memory/manager.py` | 記憶管理器 |
| 5.5 | `src/memory/feedback_processor.py` | 反饋處理器 |
| 5.6 | `src/memory/personalization.py` | 個人化引擎 |
| 5.7 | `src/memory/service.py` | 記憶服務 API |

### 第六階段：前端介面 (Phase 6)
**目標**：建構 Streamlit 使用者介面

| 步驟 | 檔案 | 說明 |
|------|------|------|
| 6.1 | `app/components/topic_input.py` | 話題輸入元件 |
| 6.2 | `app/components/progress_tracker.py` | 進度顯示 |
| 6.3 | `app/components/results_display.py` | 結果卡片 |
| 6.4 | `app/components/feedback_panel.py` | 反饋收集 |
| 6.5 | `app/pages/01_research.py` | 研究頁面 |
| 6.6 | `app/pages/02_history.py` | 歷史頁面 |
| 6.7 | `app/pages/03_preferences.py` | 偏好設定 |
| 6.8 | `app/main.py` | 更新主入口 |

### 第七階段：整合與測試 (Phase 7)
**目標**：完整測試與文件

| 步驟 | 檔案 | 說明 |
|------|------|------|
| 7.1 | `tests/unit/*.py` | 單元測試 |
| 7.2 | `tests/integration/*.py` | 整合測試 |
| 7.3 | `tests/e2e/*.py` | E2E 測試 |

## 核心資料模型

### ResearchRequest (研究請求)
```python
class ResearchRequest(BaseModel):
    topic: str                    # 研究話題
    user_id: str                  # 使用者 ID
    language: str = "zh-TW"       # 語言
    sources: list[str]            # 資料來源
    depth: int = 2                # 研究深度 (1-5)
    max_results: int = 20         # 最大結果數
```

### VideoMaterial (影片素材 - 多平台通用)
```python
class VideoMaterial(BaseModel):
    title_suggestion: str         # 標題建議
    hook_line: str                # 開頭引言 (前 3 秒抓住注意力)
    key_talking_points: list[str] # 重點論述
    visual_suggestions: list[str] # 視覺建議
    viral_score: float            # 病毒傳播分數 (0-1)
    target_emotion: str           # 目標情緒

    # 多平台適配
    platform_variants: dict = {
        "tiktok": {"duration": "15-60s", "format": "vertical"},
        "youtube_shorts": {"duration": "≤60s", "format": "vertical"},
        "instagram_reels": {"duration": "≤90s", "format": "vertical"},
    }
    call_to_action: str           # 行動呼籲
    hashtag_suggestions: list[str] # 標籤建議
```

### UserPreference (使用者偏好)
```python
class UserPreference(BaseModel):
    user_id: str
    preferred_topics: list[str]   # 偏好話題
    avoided_topics: list[str]     # 避開話題
    tone_preference: str          # 語調偏好
    corrections: list[Correction] # 歷史修正
    viewpoints: dict              # 話題觀點
```

## 資料來源詳情

### 新聞來源
| 來源 | 方法 | 備註 |
|------|------|------|
| NewsAPI | REST API | 需要 API Key，免費版有限制 |
| Google News | RSS Feed | 無需認證，可依地區/語言篩選 |

### 社群來源
| 來源 | 方法 | 備註 |
|------|------|------|
| PTT | Web Scraping / API | 台灣最大論壇，可用 ptt-web-api 或直接爬取 |
| Threads | Official API / Scraping | Meta 官方 API 或 Playwright 爬取 |
| LinkedIn | Playwright Scraping | 需登入，反爬嚴格，建議手動 URL 輸入模式 |

### PTT 爬蟲策略
```python
# 可用的看板範例
boards = [
    "Gossiping",    # 八卦版 (時事熱議)
    "Stock",        # 股票版 (財經)
    "Tech_Job",     # 科技工作版
    "movie",        # 電影版
    "HatePolitics", # 政黑版
]
```

### Threads 爬蟲策略
- 使用 Meta 官方 Threads API (如有開放)
- 備用：Playwright 模擬瀏覽器
- 關注熱門標籤和帳號

## 需要新增的依賴

```toml
# 加入 pyproject.toml
dependencies = [
    # 現有...
    "langgraph>=0.2.0",           # 代理工作流
    "chromadb>=0.4.0",            # 向量儲存
    "feedparser>=6.0.0",          # RSS 解析
    "aiosqlite>=0.19.0",          # 非同步 SQLite
    "tenacity>=8.2.0",            # 重試邏輯
    "playwright>=1.40.0",         # 網頁爬蟲
]
```

## 驗證計劃

### 功能驗證
1. **話題研究流程**
   ```bash
   # 啟動 Streamlit
   uv run streamlit run app/main.py
   # 輸入話題 → 確認結果產生
   ```

2. **記憶持久化**
   ```bash
   # 提交反饋 → 重啟應用 → 確認反饋被記住
   ```

3. **個人化效果**
   ```bash
   # 多次互動後 → 確認輸出風格符合偏好
   ```

### 測試執行
```bash
# 單元測試
uv run pytest tests/unit -v --cov=src --cov-report=term-missing

# 整合測試
uv run pytest tests/integration -v

# E2E 測試
uv run pytest tests/e2e -v
```

### 成功標準
- [ ] 使用者可輸入話題並獲得研究結果
- [ ] 至少 3 個資料來源正常運作
- [ ] 使用者修正能持久化並改善未來建議
- [ ] 影片素材包含引言、論點和視覺建議
- [ ] 測試覆蓋率 >= 80%

## 風險與緩解

| 風險 | 嚴重度 | 緩解措施 |
|------|--------|----------|
| LinkedIn 反爬蟲 | 高 | 使用瀏覽器輪換、尊重速率限制、提供手動 URL 輸入 |
| Threads API 限制 | 中 | 使用官方 API (如有)、備用網頁爬取 |
| PTT 結構變動 | 低 | PTT 結構穩定，使用 PTT API 或 RSS |
| API 速率限制 | 中 | 實作請求佇列、快取、指數退避 |
| LLM 成本 | 中 | 使用 Haiku 處理輕量任務、快取常見查詢 |
| 記憶儲存損壞 | 中 | 原子寫入、備份策略、讀取驗證 |

## 實作順序（完整架構）

採用**完整架構**開發策略，按階段順序實作所有功能：

```
Phase 1 (基礎) → Phase 2 (資料收集，新聞+社群並行)
                        ↓
              Phase 3 (AI 代理) → Phase 4 (工作流)
                                        ↓
                              Phase 5 (記憶系統) → Phase 6 (前端)
                                                        ↓
                                                  Phase 7 (測試)
```

### 並行開發建議
- **新聞線**：Phase 2.2-2.3 + Phase 3.1
- **社群線**：Phase 2.4-2.6 + Phase 3.2
- **核心線**：Phase 3.3-3.5 + Phase 4

這樣可以讓團隊成員或開發時間分配更有效率。
