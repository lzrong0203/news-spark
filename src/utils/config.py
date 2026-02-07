"""應用程式配置管理模組

使用 pydantic-settings 從 .env 檔案載入環境變數。
所有 API Keys 會自動從 .env 檔案讀取。
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """應用程式設定

    自動從 .env 檔案載入設定：
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    - NEWSAPI_KEY
    - 其他環境變數
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === API Keys (從 .env 讀取，使用 SecretStr 保護) ===
    openai_api_key: SecretStr = Field(
        default=SecretStr(""), description="OpenAI API Key (OPENAI_API_KEY)"
    )
    anthropic_api_key: SecretStr = Field(
        default=SecretStr(""), description="Anthropic API Key (ANTHROPIC_API_KEY)"
    )
    newsapi_key: SecretStr = Field(
        default=SecretStr(""), description="NewsAPI Key (NEWSAPI_KEY)"
    )

    # === LLM 設定 ===
    llm_provider: Literal["openai", "anthropic"] = Field(
        default="openai", description="LLM 提供者 (LLM_PROVIDER)"
    )
    llm_model: str = Field(
        default="gpt-4o-mini", description="LLM 模型名稱 (LLM_MODEL)"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", description="Embedding 模型 (EMBEDDING_MODEL)"
    )
    llm_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="LLM 溫度 (LLM_TEMPERATURE)"
    )
    llm_max_tokens: int = Field(
        default=4096, ge=1, description="最大 token 數 (LLM_MAX_TOKENS)"
    )

    # === 速率限制 ===
    rate_limit_requests_per_minute: int = Field(
        default=60, ge=1, description="每分鐘最大請求數"
    )

    # === 快取設定 ===
    cache_ttl_seconds: int = Field(default=3600, ge=0, description="快取 TTL (秒)")
    cache_dir: str = Field(default="data/cache", description="快取目錄")

    # === 記憶系統 ===
    memory_db_path: str = Field(
        default="data/memory/memory.db", description="SQLite 路徑"
    )
    vectorstore_dir: str = Field(
        default="data/memory/vectorstore", description="向量儲存目錄"
    )

    # === 應用程式 ===
    debug: bool = Field(default=False, description="除錯模式 (DEBUG)")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="日誌等級 (LOG_LEVEL)"
    )

    def get_openai_api_key(self) -> str:
        """取得 OpenAI API Key (明文)"""
        return self.openai_api_key.get_secret_value()

    def get_anthropic_api_key(self) -> str:
        """取得 Anthropic API Key (明文)"""
        return self.anthropic_api_key.get_secret_value()

    def get_newsapi_key(self) -> str:
        """取得 NewsAPI Key (明文)"""
        return self.newsapi_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    """取得應用程式設定 (快取單例)"""
    return Settings()


# 方便直接 import 使用
settings = get_settings()
