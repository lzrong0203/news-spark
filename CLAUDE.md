# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the Streamlit app
uv run streamlit run app/main.py

# Run tests
uv run pytest tests/ -v
uv run pytest tests/unit -v --cov=src --cov-report=term-missing  # with coverage

# Run single test file
uv run pytest tests/path/to/test_file.py -v

# Lint
uv run ruff check .
uv run ruff format .
```

## Architecture

**News Spark** is a multi-agent AI system for deep research on news and social media content, generating materials for short-form video creation.

### Three-Layer Architecture

```
Streamlit Frontend (app/)
        ↓
LangGraph Orchestration (src/graph/)
  - Supervisor agent decomposes queries
  - Parallel sub-agents execute research
  - Aggregator synthesizes results
        ↓
Memory & Personalization (src/memory/)
  - SQLite: user profiles, knowledge graph
  - Vector store: conversation embeddings, learned corrections
```

### Key Components

- **Agents** (`src/agents/`): Specialized AI agents - news scraper, social media analyzer, deep analyzer, content synthesizer, supervised by a coordinator
- **Graph** (`src/graph/`): LangGraph workflow with state management, nodes, and conditional edges
- **Scrapers** (`src/scrapers/`): Data collection from NewsAPI, Google News RSS, PTT (台灣論壇), Threads, LinkedIn
- **Memory** (`src/memory/`): Personalization system that learns from user feedback and corrections
- **Models** (`src/models/`): Pydantic data models for research requests, content items, analysis results, and video materials

### Data Flow

1. User inputs topic via Streamlit
2. Supervisor agent decomposes into sub-queries
3. Parallel agents scrape news + social media sources
4. Deep analyzer extracts insights for short video
5. Content synthesizer produces VideoMaterial (hook lines, talking points, hashtags)
6. User feedback stored in memory for future personalization

### Storage

- `data/memory/memory.db` - SQLite for user profiles and knowledge graph
- `data/memory/vectorstore/` - Chroma vector store for semantic search
- `data/cache/` - API response caching

## Language

Primary language: Traditional Chinese (zh-TW). Code comments and documentation may be in Chinese.
