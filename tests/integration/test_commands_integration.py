"""
Integration tests for Command Execution & State Management.
These tests focus on the interaction between CommandManager, various Commands,
and the ApplicationModel, ensuring that state changes are correctly applied
and can be undone/redone.
"""
import pytest
from unittest.mock import MagicMock

# Assuming these imports will be available or mocked as needed for real command instances
import matplotlib.figure
from src.models.layout.free_layout_engine import FreeLayoutEngine
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.services.config_service import ConfigService
from src.models.application_model import ApplicationModel
from src.services.commands.command_manager import CommandManager
from src.services.commands.change_property_command import ChangePropertyCommand
from src.services.commands.batch_change_plot_geometry_command import BatchChangePlotGeometryCommand
from src.services.commands.change_grid_parameters_command import ChangeGridParametersCommand
from src.models.nodes.plot_node import PlotNode
from src.models.layout.layout_config import GridConfig, Margins, Gutters, NO_MARGINS, NO_GUTTERS
from src.services.layout_manager import LayoutManager
from src.shared.constants import LayoutMode
from src.models.plots.plot_properties import LinePlotProperties, ScatterPlotProperties, BasePlotProperties
from src.models.plots.plot_types import PlotType


@pytest.fixture
def real_command_manager(real_application_model_with_plot):
    """Provides a real CommandManager instance."""
    return CommandManager(real_application_model_with_plot)

@pytest.fixture
def mock_figure():
    """Provides a mock matplotlib.figure.Figure instance."""
    return MagicMock(spec=matplotlib.figure.Figure)

@pytest.fixture
def mock_config_service():
    """Provides a mock ConfigService instance."""
    mock_service = MagicMock(spec=ConfigService)
    mock_service.get.return_value = 'free_form' # Default layout mode
    return mock_service

@pytest.fixture
def real_application_model_with_plot(mock_figure, mock_config_service):
    """Provides a real ApplicationModel with a pre-configured PlotNode."""
    model = ApplicationModel(figure=mock_figure, config_service=mock_config_service)
    plot_node = PlotNode()
    plot_node.plot_properties = LinePlotProperties() # Initialize plot_properties
    plot_node.plot_properties.title = "Initial Title"
    model.scene_root.add_child(plot_node)
    model.selection.append(plot_node) # Ensure it's selectable for some tests
    return model

@pytest.fixture
def real_layout_manager_for_commands(real_application_model_with_plot, mock_config_service):
    """Provides a real LayoutManager instance, ensuring _last_grid_config is set for testing."""
    grid_engine_mock = MagicMock(spec=GridLayoutEngine)
    grid_engine_mock.calculate_geometries.return_value = ({}, NO_MARGINS, NO_GUTTERS)
    layout_manager = LayoutManager(
        real_application_model_with_plot,
        MagicMock(spec=FreeLayoutEngine), # FreeLayoutEngine mock
        grid_engine_mock, # GridLayoutEngine mock
        mock_config_service
    )
    # Manually set an initial grid config as the command relies on _last_grid_config
    layout_manager._last_grid_config = GridConfig(rows=1, cols=1, row_ratios=[1], col_ratios=[1], margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1), gutters=Gutters(hspace=[0.05], wspace=[0.05]))
    return layout_manager

class TestCommandsIntegration:

    def test_change_property_command_execute_undo(self, real_application_model_with_plot, real_command_manager):
        """
        Integration Test: ChangePropertyCommand - Execute and Undo.
        This test should:
        - Initialize real ApplicationModel, CommandManager, and a PlotNode.
        - Create a ChangePropertyCommand to change the PlotNode's title.
        - Execute the command via CommandManager.
        - Assert that the PlotNode's title in ApplicationModel is updated correctly.
        - Call CommandManager.undo().
        - Assert that the PlotNode's title reverts to its original value in ApplicationModel.
        - Test for other properties like x_label, y_label, color, etc.
        """
        model = real_application_model_with_plot
        command_manager = real_command_manager
        plot_node = model.scene_root.children[0] # Get the pre-configured plot node

        old_title = plot_node.plot_properties.title
        new_title = "New Plot Title"

        command = ChangePropertyCommand(
            node=plot_node,
            property_name="title",
            new_value=new_title,
            property_dict_name="plot_properties",
        )

        # Execute
        command_manager.execute_command(command)
        assert plot_node.plot_properties.title == new_title

        # Undo
        command_manager.undo()
        assert plot_node.plot_properties.title == old_title

        # Redo to ensure redo works after undo
        command_manager.redo()
        assert plot_node.plot_properties.title == new_title

        # Test another property: x_label
        old_xlabel = plot_node.plot_properties.xlabel
        new_xlabel = "New X-Axis"
        command_xlabel = ChangePropertyCommand(
            node=plot_node,
            property_name="xlabel",
            new_value=new_xlabel,
            property_dict_name="plot_properties",
        )
        command_manager.execute_command(command_xlabel)
        assert plot_node.plot_properties.xlabel == new_xlabel
        command_manager.undo()
        assert plot_node.plot_properties.xlabel == old_xlabel


    def test_change_property_command_plot_type_transform(self, real_application_model_with_plot, real_command_manager):
        """
        Integration Test: ChangePropertyCommand - Plot Type Transformation.
        This test should:
        - Initialize real ApplicationModel, CommandManager, and a PlotNode with a default LinePlotProperties.
        - Create a ChangePropertyCommand to change the 'plot_type' to 'scatter'.
        - Execute the command.
        - Assert that the PlotNode's plot_properties in ApplicationModel is now an instance of ScatterPlotProperties.
        - Call CommandManager.undo().
        - Assert that the PlotNode's plot_properties reverts to a LinePlotProperties.
        """
        model = real_application_model_with_plot
        command_manager = real_command_manager
        plot_node = model.scene_root.children[0]

        # Ensure initial plot_properties is LinePlotProperties
        plot_node.plot_properties = LinePlotProperties()
        assert isinstance(plot_node.plot_properties, LinePlotProperties)

        old_plot_type = plot_node.plot_properties.plot_type
        new_plot_type = PlotType.SCATTER

        command = ChangePropertyCommand(
            node=plot_node,
            property_name="plot_type",
            new_value=new_plot_type,
            property_dict_name="plot_properties",
        )

        # Execute
        command_manager.execute_command(command)
        assert isinstance(plot_node.plot_properties, ScatterPlotProperties)
        assert plot_node.plot_properties.plot_type == new_plot_type

        # Undo
        command_manager.undo()
        assert isinstance(plot_node.plot_properties, LinePlotProperties)
        assert plot_node.plot_properties.plot_type == old_plot_type

        # Redo
        command_manager.redo()
        assert isinstance(plot_node.plot_properties, ScatterPlotProperties)
        assert plot_node.plot_properties.plot_type == new_plot_type

    @pytest.fixture
    def real_application_model_with_multiple_plots(mock_figure, mock_config_service):
        """Provides a real ApplicationModel with multiple pre-configured PlotNodes."""
        model = ApplicationModel(figure=mock_figure, config_service=mock_config_service)
        plot1 = PlotNode()
        plot1.plot_properties = LinePlotProperties() # Initialize plot_properties
        plot1.geometry = (0.1, 0.1, 0.3, 0.3)
        plot2 = PlotNode()
        plot2.plot_properties = LinePlotProperties() # Initialize plot_properties
        plot2.geometry = (0.5, 0.5, 0.2, 0.2)
        model.scene_root.add_child(plot1)
        model.scene_root.add_child(plot2)
        return model

    def test_batch_change_plot_geometry_command_execute_undo(self, real_application_model_with_multiple_plots, real_command_manager):
        """
        Integration Test: BatchChangePlotGeometryCommand - Execute and Undo.
        This test should:
        - Initialize real ApplicationModel, CommandManager, and several PlotNodes with initial geometries.
        - Create a dictionary of new geometries for these PlotNodes.
        - Create a BatchChangePlotGeometryCommand.
        - Execute the command via CommandManager.
        - Assert that all PlotNodes in ApplicationModel have their geometries updated correctly.
        - Call CommandManager.undo().
        - Assert that all PlotNodes revert to their original geometries in ApplicationModel.
        """
        model = real_application_model_with_multiple_plots
        command_manager = real_command_manager
        plot1 = model.scene_root.children[0]
        plot2 = model.scene_root.children[1]

        initial_geometries = {
            plot1.id: plot1.geometry,
            plot2.id: plot2.geometry
        }

        new_geometries = {
            plot1.id: (0.0, 0.0, 0.5, 0.5),
            plot2.id: (0.6, 0.6, 0.3, 0.3)
        }

        command = BatchChangePlotGeometryCommand(
            model=model,
            new_geometries=new_geometries,
            description="Batch Change Plot Geometries"
        )

        # Execute
        command_manager.execute_command(command)
        assert plot1.geometry == new_geometries[plot1.id]
        assert plot2.geometry == new_geometries[plot2.id]

        # Undo
        command_manager.undo()
        assert plot1.geometry == initial_geometries[plot1.id]
        assert plot2.geometry == initial_geometries[plot2.id]

        # Redo
        command_manager.redo()
        assert plot1.geometry == new_geometries[plot1.id]
        assert plot2.geometry == new_geometries[plot2.id]

    def test_change_grid_parameters_command_execute_undo(self, real_application_model_with_plot, real_command_manager, real_layout_manager_for_commands):
        """
        Integration Test: ChangeGridParametersCommand - Execute and Undo.
        This test should:
        - Initialize real ApplicationModel, CommandManager, and LayoutManager.
        - Set an initial GridConfig in ApplicationModel (or LayoutManager).
        - Create a ChangeGridParametersCommand with a new GridConfig.
        - Execute the command via CommandManager.
        - Assert that ApplicationModel.current_layout_config is updated to the new GridConfig.
        - Call CommandManager.undo().
        - Assert that ApplicationModel.current_layout_config reverts to the old GridConfig.
        """
        model = real_application_model_with_plot
        command_manager = real_command_manager
        layout_manager = real_layout_manager_for_commands

        old_config = layout_manager._last_grid_config
        new_config = GridConfig(rows=2, cols=2, row_ratios=[1, 1], col_ratios=[1, 1], margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1), gutters=Gutters(hspace=[0.05], wspace=[0.05]))

        command = ChangeGridParametersCommand(
            model=model,
            layout_manager=layout_manager,
            old_grid_config=old_config,
            new_grid_config=new_config
        )

        # Execute
        command_manager.execute_command(command)
        assert model.current_layout_config == new_config
        assert layout_manager._last_grid_config == new_config

        # Undo
        command_manager.undo()
        assert model.current_layout_config == old_config
        assert layout_manager._last_grid_config == old_config

        # Redo
        command_manager.redo()
        assert model.current_layout_config == new_config
        assert layout_manager._last_grid_config == new_config

    def test_command_manager_undo_redo_stack(self, real_application_model_with_plot, real_command_manager):
        """
        Integration Test: CommandManager - Undo/Redo Stack Functionality.
        This test should:
        - Initialize real ApplicationModel and CommandManager.
        - Execute a sequence of multiple different commands (e.g., ChangeProperty, BatchChangePlotGeometry).
        - Call CommandManager.undo() multiple times, asserting the model state is correct after each undo.
        - Call CommandManager.redo() multiple times, asserting the model state is correct after each redo.
        - Verify edge cases for undo/redo (e.g., undo when stack is empty, redo when stack is empty).
        """
        model = real_application_model_with_plot
        command_manager = real_command_manager
        plot_node = model.scene_root.children[0]

        # Initial state
        initial_title = plot_node.plot_properties.title
        initial_x_geometry = plot_node.geometry[0]
        
        # Command 1: Change title
        cmd1 = ChangePropertyCommand(node=plot_node, property_name="title", new_value="Title 1", property_dict_name="plot_properties")
        command_manager.execute_command(cmd1)
        assert plot_node.plot_properties.title == "Title 1"
        assert len(command_manager._undo_stack) > 0 and not (len(command_manager._redo_stack) > 0)

        # Command 2: Change x position
        cmd2_new_x = initial_x_geometry + 0.1
        cmd2_geometries = {plot_node.id: (cmd2_new_x, plot_node.geometry[1], plot_node.geometry[2], plot_node.geometry[3])}
        cmd2 = BatchChangePlotGeometryCommand(model=model, new_geometries=cmd2_geometries, description="Move Plot 1")
        command_manager.execute_command(cmd2)
        assert plot_node.geometry[0] == cmd2_new_x
        assert len(command_manager._undo_stack) > 0 and not (len(command_manager._redo_stack) > 0)

        # Undo 1: Revert plot position
        command_manager.undo()
        assert plot_node.geometry[0] == initial_x_geometry
        assert len(command_manager._undo_stack) > 0 and len(command_manager._redo_stack) > 0

        # Undo 2: Revert title
        command_manager.undo()
        assert plot_node.plot_properties.title == initial_title
        assert not (len(command_manager._undo_stack) > 0) and (len(command_manager._redo_stack) > 0)

        # Attempt to undo when stack is empty
        command_manager.undo() # Should do nothing
        assert plot_node.plot_properties.title == initial_title
        assert not (len(command_manager._undo_stack) > 0) and (len(command_manager._redo_stack) > 0)

        # Redo 1: Reapply title
        command_manager.redo()
        assert plot_node.plot_properties.title == "Title 1"
        assert len(command_manager._undo_stack) > 0 and len(command_manager._redo_stack) > 0

        # Redo 2: Reapply plot position
        command_manager.redo()
        assert plot_node.geometry[0] == cmd2_new_x
        assert len(command_manager._undo_stack) > 0 and not (len(command_manager._redo_stack) > 0)

        # Attempt to redo when stack is empty
        command_manager.redo() # Should do nothing
        assert plot_node.geometry[0] == cmd2_new_x
        assert len(command_manager._undo_stack) > 0 and not (len(command_manager._redo_stack) > 0)

        # Execute new command after undo, should clear redo stack
        cmd3 = ChangePropertyCommand(node=plot_node, property_name="title", new_value="New Title 3", property_dict_name="plot_properties")
        command_manager.execute_command(cmd3)
        assert plot_node.plot_properties.title == "New Title 3"
        assert len(command_manager._undo_stack) > 0 and not (len(command_manager._redo_stack) > 0)