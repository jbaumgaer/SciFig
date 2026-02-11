"""
Integration tests for ApplicationModel's layout configuration persistence (serialization/deserialization).
"""

from pathlib import Path
from unittest.mock import MagicMock

from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import FreeConfig, GridConfig, Gutters, Margins


def test_application_model_grid_config_persistence(
    real_application_model, mock_config_service, tmp_path: Path
):
    """
    Test that a GridConfig set in ApplicationModel is correctly serialized and deserialized.
    """
    model = real_application_model
    original_grid_config = GridConfig(
        rows=2,
        cols=3,
        row_ratios=[1, 2],
        col_ratios=[1, 1, 1],
        margins=Margins(left=0.1, right=0.2, top=0.3, bottom=0.4),
        gutters=Gutters(hspace=[0.05], wspace=[0.06, 0.07]),
    )
    model.current_layout_config = original_grid_config

    serialized_data = model.to_dict()

    assert "layout_config" in serialized_data
    assert serialized_data["layout_config"]["mode"] == original_grid_config.mode.value
    assert serialized_data["layout_config"]["rows"] == original_grid_config.rows
    assert serialized_data["layout_config"]["cols"] == original_grid_config.cols
    assert (
        serialized_data["layout_config"]["margins"]["left"]
        == original_grid_config.margins.left
    )

    new_model = ApplicationModel(figure=MagicMock(), config_service=mock_config_service)
    new_model.load_from_dict(serialized_data, temp_dir=tmp_path)

    assert isinstance(new_model.current_layout_config, GridConfig)
    assert new_model.current_layout_config == original_grid_config


def test_application_model_free_config_persistence(
    real_application_model, mock_config_service, tmp_path: Path
):
    """
    Test that a FreeConfig set in ApplicationModel is correctly serialized and deserialized.
    """
    model = real_application_model
    original_free_config = FreeConfig()  # FreeConfig has no extra parameters, just mode
    model.current_layout_config = original_free_config

    serialized_data = model.to_dict()

    assert "layout_config" in serialized_data
    assert serialized_data["layout_config"]["mode"] == original_free_config.mode.value

    new_model = ApplicationModel(figure=MagicMock(), config_service=mock_config_service)
    new_model.load_from_dict(serialized_data, temp_dir=tmp_path)

    assert isinstance(new_model.current_layout_config, FreeConfig)
    assert new_model.current_layout_config == original_free_config
