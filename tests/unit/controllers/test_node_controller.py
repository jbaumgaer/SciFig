import pytest
from unittest.mock import MagicMock, ANY, create_autospec
from pathlib import Path
import pandas as pd
import logging

from src.controllers.node_controller import NodeController
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.group_node import GroupNode
from src.models.plots.plot_properties import PlotProperties
from src.models.plots.plot_types import ArtistType
from src.services.commands.apply_data_to_node_command import ApplyDataToNodeCommand
from src.services.commands.add_plot_command import AddPlotCommand
from src.services.commands.change_plot_property_command import ChangePlotPropertyCommand
from src.services.commands.delete_node_command import DeleteNodeCommand
from src.services.commands.macro_command import MacroCommand
from src.shared.events import Events


@pytest.fixture
def node_controller(
    mock_application_model, mock_command_manager, mock_event_aggregator, mock_property_service
):
    """Provides a NodeController instance with all dependencies mocked."""
    mock_application_model.scene_root.id = "root_id"
    return NodeController(
        model=mock_application_model,
        command_manager=mock_command_manager,
        event_aggregator=mock_event_aggregator,
        property_service=mock_property_service,
    )


class TestNodeController:

    # --- Initialization & Event Binding ---

    def test_initialization_subscribes_to_events(self, mock_event_aggregator):
        """Verifies that the controller hooks into all required application events."""
        local_event_mock = MagicMock()
        NodeController(MagicMock(), MagicMock(), local_event_mock, MagicMock())
        
        expected_events = [
            Events.SUBPLOT_SELECTION_IN_UI_CHANGED,
            Events.SELECT_DATA_FILE_FOR_NODE_REQUESTED,
            Events.PATH_PROVIDED_FOR_NODE_DATA_OPEN,
            Events.APPLY_DATA_TO_NODE_REQUESTED,
            Events.NODE_DATA_LOADED,
            Events.CHANGE_PLOT_TYPE_REQUESTED,
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            Events.CHANGE_NODE_VISIBILITY_REQUESTED,
            Events.RENAME_NODE_REQUESTED,
            Events.CHANGE_NODE_LOCKED_REQUESTED,
            Events.TEMPLATE_LOADED,
            Events.SELECTION_CHANGED,
            Events.PLOT_COMPONENT_RECONCILIATION_REQUESTED,
            Events.DELETE_NODES_REQUESTED,
            Events.ADD_PLOT_REQUESTED
        ]
        
        for event in expected_events:
            local_event_mock.subscribe.assert_any_call(event, ANY)

    # --- Bypass Pattern (Reconciliation) ---

    def test_reconcile_node_property_updates_model_silently(
        self, node_controller, mock_application_model, mock_property_service, mock_event_aggregator
    ):
        """Tests the Bypass Pattern: direct property updates with version bumping."""
        node = PlotNode(id="p1")
        node.plot_properties = MagicMock()
        node.plot_properties._version = 10
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        # Trigger reconciliation
        node_controller.reconcile_node_property("p1", "coords.xaxis.margin", 0.1)
        
        # Verify direct update via PropertyService
        mock_property_service.set_value.assert_called_once_with(node.plot_properties, "coords.xaxis.margin", 0.1)
        # Verify version bump
        assert node.plot_properties._version == 11
        # Verify reconciled event (not changed event)
        mock_event_aggregator.publish.assert_called_once_with(
            Events.PLOT_COMPONENT_RECONCILED, node_id="p1", path="coords.xaxis.margin", new_value=0.1
        )

    # --- Data Integration Logic ---

    def test_on_data_loaded_orchestrates_theming_and_mapping(
        self, node_controller, mock_application_model, mock_event_aggregator, mock_command_manager
    ):
        """Tests the complex logic when data is loaded into an empty plot node."""
        node = PlotNode(id="p1")
        node.plot_properties = None # Start uninitialized
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        df = pd.DataFrame({"X_Col": [1, 2], "Y_Col": [3, 4]})
        file_path = Path("test.csv")
        
        # Trigger
        node_controller._on_data_loaded("p1", df, file_path)
        
        # 1. Verify theme initialization request (since props were None)
        mock_event_aggregator.publish.assert_any_call(
            Events.INITIALIZE_PLOT_THEME_REQUESTED, node_id="p1", plot_type=ArtistType.LINE
        )
        
        # 2. Verify macro-command dispatch
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, ApplyDataToNodeCommand)

    def test_on_data_loaded_with_existing_props_triggers_heuristic(
        self, node_controller, mock_application_model, mock_command_manager
    ):
        """Tests that heuristic column mapping is applied if props exist."""
        node = PlotNode(id="p1")
        node.plot_properties = MagicMock()
        node.plot_properties.artists = [MagicMock()]
        node.plot_properties.coords.coord_type = ArtistType.LINE
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        df = pd.DataFrame({"A": [1], "B": [2]})
        node_controller._on_data_loaded("p1", df, Path("test.csv"))
        
        mock_command_manager.execute_command.assert_called_once()
        macro = mock_command_manager.execute_command.call_args[0][0]
        # Verify that column mapping commands were included in the macro
        paths = [c.path for c in macro.commands]
        assert "artists.0.x_column" in paths
        assert "artists.0.y_column" in paths

    # --- UI & Selection Logic ---

    def test_on_selection_changed_for_ui_requests_tab_switch(self, node_controller, 
                                                           mock_application_model, mock_event_aggregator):
        """Verifies that single PlotNode selection triggers a switch to properties tab."""
        node = PlotNode(id="p1")
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        node_controller._on_selection_changed_for_ui(["p1"])
        
        mock_event_aggregator.publish.assert_called_once_with(
            Events.SWITCH_SIDEPANEL_TAB, tab_key="properties"
        )

    # --- Template Hydration ---

    def test_on_template_loaded_triggers_hydration_for_sparse_nodes(self, node_controller, mock_event_aggregator):
        """Tests that sparse nodes in a template are identified for hydration."""
        root = GroupNode(name="Template")
        sparse_node = PlotNode(id="p1")
        sparse_node.plot_properties = {"some": "template_data"} # sparse dict
        root.add_child(sparse_node)
        
        node_controller._on_template_loaded(root)
        
        # Verify hydration request for sparse node only
        mock_event_aggregator.publish.assert_called_once_with(
            Events.HYDRATE_PLOT_PROPERTIES_REQUESTED, node_id="p1", overrides={"some": "template_data"}
        )

    # --- Property Requests (Command Dispatch) ---

    def test_node_visibility_request(self, node_controller, mock_application_model, mock_command_manager):
        """Verifies visibility requests are wrapped in commands."""
        node = PlotNode(id="p1")
        node.visible = True
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        node_controller._on_node_visibility_request("p1", False)
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, ChangePlotPropertyCommand)
        assert command.path == "visible"
        assert command.new_value is False

    def test_node_locked_request(self, node_controller, mock_application_model, mock_command_manager):
        """Verifies locked requests are wrapped in commands."""
        node = PlotNode(id="p1")
        node.locked = False
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        node_controller._on_node_locked_request("p1", True)
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert command.path == "locked"
        assert command.new_value is True

    def test_rename_node_request(self, node_controller, mock_application_model, mock_command_manager):
        """Verifies rename requests are wrapped in commands."""
        node = PlotNode(id="p1", name="Old")
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        node_controller._on_rename_node_request("p1", "NewName")
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert command.path == "name"
        assert command.new_value == "NewName"

    # --- Edge Cases & Robustness ---

    def test_reconcile_node_property_root_resolution(
        self, node_controller, mock_application_model, mock_property_service
    ):
        """Verifies that reconciliation correctly identifies if the root is the node or properties."""
        node = PlotNode(id="p1", name="Plot")
        # Use a spec to ensure hasattr(node.plot_properties, "name") returns False
        node.plot_properties = create_autospec(PlotProperties, instance=True)
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        # 1. Target Node directly (e.g. name)
        node_controller.reconcile_node_property("p1", "name", "NewName")
        mock_property_service.set_value.assert_called_with(node, "name", "NewName")
        
        # 2. Target Properties via "artists"
        node_controller.reconcile_node_property("p1", "artists.0.color", "red")
        mock_property_service.set_value.assert_called_with(node.plot_properties, "artists.0.color", "red")

    def test_idempotent_property_requests_do_not_dispatch_commands(
        self, node_controller, mock_application_model, mock_command_manager
    ):
        """Ensures that requesting a change to the current value is a no-op."""
        node = PlotNode(id="p1", name="SameName")
        node.visible = True
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        # Request same name
        node_controller._on_rename_node_request("p1", "SameName")
        # Request same visibility
        node_controller._on_node_visibility_request("p1", True)
        
        mock_command_manager.execute_command.assert_not_called()

    def test_on_data_loaded_resets_polar_limits(
        self, node_controller, mock_application_model, mock_command_manager
    ):
        """Verifies that for Polar plots, theta and r limits are reset instead of x/y."""
        node = PlotNode(id="p1")
        node.plot_properties = MagicMock()
        # Set type to Polar
        node.plot_properties.coords.coord_type = ArtistType.POLAR_LINE
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        df = pd.DataFrame({"A": [1], "B": [2]})
        node_controller._on_data_loaded("p1", df, Path("test.csv"))
        
        macro = mock_command_manager.execute_command.call_args[0][0]
        paths = [c.path for c in macro.commands]
        
        assert "coords.theta_axis.limits" in paths
        assert "coords.r_axis.limits" in paths
        assert "coords.xaxis.limits" not in paths

    def test_handlers_graceful_on_invalid_node_id(
        self, node_controller, mock_application_model, mock_command_manager, caplog
    ):
        """Ensures the controller doesn't crash if an event provides a non-existent ID."""
        mock_application_model.scene_root.find_node_by_id.return_value = None
        
        with caplog.at_level(logging.WARNING):
            node_controller._on_rename_node_request("ghost_id", "Ghost")
            node_controller.reconcile_node_property("ghost_id", "path", 1)
            
        assert "Node with ID 'ghost_id' not found" in caplog.text
        mock_command_manager.execute_command.assert_not_called()

    def test_on_selection_changed_for_ui_multi_selection_no_op(
        self, node_controller, mock_event_aggregator
    ):
        """Verifies that multi-selection does NOT trigger tab switching."""
        # 2 nodes selected
        node_controller._on_selection_changed_for_ui(["p1", "p2"])
        
        # Verify no tab switch request
        mock_event_aggregator.publish.assert_not_called()

    def test_on_delete_nodes_request_dispatches_macro(self, node_controller, mock_command_manager):
        """Verifies that multiple deletion requests are wrapped in a MacroCommand."""
        node_controller._on_delete_nodes_request(["p1", "p2"])
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, MacroCommand)
        assert len(command.commands) == 2
        assert all(isinstance(c, DeleteNodeCommand) for c in command.commands)

    def test_on_delete_single_node_request_dispatches_direct_command(self, node_controller, mock_command_manager):
        """Verifies that a single deletion request is dispatched as a direct DeleteNodeCommand."""
        node_controller._on_delete_nodes_request(["p1"])
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, DeleteNodeCommand)
        assert command.node_id == "p1"

    def test_on_add_plot_request_dispatches_command(self, node_controller, mock_command_manager):
        """Verifies that an add plot request dispatches an AddPlotCommand."""
        from src.shared.geometry import Rect
        geom = Rect(0.1, 0.1, 0.2, 0.2)
        node_controller._on_add_plot_request(geom)
        
        mock_command_manager.execute_command.assert_called_once()
        command = mock_command_manager.execute_command.call_args[0][0]
        assert isinstance(command, AddPlotCommand)
        assert command.geometry == geom
