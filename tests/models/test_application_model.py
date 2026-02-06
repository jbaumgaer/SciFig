from unittest.mock import Mock

import pytest

from src.models.application_model import ApplicationModel


# Mock the Signal class as it's a Qt object and can't be instantiated outside a QApplication
class MockSignal:
    def __init__(self, *args, **kwargs):
        pass
    def emit(self, *args, **kwargs):
        pass
    def connect(self, *args, **kwargs):
        pass

# Replace PySide6.QtCore.Signal with MockSignal for testing outside a Qt environment
ApplicationModel.layoutConfigChanged = MockSignal()


@pytest.fixture
def mock_config_service():
    """Mocks the ConfigService."""
    mock_service = Mock()
    mock_service.get.side_effect = lambda key, default=None: {
        "ui.default_layout_mode": "free_form",
        "layout.default_grid_rows": 2,
        "layout.default_grid_cols": 2,
        "layout.grid_margin": 0.05,
        "layout.grid_gutter": 0.05,
    }.get(key, default)
    return mock_service

@pytest.fixture
def mock_figure():
    """Mocks a matplotlib Figure."""
    return Mock()

@pytest.fixture
def application_model(mock_figure, mock_config_service):
    """Provides an ApplicationModel instance with mocked dependencies."""
    model = ApplicationModel(figure=mock_figure, config_service=mock_config_service)
    # Ensure layoutConfigChanged is a mock after instantiation
    model.layoutConfigChanged = MockSignal()
    return model


def test_application_model_initial_layout_config(application_model):
    """
    Test that _current_layout_config is correctly initialized.
    It should default to FreeConfig if 'ui.default_layout_mode' is 'free_form'.
    """
    # TODO: Implement test logic
    pass

def test_application_model_layout_config_serialization(application_model):
    """
    Test that to_dict() and load_from_dict() correctly handle current_layout_config.
    This involves serializing a model with a FreeConfig and a GridConfig,
    and then deserializing it to ensure the config is restored correctly.
    """
    # TODO: Implement test logic
    pass

