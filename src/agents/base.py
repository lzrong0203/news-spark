"""Agent 基類模組

定義所有 AI 代理的共同介面和基礎功能。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


@dataclass
class AgentContext:
    """代理執行上下文"""

    session_id: str
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AgentResult(BaseModel, Generic[OutputT]):
    """代理執行結果"""

    success: bool
    data: OutputT | None = None
    error: str | None = None
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """代理基類

    所有專門代理都應繼承此類別並實作 run 方法。

    Type Parameters:
        InputT: 輸入資料類型
        OutputT: 輸出資料類型
    """

    name: str = "base_agent"
    description: str = "Base agent class"

    def __init__(self) -> None:
        self._initialized = False

    async def initialize(self) -> None:
        """初始化代理 (可選覆寫)"""
        self._initialized = True

    @abstractmethod
    async def run(
        self,
        input_data: InputT,
        context: AgentContext | None = None,
    ) -> AgentResult[OutputT]:
        """執行代理主邏輯

        Args:
            input_data: 輸入資料
            context: 執行上下文

        Returns:
            AgentResult 包含執行結果或錯誤
        """
        ...

    async def __call__(
        self,
        input_data: InputT,
        context: AgentContext | None = None,
    ) -> AgentResult[OutputT]:
        """使代理可被呼叫"""
        if not self._initialized:
            await self.initialize()

        start_time = datetime.now(timezone.utc)
        try:
            result = await self.run(input_data, context)
            execution_time = (
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )
            return result.model_copy(update={"execution_time_ms": execution_time})
        except Exception as e:
            execution_time = (
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )
            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )
