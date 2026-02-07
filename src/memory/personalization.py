"""個人化引擎

將使用者偏好和歷史修正注入到代理 prompt 中。
"""

import logging

from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """個人化引擎

    組合使用者偏好、相關修正、話題上下文，
    產生個人化的 prompt 附加段落。
    """

    def __init__(self, memory_manager: MemoryManager) -> None:
        self._manager = memory_manager

    async def get_personalized_prompt(
        self,
        user_id: str,
        base_prompt: str,
        current_input: str,
        agent_type: str,
    ) -> str:
        """產生個人化的 prompt

        Args:
            user_id: 使用者 ID
            base_prompt: 基礎 prompt
            current_input: 當前輸入 (用於搜尋相關修正)
            agent_type: 代理類型

        Returns:
            加上個人化附加段落的完整 prompt
        """
        profile = await self._manager.get_or_create_user(user_id)

        # 搜尋相關修正
        corrections = await self._manager.get_relevant_corrections(
            user_id, current_input, limit=5
        )

        # 取得話題上下文
        topic_context = await self._manager.get_topic_context(user_id, current_input)

        # 組合個人化段落
        sections = []

        # 使用者偏好
        sections.append(
            f"## 使用者偏好\n"
            f"- 風格：{profile.preferred_style.value}\n"
            f"- 深度：{profile.analysis_depth.value}\n"
            f"- 語言：{profile.language}"
        )

        if profile.professional_background:
            sections.append(f"- 專業背景：{profile.professional_background}")

        if profile.areas_of_expertise:
            sections.append(f"- 專長領域：{', '.join(profile.areas_of_expertise)}")

        # 過去的修正
        if corrections:
            correction_lines = []
            for c in corrections:
                correction_lines.append(
                    f"- 模式：{c.get('pattern', '')}\n"
                    f"  修正：{c.get('correction', '')}\n"
                    f"  適用：{c.get('context', '')}"
                )
            sections.append(
                "## 過去的修正 (請注意避免重蹈覆轍)\n" + "\n".join(correction_lines)
            )

        # 話題上下文
        topic_pref = topic_context.get("topic_preference")
        if topic_pref:
            sections.append(
                f"## 使用者對此話題的觀點\n"
                f"- 興趣度：{topic_pref.get('interest_level', 0.5)}\n"
                f"- 筆記：{topic_pref.get('perspective_notes', '無')}"
            )

        # 封鎖來源
        if profile.blocked_sources:
            sections.append(f"## 避免引用的來源\n{', '.join(profile.blocked_sources)}")

        personalization = "\n\n".join(sections)
        return f"{base_prompt}\n\n{personalization}"
