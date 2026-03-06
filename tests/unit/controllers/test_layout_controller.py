import pytest
from unittest.mock import MagicMock, ANY

from src.controllers.layout_controller import LayoutController
from src.models.layout.layout_config import GridConfig, Margins, Gutters
from src.models.nodes.plot_node import PlotNode
from src.services.commands.batch_change_plot_geometry_command import BatchChangePlotGeometryCommand
from src.services.commands.change_grid_parameters_command import ChangeGridParametersCommand
from src.shared.constants import LayoutMode
from src.shared.events import Events


@pytest.fixture
def layout_controller(
    mock_application_model, mock_command_manager, mock_layout_manager, mock_event_aggregator
):
    """Provides a LayoutController instance with all dependencies mocked."""
    return LayoutController(
        mock_application_model, mock_command_manager, mock_layout_manager, mock_event_aggregator
    )


class TestLayoutController:

    def test_initialization_subscribes_to_events(self, mock_event_aggregator):
        """Verifies that the controller subscribes to all relevant request events."""
        # Use a fresh mock to verify subscriptions in __init__
        local_event_mock = MagicMock()
        LayoutController(MagicMock(), MagicMock(), MagicMock(), local_event_mock)
        
        expected_events = [
            Events.ALIGN_PLOTS_REQUESTED,
            Events.DISTRIBUTE_PLOTS_REQUESTED,
            Events.INFER_GRID_PARAMETERS_REQUESTED,
            Events.OPTIMIZE_LAYOUT_REQUESTED,
            Events.CHANGE_GRID_PARAMETER_REQUESTED
        ]
        
        for event in expected_events:
            local_event_mock.subscribe.assert_any_call(event, ANY)

    def test_set_layout_mode(self, layout_controller, mock_layout_manager):
        """Test setting the UI selected layout mode."""
        layout_controller.set_layout_mode(LayoutMode.GRID)
        assert mock_layout_manager.ui_selected_layout_mode == LayoutMode.GRID

    def test_toggle_layout_mode(self, layout_controller, mock_layout_manager):
        """Tests the toggle logic used by UI actions."""
        layout_controller.toggle_layout_mode(True)
        assert mock_layout_manager.ui_selected_layout_mode == LayoutMode.GRID
        
        layout_controller.toggle_layout_mode(False)
        assert mock_layout_manager.ui_selected_layout_mode == LayoutMode.FREE_FORM

    # --- Event Handler Tests (Logic Delegation) ---

    def test_handle_align_plots_request(self, layout_controller, mock_application_model, 
                                       mock_layout_manager, mock_command_manager):
        """Verifies that alignment requests are translated into BatchChangePlotGeometryCommands."""
        # Setup: 1 PlotNode and 1 non-PlotNode selected
        plot = PlotNode(id="p1")
        mock_application_model.selection = [plot, MagicMock()]
        
        mock_layout_manager.perform_align.return_value = {"p1": (0,0,0.5,0.5)}
        
        # Trigger
        layout_controller._handle_align_plots_request("left")
        
        # Verify
        mock_layout_manager.perform_align.assert_called_once_with([plot], "left")
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, BatchChangePlotGeometryCommand)

    def test_handle_align_no_plots_selected(self, layout_controller, mock_application_model, 
                                           mock_layout_manager, mock_command_manager):
        """Ensures no command is executed if no plots are selected."""
        mock_application_model.selection = []
        layout_controller._handle_align_plots_request("left")
        mock_command_manager.execute_command.assert_not_called()

    def test_handle_optimize_layout_request(self, layout_controller, mock_layout_manager, mock_command_manager):
        """Verifies that optimization requests dispatch ChangeGridParametersCommand."""
        old_config = GridConfig(1, 1, [1.0], [1.0], Margins(0,0,0,0), Gutters([], []))
        new_config = GridConfig(1, 1, [1.0], [1.0], Margins(0.1, 0.1, 0.1, 0.1), Gutters([], []))
        
        mock_layout_manager.get_last_grid_config.return_value = old_config
        mock_layout_manager.get_optimized_grid_config.return_value = new_config
        
        layout_controller._handle_optimize_layout_request()
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, ChangeGridParametersCommand)
        assert command.new_grid_config == new_config

    # --- Parameter Change Logic ---

    @pytest.mark.parametrize("param, value, expected_attr, expected_val", [
        ("rows", 5, "rows", 5),
        ("cols", 3, "cols", 3),
        ("margin_top", 0.2, "margins.top", 0.2),
        ("hspace", "0.1, 0.2", "gutters.hspace", [0.1, 0.2]),
    ])
    def test_handle_change_grid_parameter_valid(self, layout_controller, mock_layout_manager, 
                                               mock_command_manager, param, value, expected_attr, expected_val):
        """Tests valid grid parameter updates and merging."""
        base = GridConfig(1, 1, [1.0], [1.0], Margins(0.05, 0.05, 0.05, 0.05), Gutters([0.01], [0.01]))
        mock_layout_manager.get_last_grid_config.return_value = base
        
        layout_controller._handle_change_grid_parameter_request(param, value)
        
        mock_command_manager.execute_command.assert_called_once()
        new_config = mock_command_manager.execute_command.call_args[0][0].new_grid_config
        
        # Verification helper for nested attrs
        if "." in expected_attr:
            obj_name, attr_name = expected_attr.split(".")
            assert getattr(getattr(new_config, obj_name), attr_name) == expected_val
        else:
            assert getattr(new_config, expected_attr) == expected_val

    def test_handle_change_grid_parameter_invalid_bounds(self, layout_controller, mock_layout_manager, mock_command_manager):
        """Verifies that invalid values (e.g. negative rows) are rejected."""
        base = GridConfig(1, 1, [1.0], [1.0], Margins(0,0,0,0), Gutters([], []))
        mock_layout_manager.get_last_grid_config.return_value = base
        
        # Boundary: Margin > 0.5 is currently rejected in source
        layout_controller._handle_change_grid_parameter_request("margin_top", 0.6)
        mock_command_manager.execute_command.assert_not_called()
        
        # Boundary: Rows <= 0
        layout_controller._handle_change_grid_parameter_request("rows", 0)
        mock_command_manager.execute_command.assert_not_called()

    def test_handle_change_grid_parameter_malformed_string(self, layout_controller, mock_layout_manager, mock_command_manager):
        """Ensures malformed hspace strings don't crash the controller."""
        base = GridConfig(1, 1, [1.0], [1.0], Margins(0,0,0,0), Gutters([], []))
        mock_layout_manager.get_last_grid_config.return_value = base
        
        layout_controller._handle_change_grid_parameter_request("hspace", "0.1, oops, 0.2")
        # Should log warning and not execute command (or execute with old value)
        mock_command_manager.execute_command.assert_not_called()
