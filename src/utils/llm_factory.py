"""LLM 工廠模組

提供統一的 LLM 和 Embedding 模型建立介面。
"""

from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.utils.config import settings


def create_chat_model(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    provider: Literal["openai", "anthropic"] | None = None,
) -> BaseChatModel:
    """建立 Chat 模型

    Args:
        model: 模型名稱，預設使用 settings.llm_model
        temperature: 溫度參數，預設使用 settings.llm_temperature
        max_tokens: 最大 token 數，預設使用 settings.llm_max_tokens
        provider: LLM 提供者，預設使用 settings.llm_provider

    Returns:
        ChatOpenAI 或 ChatAnthropic 實例
    """
    _provider = provider or settings.llm_provider
    _model = model or settings.llm_model
    _temperature = temperature if temperature is not None else settings.llm_temperature
    _max_tokens = max_tokens or settings.llm_max_tokens

    if _provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=_model if _model != "gpt-4o-mini" else "claude-3-5-haiku-latest",
            temperature=_temperature,
            max_tokens=_max_tokens,
            api_key=settings.get_anthropic_api_key(),
        )

    # 預設使用 OpenAI
    return ChatOpenAI(
        model=_model,
        temperature=_temperature,
        max_tokens=_max_tokens,
        api_key=settings.get_openai_api_key(),
    )


def create_embedding_model(
    model: str | None = None,
) -> OpenAIEmbeddings:
    """建立 Embedding 模型

    Args:
        model: 模型名稱，預設使用 settings.embedding_model

    Returns:
        OpenAIEmbeddings 實例
    """
    _model = model or settings.embedding_model

    return OpenAIEmbeddings(
        model=_model,
        api_key=settings.get_openai_api_key(),
    )
