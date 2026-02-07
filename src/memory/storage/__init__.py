"""記憶儲存層"""

from src.memory.storage.sqlite_store import SQLiteStore

__all__ = ["SQLiteStore", "VectorStore"]


def __getattr__(name: str):
    if name == "VectorStore":
        from src.memory.storage.vector_store import VectorStore

        return VectorStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
