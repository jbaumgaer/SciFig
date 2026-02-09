import pytest
from unittest.mock import MagicMock
import matplotlib.figure
from pathlib import Path
import uuid # Keep for mock.id generation

# Import the actual classes and functions
from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import FreeConfig, LayoutConfig, GridConfig, Margins, Gutters
from src.models.nodes.group_node import GroupNode
from src.models.nodes.scene_node import SceneNode
from src.services.config_service import ConfigService
import src.models.nodes.scene_node as scene_node # Import as alias to access node_factory

# --- Fixtures ---
# All generic mock fixtures are moved to tests/unit/conftest.py
# Only application_model_with_mocks remains as it's the specific test subject setup

@pytest.fixture
def application_model_with_mocks(mock_figure, mock_config_service):
    """Provides an ApplicationModel instance with mocked dependencies."""
    model = ApplicationModel(figure=mock_figure, config_service=mock_config_service)
    # Replace the actual signals with MagicMock instances for easier testing
    # Using MagicMock() directly so .emit() is a callable mock
    model.modelChanged = MagicMock() 
    model.selectionChanged = MagicMock()
    model.layoutConfigChanged = MagicMock()
    return model

# --- Tests ---

class TestApplicationModel:

    def test_initialization(self, application_model_with_mocks, mock_figure, mock_config_service):
        """Verifies initial state of ApplicationModel."""
        model = application_model_with_mocks
        assert isinstance(model.scene_root, GroupNode)
        assert model.scene_root.name == "root"
        assert model.selection == []
        assert model.figure is mock_figure
        assert model._config_service is mock_config_service
        assert isinstance(model.current_layout_config, FreeConfig)

    def test_add_node_to_root(self, application_model_with_mocks, mock_scene_node):
        """Tests adding a node to the scene root."""
        model = application_model_with_mocks
        # Use _children.clear() to clear the internal list as 'children' property has no setter
        model.scene_root._children.clear() 
        initial_child_count = len(model.scene_root.children)
        
        model.add_node(mock_scene_node)
        
        assert len(model.scene_root.children) == initial_child_count + 1
        assert mock_scene_node in model.scene_root.children
        model.modelChanged.emit.assert_called_once()

    def test_add_node_to_specific_parent(self, application_model_with_mocks, mock_scene_node, mock_group_node):
        """Tests adding a node to a specific parent group node."""
        model = application_model_with_mocks
        # Clear the scene_root's children for a clean test
        model.scene_root._children.clear() 
        model.scene_root.add_child(mock_group_node)
        
        # Reset mocks after setup that might emit signals
        model.modelChanged.reset_mock() 

        initial_child_count = len(mock_group_node.children)
        
        model.add_node(mock_scene_node, parent=mock_group_node)
        
        assert len(mock_group_node.children) == initial_child_count + 1
        assert mock_scene_node in mock_group_node.children
        model.modelChanged.emit.assert_called_once()


    def test_clear_scene(self, application_model_with_mocks, mock_scene_node, mock_group_node):
        """Tests clearing all nodes from the scene."""
        model = application_model_with_mocks
        model.add_node(mock_scene_node)
        model.add_node(mock_group_node)
        model.set_selection([mock_scene_node])
        model.modelChanged.reset_mock()
        model.selectionChanged.reset_mock()

        model.clear_scene()

        assert model.scene_root.children == []
        assert model.selection == []
        model.modelChanged.emit.assert_called_once()
        model.selectionChanged.emit.assert_called_once()

    def test_set_scene_root(self, application_model_with_mocks, mock_group_node, mock_scene_node):
        """Tests setting a new scene root."""
        model = application_model_with_mocks
        # Ensure clean state for scene_root children before adding
        model.scene_root._children.clear() 
        model.add_node(mock_scene_node) # Add some node to old root
        model.set_selection([mock_scene_node]) # Set some selection
        model.modelChanged.reset_mock()
        model.selectionChanged.reset_mock()

        model.set_scene_root(mock_group_node)

        assert model.scene_root is mock_group_node
        assert model.selection == []
        model.modelChanged.emit.assert_called_once()
        model.selectionChanged.emit.assert_called_once() # selection is cleared, so signal should emit

    def test_set_selection(self, application_model_with_mocks, mock_scene_node):
        """Tests setting the selection."""
        model = application_model_with_mocks
        model.selectionChanged.reset_mock() # Reset from potential init calls

        new_selection = [mock_scene_node]
        model.set_selection(new_selection)

        assert model.selection == new_selection
        model.selectionChanged.emit.assert_called_once()
        
    def test_set_selection_empty(self, application_model_with_mocks):
        """Tests setting an empty selection."""
        model = application_model_with_mocks
        model.set_selection([MagicMock(spec=SceneNode)]) # Set some initial selection
        model.selectionChanged.reset_mock()

        model.set_selection([])
        
        assert model.selection == []
        model.selectionChanged.emit.assert_called_once()

    @pytest.mark.parametrize("new_config_instance", [
        FreeConfig(), # This will be equal to initial current_layout_config
        GridConfig(
            rows=2, cols=2,
            row_ratios=[0.5, 0.5], col_ratios=[0.5, 0.5],
            margins=Margins(top=0.1, bottom=0.1, left=0.1, right=0.1),
            gutters=Gutters(hspace=[0.1], wspace=[0.1])
        )
    ])
    def test_current_layout_config_setter_getter(self, application_model_with_mocks, new_config_instance):
        """Tests setting and getting the current layout configuration."""
        model = application_model_with_mocks
        model.layoutConfigChanged.reset_mock()
        model.modelChanged.reset_mock()
        
        # Determine expected emit calls based on whether config actually changes
        # Initial config is FreeConfig() from ApplicationModel.__init__
        initial_config_is_free_instance = isinstance(model.current_layout_config, FreeConfig)
        new_config_is_free_instance = isinstance(new_config_instance, FreeConfig)
        
        if initial_config_is_free_instance and new_config_is_free_instance and model.current_layout_config == new_config_instance:
            expected_emits = 0 # No change, so no emits
        else:
            expected_emits = 1 # Change, so emits

        # Test setter
        model.current_layout_config = new_config_instance
        # Use == for value comparison for dataclass instances
        assert model.current_layout_config == new_config_instance 
        
        # Verify signals emitted
        if expected_emits == 1:
            model.layoutConfigChanged.emit.assert_called_once()
            model.modelChanged.emit.assert_called_once()
        else: # expected_emits == 0
            model.layoutConfigChanged.emit.assert_not_called()
            model.modelChanged.emit.assert_not_called()
        
        # Test setting same config again after initial change (if any)
        # This part ensures that setting the same value consecutively does not emit signals
        model.layoutConfigChanged.reset_mock()
        model.modelChanged.reset_mock()
        model.current_layout_config = new_config_instance
        model.layoutConfigChanged.emit.assert_not_called()
        model.modelChanged.emit.assert_not_called()


    def test_get_node_at(self, application_model_with_mocks, mock_group_node, mock_scene_node, mocker):
        """Tests finding a node at a given position using hit_test."""
        model = application_model_with_mocks
        position = (10.0, 20.0)

        # Patch hit_test method on the actual scene_root instance
        mock_hit_test = mocker.patch.object(model.scene_root, 'hit_test', return_value=None)
        
        # Case 1: No node at position
        assert model.get_node_at(position) is None
        mock_hit_test.assert_called_once_with(position)
        mock_hit_test.reset_mock() # Reset mock call count

        # Case 2: A node is at position
        mock_hit_test.return_value = mock_scene_node
        assert model.get_node_at(position) is mock_scene_node
        mock_hit_test.assert_called_once_with(position)
        mock_hit_test.reset_mock()

        # Case 3: Another node is at position
        mock_hit_test.return_value = mock_group_node
        assert model.get_node_at(position) is mock_group_node
        mock_hit_test.assert_called_once_with(position)
        mocker.stopall() # Clean up patches


    def test_to_dict_empty_scene(self, application_model_with_mocks, mocker):
        """Tests serialization of an empty scene."""
        model = application_model_with_mocks
        
        # Ensure a concrete layout config for to_dict, and mock its to_dict method
        free_config_instance = FreeConfig()
        model.current_layout_config = free_config_instance

        # Mock the scene_root's to_dict to control its output
        mocker.patch.object(model.scene_root, 'to_dict', return_value={
            "id": model.scene_root.id, 
            "type": "GroupNode", 
            "name": "root", 
            "visible": True, 
            "children": []
        })

        expected_dict = {
            "version": "1.0",
            "scene_root": {
                "id": model.scene_root.id, 
                "type": "GroupNode", 
                "name": "root", 
                "visible": True, 
                "children": []
            },
            "layout_config": free_config_instance.to_dict() # Use actual to_dict output
        }
        actual_dict = model.to_dict()
        assert actual_dict == expected_dict
        model.scene_root.to_dict.assert_called_once()
        mocker.stopall()


    def test_to_dict_with_nodes_and_layout(self, application_model_with_mocks, mocker):
        """Tests serialization with nodes and a specific layout config."""
        model = application_model_with_mocks
        # Clear existing children for a clean test setup of real nodes
        model.scene_root._children.clear()
        
        real_scene_node = SceneNode(name="RealNode1")
        real_group_node = GroupNode(name="RealGroup1")
        real_group_node.add_child(SceneNode(name="RealNode2"))
        model.add_node(real_scene_node)
        model.add_node(real_group_node)
        
        # Mock layout config and its to_dict method
        grid_config_instance = GridConfig(
            rows=2, cols=2,
            row_ratios=[0.5, 0.5], col_ratios=[0.5, 0.5],
            margins=Margins(top=0.1, bottom=0.1, left=0.1, right=0.1),
            gutters=Gutters(hspace=[0.1], wspace=[0.1])
        )
        model.current_layout_config = grid_config_instance

        # Mock scene_root's to_dict to return a controlled structure based on real nodes' to_dict
        mocker.patch.object(model.scene_root, 'to_dict', return_value={
            "id": model.scene_root.id, 
            "type": "GroupNode", 
            "name": "root", 
            "visible": True, 
            "children": [
                real_scene_node.to_dict(), 
                real_group_node.to_dict()
            ]
        })

        model_dict = model.to_dict()
        
        assert model_dict["version"] == "1.0"
        # Verify content of scene_root by checking the mocked return value
        assert model_dict["scene_root"] == {
            "id": model.scene_root.id, 
            "type": "GroupNode", 
            "name": "root", 
            "visible": True, 
            "children": [
                real_scene_node.to_dict(), 
                real_group_node.to_dict()
            ]
        }
        assert model_dict["layout_config"] == grid_config_instance.to_dict() # Use actual to_dict output
        
        model.scene_root.to_dict.assert_called_once()
        mocker.stopall()


    def test_load_from_dict_empty_data(self, application_model_with_mocks, mocker):
        """Tests loading from an empty dictionary, ensuring default state."""
        model = application_model_with_mocks
        
        # Mock node_factory to return a simple GroupNode
        mock_new_root_node = GroupNode(name="new_root", id=str(uuid.uuid4()))
        node_factory_patch = mocker.patch('src.models.application_model.node_factory', return_value=mock_new_root_node)
        
        # We expect LayoutConfig.from_dict to NOT be called, as FreeConfig() is directly assigned
        layout_config_from_dict_patch = mocker.patch('src.models.layout.layout_config.LayoutConfig.from_dict')
        
        model.modelChanged.reset_mock()
        model.selectionChanged.reset_mock() 

        empty_data = {
            "version": "1.0",
            "scene_root": {"id": str(uuid.uuid4()), "type": "GroupNode", "name": "new_root", "children": [], "visible": True}
        }
        model.load_from_dict(empty_data, temp_dir=Path("."))
        
        assert model.scene_root is mock_new_root_node # Should be the mocked instance
        assert model.scene_root.name == "new_root"
        assert isinstance(model.current_layout_config, FreeConfig) # Assert type, not identity
        
        # Assert signal call counts
        model.selectionChanged.emit.assert_called_once() # clear_scene -> set_selection
        assert model.modelChanged.emit.call_count == 2 # 1 from clear_scene + 1 from end of load_from_dict
        
        # Use the stored patch object for assertion
        node_factory_patch.assert_called_once_with(empty_data["scene_root"], temp_dir=Path("."))
        layout_config_from_dict_patch.assert_not_called() 
        mocker.stopall()


    def test_load_from_dict_with_data(self, application_model_with_mocks, mocker):
        """Tests loading from a dictionary with scene data and layout config."""
        model = application_model_with_mocks
        
        mock_loaded_root = GroupNode(name="loaded_root", id=str(uuid.uuid4()))
        node_factory_patch = mocker.patch('src.models.application_model.node_factory', return_value=mock_loaded_root)
        
        mock_loaded_layout_config = GridConfig(
            rows=1, cols=1, row_ratios=[1.0], col_ratios=[1.0], 
            margins=Margins(top=0.0, bottom=0.0, left=0.0, right=0.0),
            gutters=Gutters(hspace=[], wspace=[])
        )
        layout_config_from_dict_patch = mocker.patch('src.models.layout.layout_config.LayoutConfig.from_dict', return_value=mock_loaded_layout_config)
        
        model.modelChanged.reset_mock()
        model.selectionChanged.reset_mock() 
        model.layoutConfigChanged.reset_mock() # Reset for this specific test

        data = {
            "version": "1.0",
            "scene_root": {"id": str(uuid.uuid4()), "type": "GroupNode", "name": "loaded_root", "children": [], "visible": True},
            "layout_config": {"mode": "grid", "rows": 2, "cols": 2} # This will trigger LayoutConfig.from_dict
        }
        temp_dir = Path("./temp")
        model.load_from_dict(data, temp_dir=temp_dir)

        assert model.scene_root is mock_loaded_root
        assert model.current_layout_config is mock_loaded_layout_config
        
        # Assert signal call counts
        model.selectionChanged.emit.assert_called_once() # clear_scene -> set_selection
        model.layoutConfigChanged.emit.assert_called_once() # current_layout_config setter
        assert model.modelChanged.emit.call_count == 3 # 1 (clear_scene) + 1 (layout config setter) + 1 (end of load_from_dict)

        # Verify node_factory was called correctly
        node_factory_patch.assert_called_once_with(data["scene_root"], temp_dir=temp_dir)
        # Verify LayoutConfig.from_dict was called correctly
        layout_config_from_dict_patch.assert_called_once_with(data["layout_config"])
        mocker.stopall()


    def test_load_from_dict_missing_layout_config(self, application_model_with_mocks, mocker):
        """Tests loading from dict when layout_config is missing, ensuring it defaults to FreeConfig."""
        model = application_model_with_mocks
        
        mock_loaded_root = GroupNode(name="loaded_root", id=str(uuid.uuid4()))
        node_factory_patch = mocker.patch('src.models.application_model.node_factory', return_value=mock_loaded_root)
        
        # We expect LayoutConfig.from_dict to NOT be called.
        layout_config_from_dict_patch = mocker.patch('src.models.layout.layout_config.LayoutConfig.from_dict') 
        
        model.modelChanged.reset_mock()
        model.selectionChanged.reset_mock()
        model.layoutConfigChanged.reset_mock() # Reset for this specific test

        data = {
            "version": "1.0",
            "scene_root": {"id": str(uuid.uuid4()), "type": "GroupNode", "name": "loaded_root", "children": [], "visible": True}
            # layout_config is missing
        }
        temp_dir = Path("./temp")
        model.load_from_dict(data, temp_dir=temp_dir)

        assert model.scene_root is mock_loaded_root
        assert isinstance(model.current_layout_config, FreeConfig) # It should be a *real* FreeConfig instance now
        
        # Assert signal call counts
        model.selectionChanged.emit.assert_called_once() # clear_scene -> set_selection
        model.layoutConfigChanged.emit.assert_not_called() # No layout config data, so setter doesn't emit
        assert model.modelChanged.emit.call_count == 2 # 1 (clear_scene) + 1 (end of load_from_dict)

        node_factory_patch.assert_called_once_with(data["scene_root"], temp_dir=temp_dir)
        layout_config_from_dict_patch.assert_not_called() # Should not be called
        mocker.stopall()

    def test_serialization_round_trip(self, application_model_with_mocks, mocker):
        """
        Tests a full serialization and deserialization round trip.
        This test is more integrated and uses real SceneNode/GroupNode for data integrity.
        """
        # Create a real ApplicationModel with real nodes/configs for a proper round-trip
        real_model = ApplicationModel(figure=MagicMock(spec=matplotlib.figure.Figure), config_service=MagicMock(spec=ConfigService))
        
        # Create real nodes with minimal required arguments
        node1 = SceneNode(name="Node1")
        group1 = GroupNode(name="Group1")
        node2 = SceneNode(name="Node2")
        group1.add_child(node2) # Add node2 to group1
        real_model.add_node(node1) # Add node1 to real_model's scene_root
        real_model.add_node(group1) # Add group1 to real_model's scene_root

        grid_config = GridConfig(
            rows=2, cols=2,
            row_ratios=[0.5, 0.5], col_ratios=[0.5, 0.5],
            margins=Margins(top=0.1, bottom=0.1, left=0.1, right=0.1),
            gutters=Gutters(hspace=[0.1], wspace=[0.1])
        )
        real_model.current_layout_config = grid_config
        
        # Patch src.models.application_model.node_factory to return the *real* node_factory
        # The real node_factory needs to be imported to be used as side_effect
        node_factory_patch = mocker.patch('src.models.application_model.node_factory', side_effect=scene_node.node_factory)
        # Patch LayoutConfig.from_dict to return the *real* LayoutConfig.from_dict
        layout_config_from_dict_patch = mocker.patch('src.models.layout.layout_config.LayoutConfig.from_dict', side_effect=LayoutConfig.from_dict)
        
        # Serialize the original model
        serialized_data = real_model.to_dict()

        # Create a new model instance and deserialize into it
        loaded_model = ApplicationModel(figure=MagicMock(spec=matplotlib.figure.Figure), config_service=MagicMock(spec=ConfigService))
        # Important: Pass temp_dir even if not used by all nodes, as the signature requires it
        loaded_model.load_from_dict(serialized_data, temp_dir=Path(".")) 
        
        # Compare the serialized data of both models
        # This implicitly tests if the loaded_model's structure and data match the original
        loaded_serialized_data = loaded_model.to_dict()
        
        # Assertions
        assert serialized_data == loaded_serialized_data
        
        # Also check some specific attributes for clarity and robustness
        assert loaded_model.current_layout_config == grid_config # Use == for value comparison
        assert len(loaded_model.scene_root.children) == 2 # node1 and group1
        assert loaded_model.scene_root.children[0].name == "Node1"
        assert isinstance(loaded_model.scene_root.children[1], GroupNode)
        assert loaded_model.scene_root.children[1].name == "Group1"
        assert len(loaded_model.scene_root.children[1].children) == 1
        assert loaded_model.scene_root.children[1].children[0].name == "Node2"

        # Verify that node_factory and LayoutConfig.from_dict were called
        node_factory_patch.assert_called() # Check if it was called at least once
        layout_config_from_dict_patch.assert_called() # Check if it was called at least once
        mocker.stopall()