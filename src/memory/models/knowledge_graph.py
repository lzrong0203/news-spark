"""知識圖譜資料模型"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """知識節點類型"""

    TOPIC = "topic"
    ENTITY = "entity"
    SOURCE = "source"
    CONCEPT = "concept"
    PERSON = "person"
    ORGANIZATION = "organization"


class KnowledgeNode(BaseModel):
    """使用者知識圖譜中的節點"""

    node_id: str
    user_id: str
    node_type: NodeType
    name: str
    description: str | None = None

    # 使用者特定屬性
    user_sentiment: float = Field(ge=-1.0, le=1.0, default=0.0)
    user_notes: str | None = None
    interaction_count: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 向量嵌入鍵
    embedding_key: str | None = None


class KnowledgeEdge(BaseModel):
    """知識圖譜中的邊"""

    edge_id: str
    user_id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    weight: float = Field(ge=0.0, le=1.0, default=0.5)
    user_confirmed: bool = False
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
