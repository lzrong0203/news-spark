"""向量儲存層

使用 Chroma 提供向量相似度搜尋。
"""

import asyncio
import hashlib
import logging
from pathlib import Path

import chromadb

from src.memory.models.learned_correction import LearnedCorrection
from src.utils.llm_factory import create_embedding_model

logger = logging.getLogger(__name__)


class VectorStore:
    """Chroma 向量儲存

    按 user_id 隔離 collection，提供語意搜尋功能。
    """

    def __init__(self, persist_dir: str = "data/memory/vectorstore") -> None:
        self._persist_dir = Path(persist_dir)
        self._client: chromadb.ClientAPI | None = None
        self._embedding_fn = None

    async def initialize(self) -> None:
        """初始化 Chroma 客戶端"""
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        self._client = await asyncio.to_thread(
            chromadb.PersistentClient,
            path=str(self._persist_dir),
        )

        self._embedding_fn = create_embedding_model()

    def _get_collection(self, user_id: str, collection_type: str):
        """取得或建立 collection"""
        name = f"{user_id}_{collection_type}"
        # Chroma collection 名稱限制: 3-63 字元, [a-zA-Z0-9_-]
        safe_name = name[:63].replace(".", "_")
        return self._client.get_or_create_collection(name=safe_name)

    async def _embed_text(self, text: str) -> list[float]:
        """將文字轉為 embedding"""
        result = await asyncio.to_thread(self._embedding_fn.embed_query, text)
        return result

    # === Corrections ===

    async def store_correction(
        self,
        user_id: str,
        correction: LearnedCorrection,
    ) -> str:
        """儲存修正到向量庫"""
        collection = await asyncio.to_thread(
            self._get_collection, user_id, "corrections"
        )

        text = f"{correction.pattern} | {correction.correction} | {correction.context}"
        embedding = await self._embed_text(text)

        await asyncio.to_thread(
            collection.upsert,
            ids=[correction.correction_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[
                {
                    "correction_id": correction.correction_id,
                    "pattern": correction.pattern,
                    "correction": correction.correction,
                    "context": correction.context,
                    "confidence": correction.confidence,
                }
            ],
        )

        return correction.correction_id

    async def search_corrections(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """搜尋相關修正"""
        collection = await asyncio.to_thread(
            self._get_collection, user_id, "corrections"
        )

        # 檢查 collection 是否有資料
        count = await asyncio.to_thread(collection.count)
        if count == 0:
            return []

        query_embedding = await self._embed_text(query)

        results = await asyncio.to_thread(
            collection.query,
            query_embeddings=[query_embedding],
            n_results=min(limit, count),
            include=["metadatas", "distances"],
        )

        corrections = []
        if results and results["metadatas"]:
            for metadata in results["metadatas"][0]:
                corrections.append(metadata)

        return corrections

    # === Conversations ===

    async def store_conversation(
        self,
        user_id: str,
        session_id: str,
        content: str,
    ) -> None:
        """儲存對話到向量庫"""
        collection = await asyncio.to_thread(
            self._get_collection, user_id, "conversations"
        )

        embedding = await self._embed_text(content)
        doc_id = f"{session_id}_{hashlib.sha256(content.encode()).hexdigest()[:10]}"

        await asyncio.to_thread(
            collection.upsert,
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{"session_id": session_id}],
        )

    async def search_conversations(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """搜尋相關對話"""
        collection = await asyncio.to_thread(
            self._get_collection, user_id, "conversations"
        )

        count = await asyncio.to_thread(collection.count)
        if count == 0:
            return []

        query_embedding = await self._embed_text(query)

        results = await asyncio.to_thread(
            collection.query,
            query_embeddings=[query_embedding],
            n_results=min(limit, count),
            include=["documents", "metadatas", "distances"],
        )

        conversations = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                conversations.append(
                    {
                        "content": doc,
                        "metadata": results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                        "distance": results["distances"][0][i]
                        if results["distances"]
                        else 0,
                    }
                )

        return conversations

    async def delete_user_data(self, user_id: str) -> None:
        """刪除使用者的所有向量資料"""
        for collection_type in ["corrections", "conversations"]:
            name = f"{user_id}_{collection_type}"[:63].replace(".", "_")
            try:
                await asyncio.to_thread(self._client.delete_collection, name)
            except ValueError:
                # Collection 不存在時安全忽略
                logger.debug("Collection %s 不存在，跳過刪除", name)
            except Exception as e:
                logger.error("刪除 collection %s 失敗: %s", name, e)
                raise
