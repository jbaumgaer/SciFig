import pytest
from unittest.mock import MagicMock, ANY
from pathlib import Path

from src.controllers.layout_controller import LayoutController
from src.models.layout.layout_config import GridConfig, Margins, Gutters
from src.models.nodes.plot_node import PlotNode
from src.services.commands.batch_change_plot_geometry_command import BatchChangePlotGeometryCommand
from src.services.commands.change_grid_parameters_command import ChangeGridParametersCommand
from src.services.commands.apply_grid_command import ApplyGridCommand
from src.services.commands.change_grid_property_command import ChangeGridPropertyCommand
from src.models.nodes.grid_node import GridNode
from src.shared.constants import LayoutMode
from src.shared.events import Events
from src.shared.geometry import Rect


@pytest.fixture
def mock_property_service():
    return MagicMock()

@pytest.fixture
def layout_controller(
    mock_application_model, mock_command_manager, mock_layout_manager, mock_event_aggregator, mock_property_service
):
    """Provides a LayoutController instance with all dependencies mocked."""
    return LayoutController(
        mock_application_model, mock_command_manager, mock_layout_manager, mock_event_aggregator, mock_property_service
    )


class TestLayoutController:

    def test_initialization_subscribes_to_events(self, mock_event_aggregator):
        """Verifies that the controller subscribes to all relevant request events."""
        local_event_mock = MagicMock()
        LayoutController(MagicMock(), MagicMock(), MagicMock(), local_event_mock, MagicMock())
        
        expected_events = [
            Events.ALIGN_PLOTS_REQUESTED,
            Events.DISTRIBUTE_PLOTS_REQUESTED,
            Events.INFER_GRID_PARAMETERS_REQUESTED,
            Events.APPLY_GRID_REQUESTED, # Added in TDD-5
            Events.OPTIMIZE_LAYOUT_REQUESTED,
            Events.CHANGE_GRID_PARAMETER_REQUESTED,
            Events.BATCH_CHANGE_PLOT_GEOMETRY_REQUESTED
        ]
        
        for event in expected_events:
            local_event_mock.subscribe.assert_any_call(event, ANY)

    def test_handle_apply_grid_request(self, layout_controller, mock_command_manager, mock_layout_manager):
        """Verifies that APPLY_GRID_REQUESTED executes an ApplyGridCommand."""
        config = GridConfig(2, 2, [1,1], [1,1], Margins(1,1,1,1), Gutters([0.5], [0.5]))
        
        layout_controller._handle_apply_grid_request(config)
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, ApplyGridCommand)
        assert command._new_config == config

    def test_set_layout_mode(self, layout_controller, mock_layout_manager):
        """Test setting the UI selected layout mode."""
        layout_controller.set_layout_mode(LayoutMode.GRID)
        assert mock_layout_manager.ui_selected_layout_mode == LayoutMode.GRID

    def test_handle_align_plots_request(self, layout_controller, mock_application_model, 
                                       mock_layout_manager, mock_command_manager):
        """Verifies that alignment requests are translated into BatchChangePlotGeometryCommands."""
        plot = PlotNode(id="p1")
        mock_application_model.selection = [plot]
        mock_layout_manager.perform_align.return_value = {"p1": Rect(0,0,5,5)}
        
        layout_controller._handle_align_plots_request("left")
        
        mock_layout_manager.perform_align.assert_called_once_with([plot], "left")
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, BatchChangePlotGeometryCommand)

    @pytest.mark.parametrize("param, value, expected_path, expected_val", [
        ("rows", 5, "rows", 5),
        ("cols", 3, "cols", 3),
        ("margin_top", 2.0, "margins.top", 2.0),
        ("hspace", "1.5, 2.0", "gutters.hspace", [1.5, 2.0]),
    ])
    def test_handle_change_grid_parameter_valid(self, layout_controller, mock_application_model, 
                                               mock_command_manager, param, value, expected_path, expected_val):
        """Tests valid grid parameter updates via ChangeGridPropertyCommand."""
        mock_grid = MagicMock(spec=GridNode)
        mock_application_model.get_active_grid.return_value = mock_grid
        
        layout_controller._handle_change_grid_parameter_request(param, value)
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, ChangeGridPropertyCommand)
        assert command.grid_node == mock_grid
        assert command.path == expected_path
        assert command.new_value == expected_val

    def test_handle_change_grid_parameter_no_active_grid(self, layout_controller, mock_application_model, mock_command_manager):
        """Ensures no command is executed if no active grid is found."""
        mock_application_model.get_active_grid.return_value = None
        layout_controller._handle_change_grid_parameter_request("rows", 5)
        mock_command_manager.execute_command.assert_not_called()

    def test_handle_align_no_plots_selected(self, layout_controller, mock_application_model, 
                                           mock_command_manager):
        """Ensures no command is executed if no plots are selected."""
        mock_application_model.selection = []
        layout_controller._handle_align_plots_request("left")
        mock_command_manager.execute_command.assert_not_called()

    def test_handle_optimize_layout_request(self, layout_controller, mock_layout_manager, mock_command_manager):
        """Verifies that optimization requests dispatch ChangeGridParametersCommand."""
        old_config = GridConfig(1, 1, [1.0], [1.0], Margins(1,1,1,1), Gutters([], []))
        new_config = GridConfig(1, 1, [1.0], [1.0], Margins(1.5, 1.5, 1.5, 1.5), Gutters([], []))
        
        mock_layout_manager.get_last_grid_config.return_value = old_config
        mock_layout_manager.get_optimized_grid_config.return_value = new_config
        
        layout_controller._handle_optimize_layout_request()
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, ChangeGridParametersCommand)
        assert command.new_grid_config == new_config

    def test_handle_change_grid_parameter_malformed_string(self, layout_controller, mock_application_model, mock_command_manager):
        """Ensures malformed hspace strings don't crash the controller."""
        mock_application_model.get_active_grid.return_value = MagicMock(spec=GridNode)
        
        layout_controller._handle_change_grid_parameter_request("hspace", "0.1, oops, 0.2")
        # Should log warning and not execute command
        mock_command_manager.execute_command.assert_not_called()
