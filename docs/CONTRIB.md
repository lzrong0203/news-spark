# Contributing Guide

> Auto-generated from `pyproject.toml`, `src/utils/config.py`, and `.env.example`. Last updated: 2026-02-08.

## Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) package manager

## Environment Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

#### Required Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM and embeddings |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude models |

#### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEWSAPI_KEY` | `""` | NewsAPI key for `NewsAPIScraper` |
| `GOOGLE_API_KEY` | _(none)_ | Google API key (optional, for Google services) |
| `LLM_PROVIDER` | `openai` | LLM provider: `openai` or `anthropic` |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model name |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model name |
| `LLM_TEMPERATURE` | `0.7` | LLM temperature (0.0 - 2.0) |
| `LLM_MAX_TOKENS` | `4096` | Maximum token count per LLM response |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Rate limiter max requests per minute |
| `CACHE_TTL_SECONDS` | `3600` | Cache time-to-live in seconds |
| `CACHE_DIR` | `data/cache` | Cache directory path |
| `MEMORY_DB_PATH` | `data/memory/memory.db` | SQLite database path |
| `VECTORSTORE_DIR` | `data/memory/vectorstore` | Chroma vector store directory |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

All settings are managed by `src/utils/config.py` via `pydantic-settings`.

### 3. Install Playwright Browsers (for E2E tests)

```bash
uv run playwright install
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `uv sync` | Install all dependencies (production + dev) |
| `uv sync --no-dev` | Install production dependencies only |
| `uv run streamlit run app/main.py` | Start the Streamlit application |
| `uv run pytest tests/ -v` | Run all tests |
| `uv run pytest tests/unit -v` | Run unit tests only |
| `uv run pytest tests/integration -v` | Run integration tests only |
| `uv run pytest tests/e2e -v` | Run E2E tests (requires running Streamlit server) |
| `uv run pytest tests/unit -v --cov=src --cov-report=term-missing` | Run unit tests with coverage report |
| `uv run ruff check .` | Lint the codebase |
| `uv run ruff format .` | Auto-format the codebase |
| `uv lock --upgrade` | Update all dependency versions in lock file |

## Dependencies

### Production Dependencies

| Package | Min Version | Purpose |
|---------|-------------|---------|
| streamlit | 1.53.0 | Web UI framework |
| openai | 1.60.0 | OpenAI API client |
| langchain | 1.2.8 | LLM framework |
| langchain-openai | 1.1.7 | LangChain OpenAI integration |
| langchain-anthropic | 1.3.1 | LangChain Anthropic integration |
| langgraph | 1.0.7 | Agent workflow orchestration |
| pydantic | 2.10.0 | Data validation and models |
| pydantic-settings | 2.12.0 | Settings management from env vars |
| chromadb | 1.4.1 | Vector store for semantic search |
| feedparser | 6.0.12 | RSS feed parsing (Google News) |
| aiosqlite | 0.22.1 | Async SQLite for memory system |
| tenacity | 9.1.2 | Retry logic with exponential backoff |
| pandas | 2.2.0 | Data processing |
| numpy | 2.0.0 | Numerical computation |
| requests | 2.32.0 | HTTP client |
| beautifulsoup4 | 4.12.0 | HTML parsing for scrapers |
| httpx | 0.27.0 | Async HTTP client |
| python-dotenv | 1.0.1 | Environment variable loading |

### Dev Dependencies

| Package | Min Version | Purpose |
|---------|-------------|---------|
| pytest | 8.0.0 | Test framework |
| pytest-asyncio | 0.23.0 | Async test support |
| pytest-cov | 4.1.0 | Coverage reporting |
| pytest-playwright | 0.7.2 | E2E browser testing |
| playwright | 1.58.0 | Browser automation |
| ruff | 0.9.0 | Linter and formatter |

## Project Structure

```
AI_News/
├── app/                          # Streamlit frontend
│   ├── __init__.py
│   ├── main.py                   # App entry point
│   ├── components/               # Reusable UI components
│   │   ├── __init__.py
│   │   ├── feedback_panel.py     # User feedback collection
│   │   ├── history_store.py      # Research history storage
│   │   ├── progress_tracker.py   # Workflow progress display
│   │   ├── results_display.py    # Result rendering
│   │   └── topic_input.py        # Topic input form
│   └── pages/                    # Streamlit multi-page
│       ├── 02_history.py         # Research history page
│       └── 03_preferences.py     # User preferences page
├── src/                          # Core application logic
│   ├── agents/                   # AI agents (7 modules)
│   │   ├── __init__.py
│   │   ├── base.py               # BaseAgent, AgentContext, AgentResult
│   │   ├── supervisor.py         # SupervisorAgent (coordinator)
│   │   ├── news_scraper.py       # NewsScraperAgent
│   │   ├── social_media.py       # SocialMediaAgent
│   │   ├── deep_analyzer.py      # DeepAnalyzerAgent
│   │   └── content_synthesizer.py# ContentSynthesizerAgent
│   ├── graph/                    # LangGraph workflow (5 modules)
│   │   ├── __init__.py
│   │   ├── state.py              # ResearchState definition
│   │   ├── nodes.py              # Graph node functions
│   │   ├── edges.py              # Conditional edge logic
│   │   └── research_graph.py     # Graph builder and runner
│   ├── scrapers/                 # Data scrapers (7 modules)
│   │   ├── __init__.py
│   │   ├── base.py               # BaseScraper interface
│   │   ├── news_api.py           # NewsAPIScraper
│   │   ├── google_news.py        # GoogleNewsScraper (RSS)
│   │   ├── ptt.py                # PTTScraper (Taiwan forum)
│   │   ├── threads.py            # ThreadsScraper (Meta)
│   │   └── linkedin.py           # LinkedInScraper + LinkedInURLHandler
│   ├── memory/                   # Memory and personalization (5 modules)
│   │   ├── __init__.py
│   │   ├── manager.py            # Memory lifecycle management
│   │   ├── service.py            # Memory service interface
│   │   ├── feedback_processor.py # User feedback learning
│   │   └── personalization.py    # Personalization injection
│   ├── models/                   # Pydantic data models (3 modules)
│   │   ├── __init__.py
│   │   ├── content.py            # ContentItem, ResearchRequest, AnalysisResult
│   │   └── video_material.py     # VideoMaterial, PlatformVariant, SourceItem
│   └── utils/                    # Utilities (4 modules)
│       ├── __init__.py
│       ├── config.py             # Settings via pydantic-settings
│       ├── llm_factory.py        # LLM/embedding model creation
│       └── rate_limiter.py       # API rate limiting
├── tests/                        # Test suite
│   ├── conftest.py               # Shared fixtures
│   ├── unit/
│   │   ├── conftest.py           # Unit test fixtures
│   │   ├── test_models/          # Data model tests
│   │   ├── test_agents/          # Agent tests
│   │   ├── test_scrapers/        # Scraper tests
│   │   ├── test_memory/          # Memory system tests
│   │   ├── test_graph/           # Graph workflow tests
│   │   └── test_utils/           # Utility tests
│   ├── integration/              # Integration tests
│   └── e2e/
│       ├── conftest.py           # E2E fixtures (Streamlit server)
│       ├── pages/                # Page objects
│       │   └── news_spark_page.py
│       ├── test_sidebar.py
│       └── test_content_rendering.py
├── data/                         # Runtime data (gitignored)
│   ├── memory/                   # SQLite + Chroma vector store
│   └── cache/                    # API response cache
└── docs/                         # Documentation
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feat/your-feature
```

### 2. Write Tests First (TDD)

```bash
# Create test file
# Write failing tests
uv run pytest tests/unit/test_your_module.py -v  # RED - should fail
```

### 3. Implement

Write minimal code to pass the tests.

```bash
uv run pytest tests/unit/test_your_module.py -v  # GREEN - should pass
```

### 4. Lint and Format

```bash
uv run ruff check .
uv run ruff format .
```

### 5. Verify Coverage

```bash
uv run pytest tests/unit -v --cov=src --cov-report=term-missing
```

Target: **80%+** test coverage.

### 6. Commit

```bash
git add <files>
git commit -m "feat: description of change"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring
- `docs:` Documentation
- `test:` Tests
- `chore:` Maintenance
- `perf:` Performance
- `ci:` CI/CD

## Testing

### Test Structure

```
tests/
├── conftest.py                        # Shared fixtures
├── unit/
│   ├── conftest.py                    # Unit test fixtures
│   ├── test_models/                   # Data model tests (2 test files)
│   │   ├── test_video_material.py
│   │   └── test_content.py
│   ├── test_agents/                   # Agent tests (5 test files)
│   │   ├── test_supervisor.py
│   │   ├── test_news_scraper.py
│   │   ├── test_social_media.py
│   │   ├── test_deep_analyzer.py
│   │   └── test_content_synthesizer.py
│   ├── test_scrapers/                 # Scraper tests (5 test files)
│   │   ├── test_base.py
│   │   ├── test_news_api.py
│   │   ├── test_google_news.py
│   │   ├── test_ptt.py
│   │   ├── test_threads.py
│   │   └── test_linkedin.py
│   ├── test_memory/                   # Memory system tests (5 test files)
│   │   ├── test_manager.py
│   │   ├── test_service.py
│   │   ├── test_feedback_processor.py
│   │   ├── test_personalization.py
│   │   ├── test_sqlite_store.py
│   │   └── test_models.py
│   ├── test_graph/                    # Graph workflow tests (3 test files)
│   │   ├── test_edges.py
│   │   ├── test_nodes.py
│   │   └── test_research_graph.py
│   └── test_utils/                    # Utility tests (1 test file)
│       └── test_rate_limiter.py
├── integration/                       # Integration tests
└── e2e/
    ├── conftest.py                    # E2E fixtures (Streamlit server)
    ├── pages/                         # Page objects
    │   └── news_spark_page.py
    ├── test_sidebar.py
    └── test_content_rendering.py
```

### Pytest Configuration

From `pyproject.toml`:
- **Test paths**: `tests/`
- **Async mode**: `auto` (via `pytest-asyncio`)
- **Custom markers**: `e2e` -- end-to-end tests requiring a running Streamlit server

### Running E2E Tests

E2E tests require a running Streamlit server:

```bash
# Terminal 1: Start the app
uv run streamlit run app/main.py

# Terminal 2: Run E2E tests
uv run pytest tests/e2e -v
```

### Running Tests by Category

```bash
# All tests
uv run pytest tests/ -v

# Unit tests only
uv run pytest tests/unit -v

# Specific module tests
uv run pytest tests/unit/test_agents -v
uv run pytest tests/unit/test_scrapers -v
uv run pytest tests/unit/test_memory -v
uv run pytest tests/unit/test_graph -v
uv run pytest tests/unit/test_utils -v

# Single test file
uv run pytest tests/unit/test_models/test_video_material.py -v

# With coverage
uv run pytest tests/unit -v --cov=src --cov-report=term-missing
```

## Language

Primary language: **Traditional Chinese (zh-TW)**. Code comments and documentation may be in Chinese.
