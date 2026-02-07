# Runbook

> Operational guide for News Spark. Last updated: 2026-02-08.

## Deployment

### Local Development

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start application
uv run streamlit run app/main.py
```

The app starts at `http://localhost:8501` by default.

### Production Deployment

```bash
# 1. Install production dependencies only
uv sync --no-dev

# 2. Ensure environment variables are set
export OPENAI_API_KEY=sk-xxx
export ANTHROPIC_API_KEY=sk-ant-xxx

# 3. Run with production settings
uv run streamlit run app/main.py \
  --server.port 8501 \
  --server.headless true \
  --server.address 0.0.0.0
```

### Environment Variables

#### Required

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM and embeddings |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models |

#### Optional (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEWSAPI_KEY` | `""` | NewsAPI key for the `NewsAPIScraper` scraper |
| `GOOGLE_API_KEY` | _(none)_ | Google API key |
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

All settings are loaded via `pydantic-settings` in `src/utils/config.py`. They can be set in `.env` or as OS environment variables.

## Storage and Data

### Data Directories

| Path | Purpose | Backup? |
|------|---------|---------|
| `data/memory/memory.db` | SQLite database (user profiles, knowledge graph) | Yes |
| `data/memory/vectorstore/` | Chroma vector store (conversation embeddings) | Yes |
| `data/cache/` | API response cache | No |

### Database Backup

```bash
# Backup SQLite database
cp data/memory/memory.db data/memory/memory.db.bak

# Backup vector store
cp -r data/memory/vectorstore/ data/memory/vectorstore.bak/
```

### Database Reset

```bash
# Remove all user data (irreversible)
rm -f data/memory/memory.db
rm -rf data/memory/vectorstore/

# Clear API cache only
rm -rf data/cache/
```

## Monitoring

### Health Checks

1. **Application**: Visit `http://localhost:8501` -- should load the Streamlit UI
2. **Database**: Check `data/memory/memory.db` exists and is readable
3. **Vector Store**: Check `data/memory/vectorstore/` directory exists
4. **API Connectivity**: Verify LLM calls succeed by submitting a simple topic query

### Log Monitoring

Streamlit logs to stdout. Monitor with:

```bash
uv run streamlit run app/main.py 2>&1 | tee app.log
```

For more verbose output, set `LOG_LEVEL=DEBUG` in your `.env` file.

### Key Metrics to Watch

| Metric | Where | Threshold |
|--------|-------|-----------|
| API response time | LangChain callbacks | > 30s indicates issues |
| SQLite DB size | `data/memory/memory.db` | > 500 MB consider archiving |
| Vector store size | `data/memory/vectorstore/` | > 1 GB consider pruning |
| API error rate | stdout/app.log | > 5% investigate |

### API Rate Limits

The application includes rate limiting (`src/utils/rate_limiter.py`). The default is 60 requests per minute (configurable via `RATE_LIMIT_REQUESTS_PER_MINUTE`). Monitor for:
- `429 Too Many Requests` from NewsAPI
- OpenAI/Anthropic API quota exhaustion
- PTT/Threads scraping throttling

## Common Issues

### 1. Missing API Keys

**Symptom**: Application crashes on startup or LLM calls fail.

**Fix**: Ensure `.env` file exists with valid keys:
```bash
cat .env  # Verify keys are set (not placeholder values)
```

Note: The `Settings` class in `src/utils/config.py` defaults `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` to empty strings, so the application may start but fail when making API calls if real keys are not provided.

### 2. SQLite Database Locked

**Symptom**: `database is locked` errors.

**Fix**: Ensure only one instance of the app is running. The async SQLite driver (`aiosqlite`) handles concurrent reads but not concurrent writes from multiple processes.

```bash
# Check for running instances
ps aux | grep streamlit
# Kill stale processes if needed
```

### 3. Chroma Vector Store Corruption

**Symptom**: Embedding search returns errors or empty results.

**Fix**:
```bash
# Backup and reset vector store
mv data/memory/vectorstore/ data/memory/vectorstore.bak/
# Restart app - vector store will be recreated
```

### 4. Scraper Failures

**Symptom**: No results from specific sources.

| Source | Common Issue | Fix |
|--------|-------------|-----|
| NewsAPI | API key invalid/expired | Verify `NEWSAPI_KEY` in `.env` |
| Google News RSS | Feed URL changed | Check `src/scrapers/google_news.py` feed URLs |
| PTT | Site structure changed | Update selectors in `src/scrapers/ptt.py` |
| Threads | API rate limit / auth | Check Meta API credentials or cooldown |
| LinkedIn | Anti-scraping blocks | Use manual URL input mode, rotate user agents |

Source files for each scraper:
- `src/scrapers/news_api.py` -- `NewsAPIScraper`
- `src/scrapers/google_news.py` -- `GoogleNewsScraper`
- `src/scrapers/ptt.py` -- `PTTScraper`
- `src/scrapers/threads.py` -- `ThreadsScraper`
- `src/scrapers/linkedin.py` -- `LinkedInScraper`, `LinkedInURLHandler`

### 5. LLM Cost Spikes

**Symptom**: Unexpected API billing.

**Mitigation**:
- Switch `LLM_PROVIDER` to `anthropic` and use a smaller model
- Lower `LLM_MODEL` to a cheaper variant (e.g., `gpt-4o-mini` instead of `gpt-4o`)
- Enable API response caching via `CACHE_TTL_SECONDS` (default 3600s)
- Set research depth parameter lower (1-2 instead of 3-5)
- Monitor token usage in LangChain callbacks

### 6. Port Already in Use

**Symptom**: `Address already in use` on startup.

**Fix**:
```bash
# Find process using port 8501
lsof -i :8501
# Kill it or use a different port
uv run streamlit run app/main.py --server.port 8502
```

### 7. Dependency Installation Failures

**Symptom**: `uv sync` fails with build errors.

**Fix**:
```bash
# Ensure Python >= 3.11 is available
python3 --version

# Clear uv cache and retry
uv cache clean
uv sync

# If specific package fails (e.g., chromadb), check system dependencies
# chromadb requires SQLite >= 3.35.0
sqlite3 --version
```

### 8. Playwright Browser Not Installed

**Symptom**: E2E tests fail with browser not found errors.

**Fix**:
```bash
uv run playwright install
uv run playwright install-deps  # Install OS-level dependencies
```

## Rollback Procedures

### Application Rollback

```bash
# 1. Find the last known good commit
git log --oneline -10

# 2. Checkout the stable version
git checkout <commit-hash>

# 3. Reinstall dependencies
uv sync

# 4. Restart application
uv run streamlit run app/main.py
```

### Database Rollback

```bash
# Restore from backup
cp data/memory/memory.db.bak data/memory/memory.db
cp -r data/memory/vectorstore.bak/ data/memory/vectorstore/
```

### Dependency Rollback

The `uv.lock` file pins exact dependency versions. To rollback:

```bash
# Restore lock file from a previous commit
git checkout <commit-hash> -- uv.lock

# Reinstall exact versions
uv sync
```

### Configuration Rollback

If a bad configuration causes failures:

```bash
# Reset to defaults by removing .env overrides
# The application uses sane defaults defined in src/utils/config.py
mv .env .env.broken
cp .env.example .env
# Re-add only the required API keys
```

## Maintenance

### Regular Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Backup database | Weekly | `cp data/memory/memory.db data/memory/memory.db.bak` |
| Backup vector store | Weekly | `cp -r data/memory/vectorstore/ data/memory/vectorstore.bak/` |
| Clear API cache | Monthly | `rm -rf data/cache/*` |
| Update dependencies | Monthly | `uv lock --upgrade && uv sync` |
| Run full test suite | Before deploy | `uv run pytest tests/ -v` |
| Check lint | Before commit | `uv run ruff check .` |
| Check coverage | Weekly | `uv run pytest tests/unit -v --cov=src --cov-report=term-missing` |

### Dependency Updates

```bash
# Update all dependencies
uv lock --upgrade
uv sync

# Run tests to verify
uv run pytest tests/ -v

# If tests fail, rollback
git checkout -- uv.lock
uv sync
```

### Pre-Deploy Checklist

- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] Lint clean: `uv run ruff check .`
- [ ] Coverage >= 80%: `uv run pytest tests/unit -v --cov=src --cov-report=term-missing`
- [ ] `.env` has valid API keys (not placeholder values)
- [ ] Database backed up
- [ ] `uv.lock` committed (pinned dependency versions)
