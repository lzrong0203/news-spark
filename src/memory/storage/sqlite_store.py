"""SQLite 儲存層

使用 aiosqlite 提供非同步 CRUD 操作。
"""

import json
import logging
from pathlib import Path

import aiosqlite

from src.memory.models.feedback import UserFeedback
from src.memory.models.knowledge_graph import KnowledgeEdge, KnowledgeNode, NodeType
from src.memory.models.learned_correction import LearnedCorrection
from src.memory.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """
-- 使用者表
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    profile_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 反饋表
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    original_content TEXT NOT NULL,
    original_analysis TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    user_correction TEXT NOT NULL,
    user_explanation TEXT,
    topics_json TEXT,
    sources_json TEXT,
    processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    learned_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 學習到的修正表
CREATE TABLE IF NOT EXISTS learned_corrections (
    correction_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    pattern TEXT NOT NULL,
    correction TEXT NOT NULL,
    context TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    times_applied INTEGER DEFAULT 0,
    times_confirmed INTEGER DEFAULT 0,
    times_rejected INTEGER DEFAULT 0,
    embedding_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 知識圖譜節點
CREATE TABLE IF NOT EXISTS knowledge_nodes (
    node_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    node_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    user_sentiment REAL DEFAULT 0.0,
    user_notes TEXT,
    interaction_count INTEGER DEFAULT 0,
    embedding_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 知識圖譜邊
CREATE TABLE IF NOT EXISTS knowledge_edges (
    edge_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    weight REAL DEFAULT 0.5,
    user_confirmed INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (source_node_id) REFERENCES knowledge_nodes(node_id),
    FOREIGN KEY (target_node_id) REFERENCES knowledge_nodes(node_id)
);

-- 效能索引
CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_processed ON feedback(user_id, processed);
CREATE INDEX IF NOT EXISTS idx_corrections_user ON learned_corrections(user_id);
CREATE INDEX IF NOT EXISTS idx_nodes_user ON knowledge_nodes(user_id);
CREATE INDEX IF NOT EXISTS idx_edges_user ON knowledge_edges(user_id);
"""


class SQLiteStore:
    """SQLite 非同步儲存層"""

    def __init__(self, db_path: str = "data/memory/memory.db") -> None:
        self._db_path = Path(db_path)
        self._db: aiosqlite.Connection | None = None

    @property
    def _conn(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("SQLiteStore 尚未初始化，請先呼叫 initialize()")
        return self._db

    async def initialize(self) -> None:
        """初始化資料庫"""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self._db_path))
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.executescript(_SCHEMA_SQL)
        await self._db.commit()

    async def close(self) -> None:
        """關閉資料庫連線"""
        if self._db:
            await self._db.close()
            self._db = None

    # === User CRUD ===

    async def get_user(self, user_id: str) -> UserProfile | None:
        """取得使用者"""
        async with self._conn.execute(
            "SELECT profile_json FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return UserProfile.model_validate_json(row[0])

    async def create_user(self, profile: UserProfile) -> None:
        """建立使用者"""
        await self._conn.execute(
            "INSERT INTO users (user_id, profile_json) VALUES (?, ?)",
            (profile.user_id, profile.model_dump_json()),
        )
        await self._conn.commit()

    async def update_user(self, profile: UserProfile) -> None:
        """更新使用者"""
        await self._conn.execute(
            "UPDATE users SET profile_json = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (profile.model_dump_json(), profile.user_id),
        )
        await self._conn.commit()

    async def delete_user(self, user_id: str) -> None:
        """刪除使用者及其所有資料"""
        await self._conn.execute("BEGIN")
        try:
            await self._conn.execute(
                "DELETE FROM knowledge_edges WHERE user_id = ?", (user_id,)
            )
            await self._conn.execute(
                "DELETE FROM knowledge_nodes WHERE user_id = ?", (user_id,)
            )
            await self._conn.execute(
                "DELETE FROM learned_corrections WHERE user_id = ?", (user_id,)
            )
            await self._conn.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
            await self._conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            await self._conn.commit()
        except Exception:
            await self._conn.rollback()
            raise

    # === Feedback CRUD ===

    async def save_feedback(self, feedback: UserFeedback) -> None:
        """儲存反饋"""
        await self._conn.execute(
            """INSERT INTO feedback
            (feedback_id, user_id, session_id, feedback_type, severity,
             original_content, original_analysis, agent_type,
             user_correction, user_explanation, topics_json, sources_json, processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                feedback.feedback_id,
                feedback.user_id,
                feedback.session_id,
                feedback.feedback_type.value,
                feedback.severity.value,
                feedback.original_content,
                feedback.original_analysis,
                feedback.agent_type,
                feedback.user_correction,
                feedback.user_explanation,
                json.dumps(feedback.topics, ensure_ascii=False),
                json.dumps(feedback.sources_mentioned, ensure_ascii=False),
                int(feedback.processed),
            ),
        )
        await self._conn.commit()

    async def get_unprocessed_feedback(self, user_id: str) -> list[UserFeedback]:
        """取得未處理的反饋"""
        results = []
        async with self._conn.execute(
            "SELECT * FROM feedback WHERE user_id = ? AND processed = 0 ORDER BY created_at",
            (user_id,),
        ) as cursor:
            async for row in cursor:
                results.append(self._row_to_feedback(row))
        return results

    async def mark_feedback_processed(self, feedback_id: str) -> None:
        """標記反饋為已處理"""
        await self._conn.execute(
            "UPDATE feedback SET processed = 1, learned_at = CURRENT_TIMESTAMP WHERE feedback_id = ?",
            (feedback_id,),
        )
        await self._conn.commit()

    # === Corrections CRUD ===

    async def save_correction(self, correction: LearnedCorrection) -> None:
        """儲存學習到的修正"""
        await self._conn.execute(
            """INSERT INTO learned_corrections
            (correction_id, user_id, pattern, correction, context,
             confidence, times_applied, times_confirmed, times_rejected, embedding_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                correction.correction_id,
                correction.user_id,
                correction.pattern,
                correction.correction,
                correction.context,
                correction.confidence,
                correction.times_applied,
                correction.times_confirmed,
                correction.times_rejected,
                correction.embedding_key,
            ),
        )
        await self._conn.commit()

    async def get_corrections(
        self, user_id: str, limit: int = 10
    ) -> list[LearnedCorrection]:
        """取得修正列表"""
        results = []
        async with self._conn.execute(
            """SELECT * FROM learned_corrections
            WHERE user_id = ? ORDER BY confidence DESC, created_at DESC LIMIT ?""",
            (user_id, limit),
        ) as cursor:
            async for row in cursor:
                results.append(self._row_to_correction(row))
        return results

    async def update_correction_stats(
        self, correction_id: str, confirmed: bool
    ) -> None:
        """更新修正統計"""
        if confirmed:
            await self._conn.execute(
                """UPDATE learned_corrections
                SET times_confirmed = times_confirmed + 1,
                    times_applied = times_applied + 1,
                    confidence = MIN(1.0, confidence + 0.05)
                WHERE correction_id = ?""",
                (correction_id,),
            )
        else:
            await self._conn.execute(
                """UPDATE learned_corrections
                SET times_rejected = times_rejected + 1,
                    times_applied = times_applied + 1,
                    confidence = MAX(0.0, confidence - 0.1)
                WHERE correction_id = ?""",
                (correction_id,),
            )
        await self._conn.commit()

    # === Knowledge Graph ===

    async def save_node(self, node: KnowledgeNode) -> None:
        """儲存知識節點"""
        await self._conn.execute(
            """INSERT OR REPLACE INTO knowledge_nodes
            (node_id, user_id, node_type, name, description,
             user_sentiment, user_notes, interaction_count, embedding_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                node.node_id,
                node.user_id,
                node.node_type.value,
                node.name,
                node.description,
                node.user_sentiment,
                node.user_notes,
                node.interaction_count,
                node.embedding_key,
            ),
        )
        await self._conn.commit()

    async def get_nodes(
        self, user_id: str, node_type: NodeType | None = None
    ) -> list[KnowledgeNode]:
        """取得知識節點"""
        results = []
        if node_type:
            query = "SELECT * FROM knowledge_nodes WHERE user_id = ? AND node_type = ?"
            params = (user_id, node_type.value)
        else:
            query = "SELECT * FROM knowledge_nodes WHERE user_id = ?"
            params = (user_id,)

        async with self._conn.execute(query, params) as cursor:
            async for row in cursor:
                results.append(self._row_to_node(row))
        return results

    async def save_edge(self, edge: KnowledgeEdge) -> None:
        """儲存知識邊"""
        await self._conn.execute(
            """INSERT OR REPLACE INTO knowledge_edges
            (edge_id, user_id, source_node_id, target_node_id,
             relation_type, weight, user_confirmed, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                edge.edge_id,
                edge.user_id,
                edge.source_node_id,
                edge.target_node_id,
                edge.relation_type,
                edge.weight,
                int(edge.user_confirmed),
                edge.notes,
            ),
        )
        await self._conn.commit()

    async def get_related_nodes(self, node_id: str) -> list[tuple[KnowledgeNode, str]]:
        """取得與指定節點相關的節點"""
        results = []
        async with self._conn.execute(
            """SELECT n.*, e.relation_type FROM knowledge_edges e
            JOIN knowledge_nodes n ON e.target_node_id = n.node_id
            WHERE e.source_node_id = ?""",
            (node_id,),
        ) as cursor:
            async for row in cursor:
                node = self._row_to_node(row)
                relation = row["relation_type"]
                results.append((node, relation))
        return results

    # === Private helpers ===

    def _row_to_feedback(self, row) -> UserFeedback:
        """將 DB row 轉為 UserFeedback"""
        topics = json.loads(row["topics_json"]) if row["topics_json"] else []
        sources = json.loads(row["sources_json"]) if row["sources_json"] else []
        return UserFeedback(
            feedback_id=row["feedback_id"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            feedback_type=row["feedback_type"],
            severity=row["severity"],
            original_content=row["original_content"],
            original_analysis=row["original_analysis"],
            agent_type=row["agent_type"],
            user_correction=row["user_correction"],
            user_explanation=row["user_explanation"],
            topics=topics,
            sources_mentioned=sources,
            processed=bool(row["processed"]),
        )

    def _row_to_correction(self, row) -> LearnedCorrection:
        """將 DB row 轉為 LearnedCorrection"""
        return LearnedCorrection(
            correction_id=row["correction_id"],
            user_id=row["user_id"],
            pattern=row["pattern"],
            correction=row["correction"],
            context=row["context"],
            confidence=row["confidence"],
            times_applied=row["times_applied"],
            times_confirmed=row["times_confirmed"],
            times_rejected=row["times_rejected"],
            embedding_key=row["embedding_key"],
        )

    def _row_to_node(self, row) -> KnowledgeNode:
        """將 DB row 轉為 KnowledgeNode"""
        return KnowledgeNode(
            node_id=row["node_id"],
            user_id=row["user_id"],
            node_type=row["node_type"],
            name=row["name"],
            description=row["description"],
            user_sentiment=row["user_sentiment"],
            user_notes=row["user_notes"],
            interaction_count=row["interaction_count"],
            embedding_key=row["embedding_key"],
        )
