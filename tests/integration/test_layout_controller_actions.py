"""
Integration tests for LayoutController's UI-triggered actions.
"""

from src.models.layout.layout_config import (
    GridConfig,
)  # Added for type hinting and assertions
from src.models.nodes.plot_node import PlotNode
from src.services.commands.batch_change_plot_geometry_command import (
    BatchChangePlotGeometryCommand,
)
from src.shared.constants import LayoutMode


def test_full_grid_layout_cycle(
    real_application_model,
    real_command_manager,
    real_layout_manager,
    real_layout_controller,
):
    """
    Integration Test: Full Grid Layout Cycle.
    This test should:
    - Initialize a real ApplicationModel with several PlotNodes.
    - Initialize a real LayoutController, CommandManager, LayoutManager, and GridLayoutEngine.
    - Set a grid layout mode and parameters via LayoutController (e.g., using on_grid_layout_param_changed).
    - Assert that the PlotNodes in the ApplicationModel have their geometries updated correctly
      according to the grid layout calculation.
    - Optionally, test undo/redo of the grid layout change.
    """
    model = real_application_model
    command_manager = real_command_manager
    layout_manager = real_layout_manager
    controller = real_layout_controller

    # Add some plot nodes to the model
    plot1 = PlotNode()
    plot2 = PlotNode()
    model.scene_root.add_child(plot1)
    model.scene_root.add_child(plot2)

    # Initially in Free Form mode as per default config for mock_config_service
    assert model.current_layout_config.mode == LayoutMode.FREE_FORM

    # Switch to GRID mode (this only affects ui_selected_layout_mode, not model.current_layout_config.mode yet)
    controller.set_layout_mode(LayoutMode.GRID)
    assert layout_manager.ui_selected_layout_mode == LayoutMode.GRID
    # Explicitly set the "real" layout mode to GRID for the command manager to operate on a GridConfig
    layout_manager.set_layout_mode(LayoutMode.GRID)

    # Now, after changing grid parameters, the actual layout config in the model should be GRID
    assert model.current_layout_config.mode == LayoutMode.GRID
    assert isinstance(model.current_layout_config, GridConfig)
    initial_grid_config = (
        model.current_layout_config
    )  # This is now a GridConfig instance

    # Set grid parameters via controller. This action *will* trigger a command.
    controller.on_grid_layout_param_changed("rows", 2)
    assert model.current_layout_config.rows == 2  # Debug assertion
    controller.on_grid_layout_param_changed(
        "cols", 3
    )  # Check if grid config updated in model
    assert model.current_layout_config.rows == 2
    assert model.current_layout_config.cols == 3

    # Assert geometries are updated (exact values depend on GridLayoutEngine, check non-zero change)
    # The actual geometry calculation happens within the command's execute method
    # For now, just check they are not default 0,0,0,0 and are different
    assert plot1.geometry != (0.0, 0.0, 0.0, 0.0)
    assert plot2.geometry != (0.0, 0.0, 0.0, 0.0)
    assert plot1.geometry != plot2.geometry  # Should be different positions/sizes

    # Test undo/redo for grid parameter changes
    command_manager.undo()  # Undo the 'cols' change
    assert (
        model.current_layout_config.cols == 1
    )  # cols should be 1 (reverted from 1 to 1)
    assert model.current_layout_config.rows == 2  # rows should still be 2

    command_manager.undo()  # Undo the 'rows' change
    assert (
        model.current_layout_config.rows == initial_grid_config.rows
    )  # rows should revert to initial (1)
    assert (
        model.current_layout_config.cols == initial_grid_config.cols
    )  # cols should still be 1

    command_manager.redo()  # Redo the 'rows' change
    assert model.current_layout_config.rows == 2
    assert model.current_layout_config.cols == 1

    command_manager.redo()  # Redo the 'cols' change
    assert model.current_layout_config.rows == 2
    assert model.current_layout_config.cols == 3


def test_free_form_alignment_undo_redo(
    real_application_model,
    real_command_manager,
    real_layout_manager,
    real_layout_controller,
):
    """
    Integration Test: Free-Form Alignment with Undo/Redo.
    This test should:
    - Initialize a real ApplicationModel with several PlotNodes at arbitrary positions.
    - Select a subset of these PlotNodes.
    - Initialize a real LayoutController, CommandManager, LayoutManager, and FreeLayoutEngine.
    - Perform an alignment action (e.g., align_selected_plots to 'left') via LayoutController.
    - Assert that the selected PlotNodes in the ApplicationModel have their geometries updated correctly.
    - Trigger an undo operation via CommandManager.
    - Assert that the PlotNodes' geometries revert to their original positions.
    - Trigger a redo operation.
    - Assert that the PlotNodes' geometries return to the aligned positions.
    """
    model = real_application_model
    command_manager = real_command_manager
    layout_manager = real_layout_manager
    controller = real_layout_controller

    # Ensure Free-Form mode for manual manipulation
    controller.set_layout_mode(LayoutMode.FREE_FORM)
    assert layout_manager.ui_selected_layout_mode == LayoutMode.FREE_FORM
    # LayoutManager will transition current_layout_config to FreeConfig

    # Add plots with arbitrary initial positions
    plot1 = PlotNode()
    plot1.geometry = (0.1, 0.4, 0.2, 0.2)
    plot2 = PlotNode()
    plot2.geometry = (0.5, 0.1, 0.2, 0.2)
    plot3 = PlotNode()
    plot3.geometry = (0.3, 0.7, 0.2, 0.2)
    model.scene_root.add_child(plot1)
    model.scene_root.add_child(plot2)
    model.scene_root.add_child(plot3)

    # Select plots 1 and 2
    model.set_selection([plot1, plot2])

    initial_plot1_geometry = plot1.geometry
    initial_plot2_geometry = plot2.geometry
    initial_plot3_geometry = plot3.geometry

    # Perform align left
    controller.align_selected_plots("left")

    # Assert new geometries (plot2's x should match plot1's x)
    assert (
        plot1.geometry[0] == initial_plot1_geometry[0]
    )  # plot1 x should not change if it's the leftmost
    assert plot2.geometry[0] == plot1.geometry[0]  # plot2 x should align with plot1
    assert (
        plot3.geometry[0] == initial_plot3_geometry[0]
    )  # plot3 not selected, should not change

    # Undo
    command_manager.undo()
    assert plot1.geometry == initial_plot1_geometry
    assert plot2.geometry == initial_plot2_geometry
    assert plot3.geometry == initial_plot3_geometry

    # Redo
    command_manager.redo()
    assert plot1.geometry[0] == initial_plot1_geometry[0]
    assert plot2.geometry[0] == plot1.geometry[0]
    assert plot3.geometry[0] == initial_plot3_geometry[0]


def test_layout_controller_align_selected_plots_integration(
    real_application_model,
    real_command_manager,
    real_layout_manager,
    real_layout_controller,
    mocker,
):
    """
    Integration Test: LayoutController -> LayoutManager (Align).
    This test should:
    - Initialize real ApplicationModel, CommandManager, LayoutManager, LayoutController.
    - Add multiple PlotNodes to the model and select some.
    - Call LayoutController.align_selected_plots('left').
    - Assert that LayoutManager.perform_align was called with the correct plots and edge.
    - Assert that a BatchChangePlotGeometryCommand was executed by CommandManager.
    """
    model = real_application_model
    command_manager = real_command_manager
    layout_manager = real_layout_manager
    controller = real_layout_controller

    # Ensure Free-Form mode for manual manipulation
    controller.set_layout_mode(LayoutMode.FREE_FORM)

    # Add plots and select them
    plot1 = PlotNode()
    plot1.geometry = (0.1, 0.4, 0.2, 0.2)
    plot2 = PlotNode()
    plot2.geometry = (0.5, 0.1, 0.2, 0.2)
    model.scene_root.add_child(plot1)
    model.scene_root.add_child(plot2)
    model.set_selection([plot1, plot2])

    # Mock perform_align to control its output and verify its call
    # It should return a dict of new geometries
    mock_perform_align = mocker.patch.object(
        layout_manager,
        "perform_align",
        return_value={plot1.id: (0.1, 0.1, 0.2, 0.2), plot2.id: (0.1, 0.5, 0.2, 0.2)},
    )

    # Clear command manager history (Not needed as fixture provides fresh instance)
    # The undo/redo stacks are private, directly accessing them for clear() is not ideal
    # Instead, we assert on their state after the command is executed.

    controller.align_selected_plots("left")

    mock_perform_align.assert_called_once_with([plot1, plot2], "left")
    assert len(command_manager._undo_stack) == 1  # Check that a command was added
    assert isinstance(command_manager._undo_stack[0], BatchChangePlotGeometryCommand)


def test_layout_controller_distribute_selected_plots_integration(
    real_application_model,
    real_command_manager,
    real_layout_manager,
    real_layout_controller,
    mocker,
):
    """
    Integration Test: LayoutController -> LayoutManager (Distribute).
    This test should:
    - Initialize real ApplicationModel, CommandManager, LayoutManager, LayoutController.
    - Add multiple PlotNodes to the model and select some.
    - Call LayoutController.distribute_selected_plots('horizontal').
    - Assert that LayoutManager.perform_distribute was called with the correct plots and axis.
    - Assert that a BatchChangePlotGeometryCommand was executed by CommandManager.
    """
    model = real_application_model
    command_manager = real_command_manager
    layout_manager = real_layout_manager
    controller = real_layout_controller

    # Ensure Free-Form mode for manual manipulation
    controller.set_layout_mode(LayoutMode.FREE_FORM)

    # Add plots and select them
    plot1 = PlotNode()
    plot1.geometry = (0.1, 0.1, 0.1, 0.1)
    plot2 = PlotNode()
    plot2.geometry = (0.4, 0.4, 0.1, 0.1)
    plot3 = PlotNode()
    plot3.geometry = (0.8, 0.8, 0.1, 0.1)
    model.scene_root.add_child(plot1)
    model.scene_root.add_child(plot2)
    model.scene_root.add_child(plot3)
    model.set_selection([plot1, plot2, plot3])

    # Mock perform_distribute to control its output and verify its call
    # It should return a dict of new geometries
    mock_perform_distribute = mocker.patch.object(
        layout_manager,
        "perform_distribute",
        return_value={
            plot1.id: (0.1, 0.1, 0.1, 0.1),
            plot2.id: (0.45, 0.4, 0.1, 0.1),  # Assuming some distribution logic
            plot3.id: (0.8, 0.8, 0.1, 0.1),
        },
    )

    # Clear command manager history (Not needed as fixture provides fresh instance)
    # The undo/redo stacks are private, directly accessing them for clear() is not ideal
    # Instead, we assert on their state after the command is executed.

    controller.distribute_selected_plots("horizontal")

    mock_perform_distribute.assert_called_once_with([plot1, plot2, plot3], "horizontal")
    assert len(command_manager._undo_stack) == 1  # Check that a command was added
    assert isinstance(command_manager._undo_stack[0], BatchChangePlotGeometryCommand)
