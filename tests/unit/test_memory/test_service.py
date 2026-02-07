"""MemoryService 測試"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.memory.models.feedback import FeedbackType
from src.memory.models.user_profile import ContentStyle, UserProfile
from src.memory.service import MemoryService


@pytest.fixture
def mock_manager():
    manager = MagicMock()
    manager.initialize = AsyncMock()
    manager.close = AsyncMock()
    manager.get_or_create_user = AsyncMock(
        return_value=UserProfile(user_id="test-user")
    )
    manager.update_user_profile = AsyncMock()
    manager.store_feedback = AsyncMock()
    manager.export_user_data = AsyncMock(return_value={"profile": None})
    manager.delete_user_data = AsyncMock(return_value=True)
    manager.get_unprocessed_feedback = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def mock_feedback_processor():
    processor = MagicMock()
    processor.process_all_pending = AsyncMock(return_value=2)
    return processor


@pytest.fixture
def mock_personalization():
    engine = MagicMock()
    engine.get_personalized_prompt = AsyncMock(return_value="personalized prompt")
    return engine


class TestMemoryService:
    async def test_initialize(self):
        service = MemoryService()

        with patch("src.memory.service.MemoryManager") as MockManager:
            mock_mgr = MagicMock()
            mock_mgr.initialize = AsyncMock()
            MockManager.return_value = mock_mgr

            await service.initialize()
            assert service._initialized is True
            mock_mgr.initialize.assert_awaited_once()

    async def test_close(self, mock_manager):
        service = MemoryService()
        service._manager = mock_manager
        await service.close()
        mock_manager.close.assert_awaited_once()

    async def test_get_or_create_user(self, mock_manager):
        service = MemoryService()
        service._manager = mock_manager
        service._initialized = True

        user = await service.get_or_create_user("test-user")
        assert user.user_id == "test-user"

    async def test_update_preferences(self, mock_manager):
        service = MemoryService()
        service._manager = mock_manager
        service._initialized = True

        result = await service.update_preferences(
            "test-user", {"preferred_style": ContentStyle.FORMAL}
        )
        assert result.preferred_style == ContentStyle.FORMAL
        mock_manager.update_user_profile.assert_awaited_once()

    async def test_get_personalized_prompt(self, mock_manager, mock_personalization):
        service = MemoryService()
        service._manager = mock_manager
        service._personalization = mock_personalization
        service._initialized = True

        result = await service.get_personalized_prompt(
            "user-1", "base prompt", "AI topic", "deep_analyzer"
        )
        assert result == "personalized prompt"

    async def test_submit_feedback(self, mock_manager):
        service = MemoryService()
        service._manager = mock_manager
        service._initialized = True

        fb_id = await service.submit_feedback(
            user_id="user-1",
            session_id="sess-1",
            feedback_type=FeedbackType.CORRECTION,
            original_content="content",
            original_analysis="analysis",
            user_correction="correction",
        )
        assert isinstance(fb_id, str)
        mock_manager.store_feedback.assert_awaited_once()

    async def test_process_feedback(self, mock_manager, mock_feedback_processor):
        service = MemoryService()
        service._manager = mock_manager
        service._feedback_processor = mock_feedback_processor
        service._initialized = True

        count = await service.process_feedback("user-1")
        assert count == 2

    async def test_export_user_data(self, mock_manager):
        service = MemoryService()
        service._manager = mock_manager
        service._initialized = True

        data = await service.export_user_data("user-1")
        assert "profile" in data

    async def test_delete_user_data(self, mock_manager):
        service = MemoryService()
        service._manager = mock_manager
        service._initialized = True

        result = await service.delete_user_data("user-1")
        assert result is True
