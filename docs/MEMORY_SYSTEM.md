# 記憶系統設計文件

## 概述

記憶系統是 News Spark 的核心組件，負責：
1. 儲存和檢索使用者偏好
2. 學習使用者的修正和反饋
3. 提供個人化的分析結果
4. 維護對話歷史和知識圖譜

## 架構圖

```
+--------------------------------------------------+
|                  Memory System                    |
+--------------------------------------------------+
|                                                   |
|  +-------------+  +-------------+  +------------+ |
|  | User Profile|  | Conversation|  | Knowledge  | |
|  | Store       |  | Memory      |  | Graph      | |
|  | (SQLite)    |  | (Vector)    |  | (SQLite)   | |
|  +-------------+  +-------------+  +------------+ |
|         |               |               |         |
|  +------+---------------+---------------+------+  |
|  |            Memory Manager                   |  |
|  +---------------------------------------------+  |
|         |               |               |         |
|  +------+------+ +------+------+ +-----+------+  |
|  | Feedback    | | Context     | | Preference |  |
|  | Processor   | | Retriever   | | Engine     |  |
|  +-------------+ +-------------+ +------------+  |
|                                                   |
+--------------------------------------------------+
                        |
                        v
+--------------------------------------------------+
|              Personalization Engine               |
+--------------------------------------------------+
|  - Prompt injection                               |
|  - Result weighting                               |
|  - Style adaptation                               |
+--------------------------------------------------+
```

## 資料模型

### UserProfile (使用者檔案)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class ContentStyle(str, Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    SIMPLIFIED = "simplified"

class AnalysisDepth(str, Enum):
    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"

class TopicPreference(BaseModel):
    """使用者對特定話題的偏好"""
    topic: str
    interest_level: float = Field(ge=0.0, le=1.0, default=0.5)
    perspective_notes: str = ""
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class SourceTrust(BaseModel):
    """使用者對新聞來源的信任度"""
    source_name: str
    source_url: Optional[str] = None
    trust_level: float = Field(ge=0.0, le=1.0, default=0.5)
    notes: str = ""

class UserProfile(BaseModel):
    """完整的使用者檔案"""
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 基本偏好
    display_name: Optional[str] = None
    language: str = "zh-TW"
    timezone: str = "Asia/Taipei"

    # 內容偏好
    preferred_style: ContentStyle = ContentStyle.CASUAL
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD

    # 話題偏好
    topic_preferences: Dict[str, TopicPreference] = {}

    # 來源偏好
    trusted_sources: List[SourceTrust] = []
    blocked_sources: List[str] = []

    # 觀點元數據
    professional_background: Optional[str] = None
    areas_of_expertise: List[str] = []
    known_biases: List[str] = []

    # 學習設定
    auto_learn_from_feedback: bool = True
    feedback_weight: float = Field(ge=0.1, le=1.0, default=0.7)
```

### UserFeedback (使用者反饋)

```python
class FeedbackType(str, Enum):
    CORRECTION = "correction"      # 修正事實錯誤
    DISAGREEMENT = "disagreement"  # 不同意分析
    PREFERENCE = "preference"      # 風格/格式偏好
    RELEVANCE = "relevance"        # 相關性標記
    QUALITY = "quality"            # 品質評分

class FeedbackSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"

class UserFeedback(BaseModel):
    """單筆使用者反饋"""
    feedback_id: str
    user_id: str
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 上下文
    original_content: str
    original_analysis: str
    agent_type: str

    # 反饋詳情
    feedback_type: FeedbackType
    severity: FeedbackSeverity = FeedbackSeverity.MODERATE
    user_correction: str
    user_explanation: Optional[str] = None

    # 學習元數據
    topics: List[str] = []
    sources_mentioned: List[str] = []

    # 處理狀態
    processed: bool = False
    learned_at: Optional[datetime] = None
```

### LearnedCorrection (學習到的修正)

```python
class LearnedCorrection(BaseModel):
    """已處理的修正，成為系統知識的一部分"""
    correction_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 學習內容
    pattern: str       # 要注意的模式
    correction: str    # 如何修正
    context: str       # 何時適用

    # 學習元數據
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    times_applied: int = 0
    times_confirmed: int = 0
    times_rejected: int = 0

    # 向量嵌入鍵
    embedding_key: Optional[str] = None
```

### KnowledgeNode (知識節點)

```python
class NodeType(str, Enum):
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
    description: Optional[str] = None

    # 使用者特定屬性
    user_sentiment: float = Field(ge=-1.0, le=1.0, default=0.0)
    user_notes: Optional[str] = None
    interaction_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 向量嵌入鍵
    embedding_key: Optional[str] = None
```

## 儲存策略

### 目錄結構

```
data/
├── memory/
│   ├── users/
│   │   └── {user_id}/
│   │       ├── profile.json         # 使用者檔案
│   │       ├── conversations/       # 對話記錄
│   │       │   └── {session_id}.json
│   │       └── feedback/            # 原始反饋
│   │           └── {date}.json
│   ├── memory.db                    # SQLite 資料庫
│   └── vectorstore/                 # Chroma 向量儲存
│       └── {user_id}/
│           ├── conversations/       # 對話嵌入
│           ├── corrections/         # 修正嵌入
│           └── knowledge/           # 知識圖譜嵌入
```

### SQLite Schema

```sql
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
    user_correction TEXT NOT NULL,
    user_explanation TEXT,
    topics_json TEXT,
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
CREATE INDEX IF NOT EXISTS idx_corrections_user ON learned_corrections(user_id);
CREATE INDEX IF NOT EXISTS idx_nodes_user ON knowledge_nodes(user_id);
CREATE INDEX IF NOT EXISTS idx_edges_user ON knowledge_edges(user_id);
```

## 核心服務 API

### MemoryService

```python
class MemoryService:
    """記憶系統的高階 API"""

    # === 使用者管理 ===
    async def get_or_create_user(self, user_id: str) -> UserProfile: ...
    async def update_preferences(self, user_id: str, preferences: Dict) -> UserProfile: ...

    # === 對話管理 ===
    async def start_session(self, user_id: str) -> str: ...
    async def end_session(self, session_id: str) -> ConversationSummary: ...

    # === 個人化 ===
    async def get_personalized_prompt(
        self,
        user_id: str,
        base_prompt: str,
        current_input: str,
        agent_type: str
    ) -> str: ...

    async def get_langchain_memory(
        self,
        user_id: str,
        session_id: str
    ) -> PersonalizedMemory: ...

    # === 反饋 ===
    async def submit_feedback(
        self,
        user_id: str,
        session_id: str,
        feedback_type: FeedbackType,
        original_content: str,
        original_analysis: str,
        user_correction: str,
        explanation: Optional[str] = None
    ) -> str: ...

    async def process_feedback(self, user_id: str) -> int: ...

    # === 資料管理 (GDPR) ===
    async def export_user_data(self, user_id: str) -> Dict: ...
    async def delete_user_data(self, user_id: str) -> bool: ...
```

## 反饋處理流程

```
使用者提交反饋
       ↓
┌─────────────────┐
│ FeedbackProcessor│
│                  │
│ 1. 驗證反饋      │
│ 2. 萃取主題      │
│ 3. 使用 LLM 分析 │
│ 4. 產生模式      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 儲存為           │
│ LearnedCorrection│
│                  │
│ - pattern        │
│ - correction     │
│ - context        │
│ - confidence     │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 向量嵌入         │
│ (語意搜尋)       │
└────────┬────────┘
         ↓
    未來使用時
    語意檢索相關修正
```

## 個人化注入流程

```python
async def get_personalized_prompt(
    self,
    user_id: str,
    base_prompt: str,
    current_input: str,
    agent_type: str
) -> str:
    # 1. 取得使用者檔案
    profile = await self.get_user(user_id)

    # 2. 搜尋相關修正
    corrections = await self.search_corrections(
        user_id,
        current_input,
        limit=5
    )

    # 3. 取得話題上下文
    topic_context = await self.get_topic_context(
        user_id,
        current_input
    )

    # 4. 組合個人化提示
    personalization = f"""
## 使用者偏好
- 風格：{profile.preferred_style}
- 深度：{profile.analysis_depth}
- 專業背景：{profile.professional_background or '未指定'}

## 過去的修正 (請注意)
{self._format_corrections(corrections)}

## 使用者對此話題的觀點
{topic_context}
"""

    return base_prompt + "\n\n" + personalization
```

## LangChain 整合

```python
from langchain.schema import BaseMemory

class PersonalizedMemory(BaseMemory):
    """具有個人化支援的 LangChain 相容記憶"""

    memory_manager: MemoryManager
    user_id: str
    session_id: str

    @property
    def memory_variables(self) -> List[str]:
        return ["history", "user_context", "relevant_corrections"]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # 載入對話歷史
        history = self.memory_manager.get_session_history(self.session_id)

        # 根據輸入載入相關使用者上下文
        query = inputs.get("input", "")
        context = self.memory_manager.get_relevant_context(
            self.user_id,
            query
        )

        return {
            "history": history,
            "user_context": context.user_preferences,
            "relevant_corrections": context.applicable_corrections
        }

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        # 儲存訊息到對話
        self.memory_manager.add_message(
            self.session_id,
            ConversationMessage(
                role=MessageRole.USER,
                content=inputs.get("input", "")
            )
        )
        self.memory_manager.add_message(
            self.session_id,
            ConversationMessage(
                role=MessageRole.ASSISTANT,
                content=outputs.get("output", "")
            )
        )
```

## 隱私與安全

### 資料隔離
- 每個使用者的資料完全隔離
- 向量儲存按 user_id 分區
- 不同使用者之間無法交叉查詢

### GDPR 合規
- `export_user_data()`: 匯出所有使用者資料
- `delete_user_data()`: 完全刪除使用者資料
- 本地儲存，不傳送到外部服務

### 加密選項
- 使用者檔案可選擇性加密
- 敏感偏好（如政治觀點）建議加密儲存

## 效能考量

### 向量搜尋優化
- 使用 Chroma 的本地模式
- 預設使用 `text-embedding-3-small` (較便宜)
- 可選本地嵌入 (sentence-transformers) 作為備援

### 快取策略
- 使用者檔案快取 (LRU)
- 常見查詢結果快取
- 嵌入批次處理

### 延遲目標
- 上下文檢索 < 500ms
- 反饋處理 < 2s
- 完整個人化注入 < 1s
