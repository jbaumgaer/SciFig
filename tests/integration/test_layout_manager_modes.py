"""
Integration tests for LayoutManager's mode switching and engine activation.
"""

from src.models.layout.free_layout_engine import FreeLayoutEngine
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.shared.constants import LayoutMode


def test_layout_mode_switching(
    real_application_model, real_layout_controller, real_layout_manager
):
    """
    Integration Test: Layout Mode Switching.
    This test should:
    - Initialize a real ApplicationModel, LayoutController, and LayoutManager.
    - Set the layout mode to GRID via LayoutController.set_layout_mode.
    - Assert that ApplicationModel.current_layout_config.mode is GRID.
    - Set the layout mode to FREE_FORM.
    - Assert that ApplicationModel.current_layout_config.mode is FREE_FORM.
    - Ensure that the LayoutManager's internal active engine changes accordingly.
    """
    model = real_application_model
    controller = real_layout_controller
    layout_manager = real_layout_manager

    # Initially Free-Form as per default config
    assert model.current_layout_config.mode == LayoutMode.FREE_FORM
    assert isinstance(layout_manager.get_active_engine(), FreeLayoutEngine)

    # Set to GRID mode
    controller.set_layout_mode(LayoutMode.GRID)
    assert layout_manager.ui_selected_layout_mode == LayoutMode.GRID
    assert model.current_layout_config.mode == LayoutMode.GRID
    assert isinstance(layout_manager.get_active_engine(), GridLayoutEngine)

    # Set back to FREE_FORM mode
    controller.set_layout_mode(LayoutMode.FREE_FORM)
    assert layout_manager.ui_selected_layout_mode == LayoutMode.FREE_FORM
    assert model.current_layout_config.mode == LayoutMode.FREE_FORM
    assert isinstance(layout_manager.get_active_engine(), FreeLayoutEngine)
