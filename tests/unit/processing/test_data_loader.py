import pytest
import pandas as pd
from unittest.mock import MagicMock
from src.processing.data_loader import DataLoader


@pytest.fixture
def data_loader():
    """Provides a fresh DataLoader instance."""
    return DataLoader()


@pytest.fixture
def sample_node():
    """Provides a mock PlotNode."""
    node = MagicMock()
    node.id = "p1"
    return node


@pytest.fixture
def sample_csv_semicolon(tmp_path):
    """Creates a valid sample CSV file with semicolons (as required by current impl)."""
    df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
    file_path = tmp_path / "sample.csv"
    df.to_csv(file_path, index=False, sep=";")
    return file_path


class TestDataLoader:
    """
    Unit tests for DataLoader.
    Verifies data parsing logic and signal emission.
    """

    def test_process_data_success(self, qtbot, data_loader, sample_node, sample_csv_semicolon):
        """Verifies successful data loading and signal emission."""
        # Connect to signals using qtbot
        with qtbot.waitSignal(data_loader.dataReady, timeout=1000) as blocker:
            data_loader.process_data(sample_csv_semicolon, sample_node)
            
        # Verify signal payload
        data, node = blocker.args
        assert node is sample_node
        assert isinstance(data, pd.DataFrame)
        assert list(data.columns) == ["x", "y"]
        assert len(data) == 3

    def test_process_data_file_not_found(self, qtbot, data_loader, sample_node):
        """Verifies error signal emission when file is missing."""
        with qtbot.waitSignal(data_loader.errorOccurred, timeout=1000) as blocker:
            data_loader.process_data("non_existent.csv", sample_node)
            
        error_msg = blocker.args[0]
        assert "no such file" in error_msg.lower()

    def test_process_data_malformed_csv(self, tmp_path, qtbot, data_loader, sample_node):
        """Verifies error handling for files that cannot be parsed as semicolon CSV."""
        # Note: pandas is quite robust, but empty or binary files usually fail
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")
        
        with qtbot.waitSignal(data_loader.errorOccurred, timeout=1000) as blocker:
            data_loader.process_data(empty_file, sample_node)
            
        assert blocker.args[0] is not None

    def test_process_data_standard_comma_csv_fails_parsing(self, tmp_path, qtbot, data_loader, sample_node):
        """
        Demonstrates that standard comma-separated CSVs fail to parse correctly 
        under the current semicolon-only implementation (parsing as a single column).
        """
        df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
        comma_file = tmp_path / "comma.csv"
        df.to_csv(comma_file, index=False, sep=",")
        
        with qtbot.waitSignal(data_loader.dataReady, timeout=1000) as blocker:
            data_loader.process_data(comma_file, sample_node)
            
        data, _ = blocker.args
        # Should have only 1 column because it didn't find semicolons
        assert len(data.columns) == 1
