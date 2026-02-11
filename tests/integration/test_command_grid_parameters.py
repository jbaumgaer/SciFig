"""
Integration tests for the ChangeGridParametersCommand.
"""

from src.models.layout.layout_config import GridConfig, Gutters, Margins
from src.services.commands.change_grid_parameters_command import (
    ChangeGridParametersCommand,
)
from src.shared.constants import LayoutMode


def test_change_grid_parameters_command_execute_undo_redo(
    real_application_model, real_command_manager, real_layout_manager
):
    """
    Test that ChangeGridParametersCommand correctly executes, undoes, and redoes changes
    to the GridConfig in the ApplicationModel via the LayoutManager.
    """
    model = real_application_model
    command_manager = real_command_manager
    layout_manager = real_layout_manager

    # Ensure initial mode is GRID (or set it)
    layout_manager.set_layout_mode(LayoutMode.GRID)
    initial_config: GridConfig = (
        model.current_layout_config
    )  # This is a GridConfig due to set_layout_mode

    # Create a new GridConfig with different parameters
    new_margins = Margins(left=0.2, right=0.2, top=0.2, bottom=0.2)
    new_gutters = Gutters(hspace=[0.1], wspace=[0.1])
    new_config = GridConfig(
        rows=3,
        cols=3,
        row_ratios=[1, 1, 1],
        col_ratios=[1, 1, 1],
        margins=new_margins,
        gutters=new_gutters,
    )

    # 1. Execute Command
    command = ChangeGridParametersCommand(
        model, layout_manager, initial_config, new_config
    )
    command_manager.execute_command(command)

    # Assert model's current_layout_config is the new_config
    assert model.current_layout_config.rows == new_config.rows
    assert model.current_layout_config.cols == new_config.cols
    assert model.current_layout_config.margins == new_config.margins
    assert model.current_layout_config.gutters == new_config.gutters
    assert model.current_layout_config == new_config

    # 2. Undo Command
    command_manager.undo()

    # Assert model's current_layout_config is the initial_config
    assert model.current_layout_config.rows == initial_config.rows
    assert model.current_layout_config.cols == initial_config.cols
    assert model.current_layout_config.margins == initial_config.margins
    assert model.current_layout_config.gutters == initial_config.gutters
    assert model.current_layout_config == initial_config

    # 3. Redo Command
    command_manager.redo()

    # Assert model's current_layout_config is the new_config again
    assert model.current_layout_config.rows == new_config.rows
    assert model.current_layout_config.cols == new_config.cols
    assert model.current_layout_config.margins == new_config.margins
    assert model.current_layout_config.gutters == new_config.gutters
    assert model.current_layout_config == new_config
