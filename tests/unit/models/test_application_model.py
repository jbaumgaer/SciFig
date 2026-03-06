import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

import src.models.nodes.scene_node as scene_node
from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import (
    FreeConfig,
    GridConfig,
    Gutters,
    LayoutConfig,
    Margins,
)
from src.models.nodes.group_node import GroupNode
from src.models.nodes.scene_node import SceneNode
from src.shared.events import Events


@pytest.fixture
def application_model_with_mocks(mock_event_aggregator):
    """Provides an ApplicationModel instance with a mocked EventAggregator."""
    return ApplicationModel(event_aggregator=mock_event_aggregator)


class TestApplicationModel:

    def test_initialization(self, mock_event_aggregator):
        """Verifies initial state of ApplicationModel."""
        model = ApplicationModel(event_aggregator=mock_event_aggregator)
        assert isinstance(model.scene_root, GroupNode)
        assert model.scene_root.name == "root"
        assert model.selection == []
        assert isinstance(model.current_layout_config, FreeConfig)
        assert model.is_dirty is False
        assert model.file_path is None

    # --- State Management Tests ---

    def test_set_dirty(self, application_model_with_mocks):
        """Tests setting the dirty status."""
        model = application_model_with_mocks
        assert model.is_dirty is False

        model.set_dirty(True)
        assert model.is_dirty is True

        model.set_dirty(False)
        assert model.is_dirty is False

    def test_reset_state(self, application_model_with_mocks, mock_event_aggregator):
        """Tests resetting the model to a default state."""
        model = application_model_with_mocks
        model.scene_root = GroupNode(name="new_root")
        model.set_selection([SceneNode()])
        model.file_path = Path("test.sci")
        model.set_dirty(True)

        mock_event_aggregator.publish.reset_mock()

        model.reset_state()

        assert model.scene_root.name == "root"
        assert model.selection == []
        assert model.file_path is None
        assert model.is_dirty is False
        assert isinstance(model.current_layout_config, FreeConfig)

        # Verify events
        mock_event_aggregator.publish.assert_any_call(Events.PROJECT_WAS_RESET)
        mock_event_aggregator.publish.assert_any_call(
            Events.SELECTION_CHANGED, selected_node_ids=[]
        )

    # --- Scene Graph Manipulation Tests ---

    def test_add_node_to_root(self, application_model_with_mocks, mock_scene_node):
        """Tests adding a node to the scene root."""
        model = application_model_with_mocks
        initial_child_count = len(model.scene_root.children)

        model.add_node(mock_scene_node)

        assert len(model.scene_root.children) == initial_child_count + 1
        assert mock_scene_node in model.scene_root.children

    def test_add_node_to_specific_parent(
        self, application_model_with_mocks, mock_scene_node
    ):
        """Tests adding a node to a specific parent group node."""
        model = application_model_with_mocks
        parent = GroupNode(name="parent")
        model.scene_root.add_child(parent)

        model.add_node(mock_scene_node, parent=parent)

        assert mock_scene_node in parent.children

    def test_set_scene_root(self, application_model_with_mocks, mock_event_aggregator):
        """Tests setting a new scene root, which should clear selection."""
        model = application_model_with_mocks
        node = SceneNode(id="old_node")
        model.set_selection([node])
        
        new_root = GroupNode(name="new_root")
        mock_event_aggregator.publish.reset_mock()
        
        model.set_scene_root(new_root)
        
        assert model.scene_root is new_root
        assert model.selection == []
        mock_event_aggregator.publish.assert_called_once_with(
            Events.SELECTION_CHANGED, selected_node_ids=[]
        )

    # --- Selection Tests ---

    def test_set_selection(self, application_model_with_mocks, mock_event_aggregator):
        """Tests setting the selection."""
        model = application_model_with_mocks
        node = SceneNode(id="test_id")
        
        mock_event_aggregator.publish.reset_mock()
        
        model.set_selection([node])

        assert model.selection == [node]
        mock_event_aggregator.publish.assert_called_once_with(
            Events.SELECTION_CHANGED, selected_node_ids=["test_id"]
        )

    def test_set_selection_empty(self, application_model_with_mocks, mock_event_aggregator):
        """Tests clearing the selection."""
        model = application_model_with_mocks
        model.set_selection([SceneNode(id="p1")])
        
        mock_event_aggregator.publish.reset_mock()
        
        model.set_selection([])
        
        assert model.selection == []
        mock_event_aggregator.publish.assert_called_once_with(
            Events.SELECTION_CHANGED, selected_node_ids=[]
        )

    def test_set_selected_path(self, application_model_with_mocks, mock_event_aggregator):
        """Tests setting a sub-component selection path."""
        model = application_model_with_mocks
        node = SceneNode(id="test_id")
        model.set_selection([node])
        
        mock_event_aggregator.publish.reset_mock()
        
        model.set_selected_path("coords.xaxis")
        
        assert model.selected_path == "coords.xaxis"
        mock_event_aggregator.publish.assert_called_once_with(
            Events.SUB_COMPONENT_SELECTED, node_id="test_id", path="coords.xaxis"
        )

    # --- Layout Tests ---

    @pytest.mark.parametrize(
        "new_config",
        [
            FreeConfig(),
            GridConfig(
                rows=2, cols=2,
                row_ratios=[0.5, 0.5], col_ratios=[0.5, 0.5],
                margins=Margins(0.1, 0.1, 0.1, 0.1),
                gutters=Gutters([0.1], [0.1])
            ),
        ],
    )
    def test_current_layout_config_setter(self, application_model_with_mocks, new_config):
        """Tests setting and getting the current layout configuration."""
        model = application_model_with_mocks
        
        model.current_layout_config = new_config
        assert model.current_layout_config == new_config
        
        # Test idempotency (setting same config again shouldn't do anything)
        model.current_layout_config = new_config
        assert model.current_layout_config == new_config

    # --- Utility Tests ---

    def test_get_node_at(self, application_model_with_mocks, mocker):
        """Tests finding a node at a given position using hit_test."""
        model = application_model_with_mocks
        position = (0.5, 0.5)
        mock_node = SceneNode()
        
        mocker.patch.object(model.scene_root, "hit_test", return_value=mock_node)
        
        assert model.get_node_at(position) is mock_node
        model.scene_root.hit_test.assert_called_once_with(position)

    def test_extract_plot_states(self, application_model_with_mocks, mocker):
        """Tests extracting states from all PlotNodes in the scene graph."""
        from src.models.nodes.plot_node import PlotNode
        model = application_model_with_mocks
        
        # Setup scene graph: root -> group -> [plot1, plot2], plot3
        plot1 = PlotNode(id="p1")
        plot1.data = MagicMock(spec=pd.DataFrame)
        plot1.plot_properties = MagicMock()
        plot1.plot_properties.to_dict.return_value = {"type": "line"}
        
        plot2 = PlotNode(id="p2")
        # No data for plot2, should be ignored
        
        plot3 = PlotNode(id="p3")
        plot3.data = MagicMock(spec=pd.DataFrame)
        plot3.plot_properties = MagicMock()
        plot3.plot_properties.to_dict.return_value = {"type": "scatter"}
        
        group = GroupNode(name="group")
        group.add_child(plot1)
        group.add_child(plot2)
        
        model.add_node(group)
        model.add_node(plot3)
        
        states = model.extract_plot_states()
        
        assert len(states) == 2
        
        # Verify p1
        p1_state = next(s for s in states if s["id"] == "p1")
        assert p1_state["data"] is plot1.data
        assert p1_state["plot_properties_dict"] == {"type": "line"}
        
        # Verify p3
        p3_state = next(s for s in states if s["id"] == "p3")
        assert p3_state["data"] is plot3.data
        assert p3_state["plot_properties_dict"] == {"type": "scatter"}

    # --- Serialization Tests ---

    def test_as_dict(self, application_model_with_mocks, mocker):
        """Tests serialization of the model."""
        model = application_model_with_mocks
        
        mocker.patch.object(model.scene_root, "to_dict", return_value={"root": "data"})
        # Use actual to_dict from FreeConfig (default)
        layout_dict = model.current_layout_config.to_dict()
        
        expected = {
            "version": "1.0",
            "scene_root": {"root": "data"},
            "layout_config": layout_dict
        }
        
        assert model.as_dict() == expected

    def test_load_from_state_basic(self, application_model_with_mocks, mocker):
        """Tests basic loading from a state dictionary."""
        model = application_model_with_mocks
        mock_new_root = GroupNode(name="loaded")
        mocker.patch("src.models.application_model.node_factory", return_value=mock_new_root)
        
        data = {
            "scene_root": {"some": "node_data"},
            "layout_config": {"mode": "free_form"}
        }
        temp_dir = Path("./temp")
        
        model.load_from_state(data, temp_dir=temp_dir)
        
        assert model.scene_root is mock_new_root
        assert model.is_dirty is False
        assert isinstance(model.current_layout_config, FreeConfig)

    def test_load_from_state_missing_layout(self, application_model_with_mocks, mocker):
        """Tests that loading defaults to FreeConfig if layout data is missing."""
        model = application_model_with_mocks
        mocker.patch("src.models.application_model.node_factory", return_value=GroupNode())
        
        # Grid config is active before load
        model.current_layout_config = GridConfig(1,1,[1],[1], Margins(0,0,0,0), Gutters([],[]))
        
        data = {"scene_root": {"some": "data"}} # No layout_config
        model.load_from_state(data, Path("."))
        
        assert isinstance(model.current_layout_config, FreeConfig)

    def test_load_from_state_resets_dirty_and_selection(self, application_model_with_mocks, mocker):
        """Tests that loading state resets dirty flag and selection."""
        model = application_model_with_mocks
        model.set_dirty(True)
        model.set_selection([SceneNode()])
        mocker.patch("src.models.application_model.node_factory", return_value=GroupNode())
        
        data = {"scene_root": {"some": "data"}}
        model.load_from_state(data, Path("."))
        
        assert model.is_dirty is False
        assert model.selection == []

    def test_serialization_round_trip(self, real_event_aggregator, mocker):
        """Tests a full serialization and deserialization round trip with complex data."""
        model = ApplicationModel(event_aggregator=real_event_aggregator)
        
        node1 = SceneNode(name="Node1")
        model.add_node(node1)
        
        grid_config = GridConfig(
            rows=2, cols=2,
            row_ratios=[0.5, 0.5], col_ratios=[0.5, 0.5],
            margins=Margins(0.1, 0.1, 0.1, 0.1),
            gutters=Gutters([0.1], [0.1])
        )
        model.current_layout_config = grid_config
        
        # Patch node_factory to use the real one for true round-trip
        mocker.patch("src.models.application_model.node_factory", side_effect=scene_node.node_factory)
        
        serialized = model.as_dict()
        
        new_model = ApplicationModel(event_aggregator=real_event_aggregator)
        new_model.load_from_state(serialized, temp_dir=Path("."))
        
        assert new_model.as_dict() == serialized
        assert isinstance(new_model.current_layout_config, GridConfig)
        assert new_model.current_layout_config.rows == 2
        assert len(new_model.scene_root.children) == 1
        assert new_model.scene_root.children[0].name == "Node1"
