"""FeedbackProcessor 測試"""

from unittest.mock import AsyncMock, MagicMock


from src.memory.feedback_processor import CorrectionExtraction, FeedbackProcessor
from src.memory.models.feedback import FeedbackType, UserFeedback


def _make_sample_feedback() -> UserFeedback:
    return UserFeedback(
        feedback_id="fb-1",
        user_id="user-1",
        session_id="sess-1",
        original_content="原始內容",
        original_analysis="原始分析",
        agent_type="deep_analyzer",
        feedback_type=FeedbackType.CORRECTION,
        user_correction="修正內容",
        user_explanation="因為原始分析遺漏了重點",
        topics=["AI"],
    )


def _make_mock_manager():
    manager = MagicMock()
    manager.store_correction = AsyncMock()
    manager.mark_feedback_processed = AsyncMock()
    manager.get_unprocessed_feedback = AsyncMock(return_value=[])
    return manager


def _make_mock_llm():
    llm = MagicMock()
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(
        return_value=CorrectionExtraction(
            pattern="提到 AI 時",
            correction="應注意新興工作機會",
            context="AI 話題分析",
            confidence=0.8,
        )
    )
    llm.with_structured_output.return_value = structured_llm
    return llm


class TestFeedbackProcessor:
    async def test_process_feedback(self):
        manager = _make_mock_manager()
        llm = _make_mock_llm()
        processor = FeedbackProcessor(memory_manager=manager, llm=llm)

        feedback = _make_sample_feedback()
        correction = await processor.process_feedback(feedback)

        assert correction.pattern == "提到 AI 時"
        assert correction.correction == "應注意新興工作機會"
        assert correction.confidence == 0.8
        manager.store_correction.assert_awaited_once()
        manager.mark_feedback_processed.assert_awaited_once_with("fb-1")

    async def test_process_all_pending(self):
        feedback = _make_sample_feedback()
        manager = _make_mock_manager()
        manager.get_unprocessed_feedback.return_value = [feedback]
        llm = _make_mock_llm()

        processor = FeedbackProcessor(memory_manager=manager, llm=llm)
        count = await processor.process_all_pending("user-1")

        assert count == 1

    async def test_process_all_pending_with_errors(self):
        feedback = _make_sample_feedback()
        manager = _make_mock_manager()
        manager.get_unprocessed_feedback.return_value = [feedback]

        llm = MagicMock()
        structured_llm = MagicMock()
        structured_llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))
        llm.with_structured_output.return_value = structured_llm

        processor = FeedbackProcessor(memory_manager=manager, llm=llm)
        count = await processor.process_all_pending("user-1")

        assert count == 0

    async def test_process_empty_pending(self):
        manager = _make_mock_manager()
        manager.get_unprocessed_feedback.return_value = []
        llm = _make_mock_llm()

        processor = FeedbackProcessor(memory_manager=manager, llm=llm)
        count = await processor.process_all_pending("user-1")

        assert count == 0
