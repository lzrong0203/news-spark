"""記憶服務 API

提供記憶系統的高階 Facade 介面。
"""

import logging
import re
import uuid

from src.memory.feedback_processor import FeedbackProcessor
from src.memory.manager import MemoryManager
from src.memory.models.feedback import FeedbackType, UserFeedback
from src.memory.models.user_profile import UserProfile
from src.memory.personalization import PersonalizationEngine

logger = logging.getLogger(__name__)

_USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")


def _validate_user_id(user_id: str) -> str:
    """驗證 user_id 格式

    Args:
        user_id: 使用者 ID

    Returns:
        驗證通過的 user_id

    Raises:
        ValueError: user_id 格式無效
    """
    if not _USER_ID_PATTERN.match(user_id):
        raise ValueError(
            f"無效的 user_id 格式: {user_id!r}。"
            "僅允許英數字、底線、連字號，長度 1-50。"
        )
    return user_id


class MemoryService:
    """記憶系統的高階 API

    統一管理記憶管理器、反饋處理器、個人化引擎。
    """

    def __init__(self) -> None:
        self._manager: MemoryManager | None = None
        self._feedback_processor: FeedbackProcessor | None = None
        self._personalization: PersonalizationEngine | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """初始化所有元件"""
        self._manager = MemoryManager()
        await self._manager.initialize()

        self._feedback_processor = FeedbackProcessor(self._manager)
        self._personalization = PersonalizationEngine(self._manager)
        self._initialized = True

    def _ensure_initialized(self) -> None:
        """確保服務已初始化"""
        if not self._initialized:
            raise RuntimeError("MemoryService 尚未初始化，請先呼叫 initialize()")

    async def close(self) -> None:
        """關閉所有元件"""
        if self._manager:
            await self._manager.close()

    # === 使用者管理 ===

    async def get_or_create_user(self, user_id: str) -> UserProfile:
        """取得或建立使用者"""
        self._ensure_initialized()
        _validate_user_id(user_id)
        return await self._manager.get_or_create_user(user_id)

    # 允許使用者更新的欄位白名單
    _UPDATABLE_FIELDS = frozenset({
        "display_name",
        "language",
        "preferred_style",
        "analysis_depth",
        "blocked_sources",
    })

    async def update_preferences(self, user_id: str, preferences: dict) -> UserProfile:
        """更新使用者偏好

        Args:
            user_id: 使用者 ID
            preferences: 偏好欄位 dict (key=欄位名, value=新值)

        Returns:
            更新後的 UserProfile
        """
        self._ensure_initialized()
        _validate_user_id(user_id)
        profile = await self._manager.get_or_create_user(user_id)

        safe_updates = {
            k: v for k, v in preferences.items() if k in self._UPDATABLE_FIELDS
        }
        updated_profile = profile.model_copy(update=safe_updates)

        await self._manager.update_user_profile(updated_profile)
        return updated_profile

    # === 個人化 ===

    async def get_personalized_prompt(
        self,
        user_id: str,
        base_prompt: str,
        current_input: str,
        agent_type: str,
    ) -> str:
        """取得個人化 prompt"""
        self._ensure_initialized()
        return await self._personalization.get_personalized_prompt(
            user_id, base_prompt, current_input, agent_type
        )

    # === 反饋 ===

    async def submit_feedback(  # noqa: PLR0913
        self,
        user_id: str,
        session_id: str,
        feedback_type: FeedbackType,
        original_content: str,
        original_analysis: str,
        user_correction: str,
        agent_type: str = "general",
        explanation: str | None = None,
    ) -> str:
        """提交反饋

        Returns:
            feedback_id
        """
        self._ensure_initialized()
        _validate_user_id(user_id)
        feedback_id = str(uuid.uuid4())
        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            session_id=session_id,
            original_content=original_content,
            original_analysis=original_analysis,
            agent_type=agent_type,
            feedback_type=feedback_type,
            user_correction=user_correction,
            user_explanation=explanation,
        )

        await self._manager.store_feedback(feedback)
        return feedback_id

    async def process_feedback(self, user_id: str) -> int:
        """處理所有待處理反饋

        Returns:
            處理的反饋數量
        """
        self._ensure_initialized()
        _validate_user_id(user_id)
        return await self._feedback_processor.process_all_pending(user_id)

    # === GDPR ===

    async def export_user_data(self, user_id: str) -> dict:
        """匯出使用者所有資料"""
        self._ensure_initialized()
        _validate_user_id(user_id)
        return await self._manager.export_user_data(user_id)

    async def delete_user_data(self, user_id: str) -> bool:
        """刪除使用者所有資料"""
        self._ensure_initialized()
        _validate_user_id(user_id)
        return await self._manager.delete_user_data(user_id)
