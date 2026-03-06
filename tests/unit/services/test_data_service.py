import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.services.data_service import DataService
from src.shared.events import Events
from src.models.nodes.plot_node import PlotNode


@pytest.fixture
def data_service(mock_application_model, mock_event_aggregator):
    """Provides a DataService instance."""
    return DataService(model=mock_application_model, event_aggregator=mock_event_aggregator)


@pytest.fixture
def sample_node():
    """Provides a mock PlotNode."""
    node = MagicMock(spec=PlotNode)
    node.id = "p1"
    return node


class TestDataService:
    """
    Unit tests for DataService.
    Verifies the orchestration of background data loading tasks.
    """

    def test_handle_load_request_starts_thread(self, data_service, mock_application_model, sample_node, tmp_path, mocker):
        """Verifies that a valid load request initializes a thread and worker."""
        # 1. Setup mocks
        mock_thread_cls = mocker.patch("src.services.data_service.QThread")
        mock_loader_cls = mocker.patch("src.services.data_service.DataLoader")
        
        mock_application_model.scene_root.find_node_by_id.return_value = sample_node
        
        # Create a real file so the exists() check passes
        test_file = tmp_path / "test.csv"
        test_file.write_text("data")
        
        # 2. Execute
        data_service.handle_load_request("p1", test_file)
        
        # 3. Verify
        assert "p1" in data_service._active_tasks
        mock_thread_cls.return_value.start.assert_called_once()
        mock_loader_cls.return_value.moveToThread.assert_called_once_with(mock_thread_cls.return_value)

    def test_handle_load_request_fails_on_missing_file(self, data_service, caplog):
        """Verifies that missing files are handled gracefully."""
        data_service.handle_load_request("p1", Path("non_existent.csv"))
        assert "File not found" in caplog.text
        assert "p1" not in data_service._active_tasks

    def test_handle_load_request_fails_on_missing_node(self, data_service, mock_application_model, tmp_path, caplog):
        """Verifies that requests for invalid node IDs are rejected."""
        mock_application_model.scene_root.find_node_by_id.return_value = None
        test_file = tmp_path / "test.csv"
        test_file.write_text("data")
        
        data_service.handle_load_request("invalid_id", test_file)
        assert "not found" in caplog.text
        assert "invalid_id" not in data_service._active_tasks

    def test_on_data_ready_publishes_event(self, data_service, mock_event_aggregator, sample_node):
        """Verifies that the correct event is published when data is ready."""
        df = MagicMock()
        mock_thread = MagicMock()
        file_path = Path("test.csv")
        
        data_service._on_data_ready(df, sample_node, file_path, mock_thread)
        
        mock_event_aggregator.publish.assert_called_once_with(
            Events.NODE_DATA_LOADED,
            node_id="p1",
            data=df,
            file_path=file_path
        )
        mock_thread.quit.assert_called_once()

    def test_cleanup_task_removes_from_active_tasks(self, data_service):
        """Verifies that tasks are correctly removed from the registry."""
        data_service._active_tasks["p1"] = (MagicMock(), MagicMock())
        
        data_service._cleanup_task("p1")
        
        assert "p1" not in data_service._active_tasks

    def test_duplicate_request_is_ignored(self, data_service, tmp_path, caplog):
        """Ensures that a second request for the same node is ignored if one is active."""
        data_service._active_tasks["p1"] = (MagicMock(), MagicMock())
        test_file = tmp_path / "test.csv"
        test_file.write_text("data")
        
        data_service.handle_load_request("p1", test_file)
        
        assert "Load already in progress" in caplog.text
