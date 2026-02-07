# News Spark

AI 驅動的新聞分析與短片素材產生器。透過多代理系統深度研究新聞與社群內容，自動產出適合短影片的素材，包含 Hook Line、論點、視覺建議、Hashtag 及多平台變體。

## 功能特色

- **多來源資料蒐集** — 同時抓取 NewsAPI、Google News RSS、PTT、Threads、LinkedIn
- **多代理協作** — Supervisor 分解任務，專業代理平行執行研究
- **深度分析** — 萃取關鍵洞察、爭議點、情緒摘要
- **短片素材產出** — 自動產生 Hook Line、論點、視覺建議、CTA、Hashtag
- **多平台適配** — 針對 TikTok、YouTube Shorts、Instagram Reels 產出專屬建議
- **記憶系統** — 學習使用者偏好與反饋，持續優化產出品質
- **研究歷史** — 保存每次研究結果，可隨時回顧

## 技術架構

```
Streamlit Frontend (app/)
        |
LangGraph Orchestration (src/graph/)
  - Supervisor 分解查詢
  - 平行子代理執行研究
  - Content Synthesizer 彙整結果
        |
Memory & Personalization (src/memory/)
  - SQLite: 使用者設定檔、知識圖譜
  - Chroma: 對話嵌入、學習修正
```

### 研究流程

```
使用者輸入主題
    -> Supervisor 分解子查詢
    -> News Scraper (NewsAPI + Google News)
    -> Social Media (PTT + Threads)
    -> Deep Analyzer (深度分析)
    -> Content Synthesizer (產出 VideoMaterial)
    -> 顯示結果 + 收集反饋
```

### 核心元件

| 模組 | 說明 |
|------|------|
| `src/agents/` | AI 代理 — supervisor、news_scraper、social_media、deep_analyzer、content_synthesizer |
| `src/graph/` | LangGraph 工作流 — 狀態管理、節點、條件邊、研究圖 |
| `src/scrapers/` | 資料抓取 — NewsAPI、Google News RSS、PTT、Threads、LinkedIn |
| `src/memory/` | 記憶系統 — SQLite 儲存、向量搜尋、反饋處理、個人化 |
| `src/models/` | 資料模型 — ResearchRequest、ContentItem、AnalysisResult、VideoMaterial |
| `src/utils/` | 工具 — 設定管理 (pydantic-settings)、LLM 工廠、速率限制器 |
| `app/` | Streamlit 前端 — 主頁面、歷史頁、偏好設定、結果展示元件 |

## 目錄結構

```
news-spark/
├── app/
│   ├── main.py                 # Streamlit 主頁面
│   ├── components/
│   │   ├── topic_input.py      # 研究主題輸入元件
│   │   ├── results_display.py  # 結果展示元件
│   │   ├── feedback_panel.py   # 反饋面板
│   │   ├── progress_tracker.py # 進度追蹤
│   │   └── history_store.py    # 歷史儲存
│   └── pages/
│       ├── 02_history.py       # 研究歷史頁面
│       └── 03_preferences.py   # 偏好設定頁面
├── src/
│   ├── agents/
│   │   ├── base.py             # Agent 基類 (BaseAgent, AgentResult)
│   │   ├── supervisor.py       # 任務分解與協調
│   │   ├── news_scraper.py     # 新聞抓取代理
│   │   ├── social_media.py     # 社群媒體代理
│   │   ├── deep_analyzer.py    # 深度分析代理
│   │   └── content_synthesizer.py # 內容合成代理
│   ├── graph/
│   │   ├── state.py            # ResearchState 定義
│   │   ├── nodes.py            # 圖節點實作
│   │   ├── edges.py            # 條件邊與錯誤處理
│   │   └── research_graph.py   # 主研究工作流
│   ├── scrapers/
│   │   ├── base.py             # 爬蟲基類 (SSRF 防護、重試)
│   │   ├── news_api.py         # NewsAPI 爬蟲
│   │   ├── google_news.py      # Google News RSS 爬蟲
│   │   ├── ptt.py              # PTT 論壇爬蟲
│   │   ├── threads.py          # Threads 爬蟲
│   │   └── linkedin.py         # LinkedIn 爬蟲
│   ├── memory/
│   │   ├── service.py          # 記憶服務主入口
│   │   ├── manager.py          # 記憶管理器
│   │   ├── feedback_processor.py # 反饋處理
│   │   ├── personalization.py  # 個人化引擎
│   │   ├── models/             # 記憶資料模型
│   │   └── storage/            # SQLite + Chroma 儲存
│   ├── models/
│   │   ├── content.py          # ResearchRequest, ContentItem, AnalysisResult
│   │   └── video_material.py   # VideoMaterial, PlatformVariant, SourceItem
│   └── utils/
│       ├── config.py           # 設定管理 (pydantic-settings)
│       ├── llm_factory.py      # LLM 工廠
│       └── rate_limiter.py     # 速率限制器
├── tests/
│   ├── unit/                   # 單元測試 (agents, graph, memory, models, scrapers, utils)
│   ├── integration/            # 整合測試
│   └── e2e/                    # E2E 測試 (Playwright)
├── data/
│   ├── cache/                  # API 回應快取
│   └── memory/                 # SQLite + Chroma 向量庫
├── docs/                       # 文件
├── pyproject.toml              # 專案設定與依賴
└── .env.example                # 環境變數範本
```

## 安裝

### 前置需求

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) 套件管理器

### 步驟

```bash
# 1. Clone 專案
git clone <repo-url>
cd news-spark

# 2. 安裝依賴
uv sync

# 3. 設定環境變數
cp .env.example .env
# 編輯 .env 填入你的 API Keys
```

## 環境變數

將 `.env.example` 複製為 `.env` 並設定以下變數：

### 必要

| 變數 | 說明 | 範例 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API Key | `sk-xxx` |
| `NEWSAPI_KEY` | [NewsAPI](https://newsapi.org/) Key | `xxx` |

### 選用

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | Anthropic API Key（使用 Anthropic 時必填）| — |
| `LLM_PROVIDER` | LLM 提供者 | `openai` |
| `LLM_MODEL` | 模型名稱 | `gpt-4o-mini` |
| `LLM_TEMPERATURE` | 溫度 (0.0-2.0) | `0.7` |
| `LLM_MAX_TOKENS` | 最大 token 數 | `4096` |
| `EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-3-small` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | 每分鐘最大請求數 | `60` |
| `CACHE_TTL_SECONDS` | 快取 TTL（秒）| `3600` |
| `CACHE_DIR` | 快取目錄 | `data/cache` |
| `MEMORY_DB_PATH` | SQLite 路徑 | `data/memory/memory.db` |
| `VECTORSTORE_DIR` | 向量儲存目錄 | `data/memory/vectorstore` |
| `DEBUG` | 除錯模式 | `false` |
| `LOG_LEVEL` | 日誌等級 | `INFO` |

## 使用

```bash
# 啟動 Streamlit 應用
uv run streamlit run app/main.py
```

開啟瀏覽器訪問 `http://localhost:8501`，在側邊欄輸入研究主題並點選「開始分析」。

## 開發

```bash
# 執行所有測試
uv run pytest tests/ -v

# 單元測試 + 覆蓋率
uv run pytest tests/unit -v --cov=src --cov-report=term-missing

# 執行單一測試檔
uv run pytest tests/unit/test_agents/test_supervisor.py -v

# E2E 測試（需先啟動 Streamlit）
uv run pytest tests/e2e -v -m e2e

# Lint 與格式化
uv run ruff check .
uv run ruff format .
```

## 主要依賴

| 套件 | 用途 |
|------|------|
| [Streamlit](https://streamlit.io/) | Web UI 框架 |
| [LangGraph](https://langchain-ai.github.io/langgraph/) | 多代理工作流編排 |
| [LangChain](https://www.langchain.com/) | LLM 整合框架 |
| [Pydantic](https://docs.pydantic.dev/) | 資料驗證與模型 |
| [ChromaDB](https://www.trychroma.com/) | 向量資料庫 |
| [httpx](https://www.python-httpx.org/) | 非同步 HTTP 客戶端 |
| [feedparser](https://feedparser.readthedocs.io/) | RSS 解析 |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML 解析 |

## License

[GPL-3.0](LICENSE)
