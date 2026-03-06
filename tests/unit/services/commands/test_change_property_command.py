import pytest
from unittest.mock import MagicMock, ANY, create_autospec
from src.services.commands.change_plot_property_command import ChangePlotPropertyCommand, PropertyPathError
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import PlotProperties, Cartesian2DProperties
from src.shared.events import Events


class TestChangePlotPropertyCommand:

    def test_get_root_resolution(self, mock_event_aggregator, mock_property_service):
        """Verifies that the command correctly identifies the target object (Node vs Properties)."""
        node = PlotNode(id="p1", name="Plot")
        # Use real objects for structural checks
        node.plot_properties = PlotProperties(
            titles={},
            coords=MagicMock(spec=Cartesian2DProperties),
            legend={},
            artists=[]
        )
        
        # 1. Target Node (name exists on node, but NOT on plot_properties)
        cmd_node = ChangePlotPropertyCommand(node, "name", "New", mock_event_aggregator, mock_property_service)
        assert cmd_node._get_root() is node
        
        # 2. Target Properties (titles exists on plot_properties)
        cmd_props = ChangePlotPropertyCommand(node, "titles.left.text", "NewTitle", mock_event_aggregator, mock_property_service)
        assert cmd_props._get_root() is node.plot_properties

    def test_execute_and_undo_basic(self, mock_event_aggregator, mock_property_service):
        """Tests the full lifecycle of a simple property change."""
        node = PlotNode(id="p1")
        node.plot_properties = MagicMock()
        node.plot_properties._version = 1
        
        # Setup PropertyService mocks
        mock_property_service.resolve_concrete_paths.return_value = ["path.to.val"]
        mock_property_service.get_value.return_value = "old"
        
        cmd = ChangePlotPropertyCommand(node, "path.to.val", "new", mock_event_aggregator, mock_property_service)
        
        # Execute
        cmd.execute()
        
        mock_property_service.set_value.assert_called_with(ANY, "path.to.val", "new")
        assert node.plot_properties._version == 2
        mock_event_aggregator.publish.assert_called_with(
            Events.PLOT_COMPONENT_CHANGED, node_id="p1", path="path.to.val", new_value="new"
        )
        
        # Undo
        cmd.undo()
        
        mock_property_service.set_value.assert_called_with(ANY, "path.to.val", "old")
        assert node.plot_properties._version == 3
        mock_event_aggregator.publish.assert_called_with(
            Events.PLOT_COMPONENT_CHANGED, node_id="p1", path="path.to.val", new_value=None
        )

    def test_execute_multi_path_expansion(self, mock_event_aggregator, mock_property_service):
        """Tests that a single path can affect multiple concrete properties."""
        node = PlotNode(id="p1")
        node.plot_properties = MagicMock()
        
        # Setup PropertyService to resolve one path to two concrete ones
        mock_property_service.resolve_concrete_paths.return_value = ["color1", "color2"]
        mock_property_service.get_value.side_effect = ["old1", "old2"]
        
        cmd = ChangePlotPropertyCommand(node, "wildcard.color", "red", mock_event_aggregator, mock_property_service)
        cmd.execute()
        
        # Check expansion map
        assert cmd._expansion_map == {"color1": "old1", "color2": "old2"}
        assert mock_property_service.set_value.call_count == 2

    def test_invalid_path_raises_error(self, mock_event_aggregator, mock_property_service):
        """Ensures PropertyPathError is raised if path resolution fails."""
        node = PlotNode()
        mock_property_service.resolve_concrete_paths.return_value = []
        
        cmd = ChangePlotPropertyCommand(node, "invalid", 1, mock_event_aggregator, mock_property_service)
        
        with pytest.raises(PropertyPathError):
            cmd.execute()

    def test_execute_without_publish(self, mock_event_aggregator, mock_property_service):
        """Verifies the publish flag is respected."""
        node = PlotNode()
        mock_property_service.resolve_concrete_paths.return_value = ["p"]
        
        cmd = ChangePlotPropertyCommand(node, "p", 1, mock_event_aggregator, mock_property_service)
        cmd.execute(publish=False)
        
        mock_event_aggregator.publish.assert_not_called()
