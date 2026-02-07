"""研究歷史持久化儲存

以 JSON 檔案存放研究歷史，跨 session 保留。
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_HISTORY_FILE = (
    Path(__file__).resolve().parent.parent.parent / "data" / "research_history.json"
)


def load_history() -> list[dict]:
    """從磁碟載入研究歷史"""
    if not _HISTORY_FILE.exists():
        return []
    try:
        return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("無法讀取歷史檔案，回傳空列表")
        return []


def save_history(history: list[dict]) -> None:
    """儲存研究歷史到磁碟"""
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
