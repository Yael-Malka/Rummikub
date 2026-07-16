"""Board service unit tests."""

import pytest
from datetime import datetime, timezone, timedelta

@pytest.mark.anyio
async def test_lazy_timeout_fallback(mocker):
    # This test ensures that when a board's created_at exceeds the timeout+grace duration, 
    # board_service handles it by updating DB and Redis, then throwing PlayFailedError.
    
    # Mock settings
    mocker.patch("src.core.config.settings.PROCESSING_TIMEOUT_SECONDS", 120)
    mocker.patch("src.core.config.settings.PROCESSING_TIMEOUT_GRACE_SECONDS", 15)
    
    # Mock db board
    class MockBoard:
        id = "49701ce8-c174-4b53-855f-ef717f001ccd"
        status = "processing"
        created_at = datetime.now(timezone.utc) - timedelta(seconds=200) # Exceeds 135
        user_id = "test-user"
    
    board = MockBoard()
    mocker.patch("src.services.board_service.get_board_by_id", return_value=board)
    
    mock_session = mocker.Mock()
    mock_session.commit = mocker.AsyncMock()
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = board
    
    mock_redis = mocker.AsyncMock()
    mock_redis.get.return_value = None # No envelope
    
    from src.services.board_service import check_board_status
    from src.core.exceptions import PlayFailedError
    
    with pytest.raises(PlayFailedError) as exc_info:
        await check_board_status("49701ce8-c174-4b53-855f-ef717f001ccd", "test-user", mock_redis, mock_session)
        
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "PROCESSING_TIMED_OUT"
    
    # verify DB updated
    assert board.status == "failed"
    assert board.failure_code == "PROCESSING_TIMED_OUT"
    mock_session.commit.assert_called_once()
