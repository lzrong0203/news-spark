"""記憶管理器

協調 SQLiteStore 和 VectorStore，提供統一的記憶操作。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from src.memory.models.feedback import UserFeedback
from src.memory.models.knowledge_graph import KnowledgeNode, NodeType
from src.memory.models.learned_correction import LearnedCorrection
from src.memory.models.user_profile import TopicPreference, UserProfile
from src.memory.storage.sqlite_store import SQLiteStore
from src.utils.config import settings

if TYPE_CHECKING:
    from src.memory.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """記憶管理器

    協調 SQLiteStore (結構化資料) 和 VectorStore (語意搜尋)。
    提供使用者管理、反饋儲存、修正檢索等功能。
    """

    def __init__(
        self,
        sqlite_store: SQLiteStore | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self._sqlite = sqlite_store
        self._vector = vector_store
        self._user_cache: dict[str, UserProfile] = {}

    async def initialize(self) -> None:
        """初始化儲存層"""
        if self._sqlite is None:
            self._sqlite = SQLiteStore(settings.memory_db_path)
        if self._vector is None:
            from src.memory.storage.vector_store import VectorStore

            self._vector = VectorStore(settings.vectorstore_dir)

        await self._sqlite.initialize()
        await self._vector.initialize()

    async def close(self) -> None:
        """關閉儲存層"""
        if self._sqlite:
            await self._sqlite.close()

    # === 使用者管理 ===

    async def get_or_create_user(self, user_id: str) -> UserProfile:
        """取得或建立使用者"""
        # 快取檢查
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        profile = await self._sqlite.get_user(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            await self._sqlite.create_user(profile)

        self._user_cache[user_id] = profile
        return profile

    async def update_user_profile(self, profile: UserProfile) -> None:
        """更新使用者檔案"""
        updated_profile = profile.model_copy(
            update={"updated_at": datetime.now(timezone.utc)}
        )
        await self._sqlite.update_user(updated_profile)
        self._user_cache[updated_profile.user_id] = updated_profile

    # === 反饋管理 ===

    async def store_feedback(self, feedback: UserFeedback) -> None:
        """儲存使用者反饋"""
        await self._sqlite.save_feedback(feedback)

    async def get_unprocessed_feedback(self, user_id: str) -> list[UserFeedback]:
        """取得未處理的反饋"""
        return await self._sqlite.get_unprocessed_feedback(user_id)

    async def mark_feedback_processed(self, feedback_id: str) -> None:
        """標記反饋為已處理"""
        await self._sqlite.mark_feedback_processed(feedback_id)

    # === 修正管理 ===

    async def store_correction(self, correction: LearnedCorrection) -> None:
        """儲存修正 (SQLite + Vector Store)"""
        await self._sqlite.save_correction(correction)
        await self._vector.store_correction(correction.user_id, correction)

    async def get_relevant_corrections(
        self, user_id: str, query: str, limit: int = 5
    ) -> list[dict]:
        """搜尋與查詢相關的修正 (向量相似度)"""
        return await self._vector.search_corrections(user_id, query, limit)

    async def get_corrections(
        self, user_id: str, limit: int = 10
    ) -> list[LearnedCorrection]:
        """取得修正列表 (按信心度排序)"""
        return await self._sqlite.get_corrections(user_id, limit)

    # === 話題上下文 ===

    async def get_topic_context(self, user_id: str, topic: str) -> dict:
        """取得使用者對特定話題的上下文"""
        profile = await self.get_or_create_user(user_id)

        # 從 topic_preferences 取得偏好
        topic_pref = profile.topic_preferences.get(topic)

        # 從知識圖譜取得相關節點
        nodes = await self._sqlite.get_nodes(user_id, NodeType.TOPIC)
        related_nodes = [n for n in nodes if topic.lower() in n.name.lower()]

        # 搜尋相關對話
        conversations = await self._vector.search_conversations(user_id, topic, limit=3)

        return {
            "topic_preference": topic_pref.model_dump() if topic_pref else None,
            "related_knowledge": [n.model_dump() for n in related_nodes],
            "related_conversations": conversations,
            "user_style": profile.preferred_style.value,
            "analysis_depth": profile.analysis_depth.value,
        }

    async def update_topic_preference(
        self,
        user_id: str,
        topic: str,
        interest_level: float,
        notes: str = "",
    ) -> None:
        """更新話題偏好"""
        profile = await self.get_or_create_user(user_id)
        new_prefs = {
            **profile.topic_preferences,
            topic: TopicPreference(
                topic=topic,
                interest_level=interest_level,
                perspective_notes=notes,
            ),
        }
        updated_profile = profile.model_copy(update={"topic_preferences": new_prefs})
        await self.update_user_profile(updated_profile)

    # === 知識圖譜 ===

    async def save_knowledge_node(self, node: KnowledgeNode) -> None:
        """儲存知識節點"""
        await self._sqlite.save_node(node)

    # === GDPR ===

    async def export_user_data(self, user_id: str) -> dict:
        """匯出使用者所有資料"""
        profile = await self._sqlite.get_user(user_id)
        corrections = await self._sqlite.get_corrections(user_id, limit=1000)
        nodes = await self._sqlite.get_nodes(user_id)

        return {
            "profile": profile.model_dump() if profile else None,
            "corrections": [c.model_dump() for c in corrections],
            "knowledge_nodes": [n.model_dump() for n in nodes],
        }

    async def delete_user_data(self, user_id: str) -> bool:
        """刪除使用者所有資料"""
        await self._sqlite.delete_user(user_id)
        await self._vector.delete_user_data(user_id)
        self._user_cache.pop(user_id, None)
        return True
