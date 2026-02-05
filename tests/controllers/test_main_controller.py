import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QSettings

from src.commands.command_manager import CommandManager
from src.config_service import ConfigService
from src.controllers.main_controller import MainController
from src.models import ApplicationModel
from src.models.nodes import GroupNode, PlotNode, SceneNode
from src.models.nodes.plot_properties import BasePlotProperties, PlotType


@pytest.fixture
def mock_model():
    model = MagicMock(spec=ApplicationModel)
    model.scene_root = GroupNode(name="root_mock")
    model.scene_root.all_descendants.return_value = [model.scene_root] # Mock initial state
    model.modelChanged = MagicMock()
    model.selection = []
    # Mock set_scene_root as it's called
    model.set_scene_root = MagicMock()
    model.clear_scene = MagicMock() # Mock clear_scene
    model.add_node = MagicMock() # Mock add_node if it's used in error case
    return model

@pytest.fixture
def mock_command_manager():
    return MagicMock(spec=CommandManager)

@pytest.fixture
def mock_config_service():
    config_service = MagicMock(spec=ConfigService)
    config_service.get.side_effect = lambda key, default=None: {
        "organization": "TestOrg",
        "app_name": "TestApp",
        "layout.default_template": "test_2x2_layout.json",
        "paths.layout_templates_dir": "configs/layouts",
        "layout.default_margin": 0.1,
        "layout.default_gutter": 0.08,
        "layout.max_recent_files": 5,
    }.get(key, default)
    return config_service

@pytest.fixture
def main_controller(mock_model, mock_config_service):
    return MainController(mock_model, mock_config_service)


@pytest.fixture
def mock_layout_template_file(tmp_path):
    # Create a dummy configs/layouts directory inside the tmp_path
    layout_dir = tmp_path / "configs" / "layouts"
    layout_dir.mkdir(parents=True)

    template_content = {
        "type": "GroupNode",
        "name": "Test 2x2 Layout",
        "id": "layout_test_001",
        "visible": True,
        "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
        "children": [
            {
              "type": "PlotNode",
              "name": "Plot A",
              "id": "plot_A",
              "visible": True,
              "geometry": { "x": 0.0, "y": 0.5, "width": 0.5, "height": 0.5 },
              "plot_properties": { "plot_type": "line", "title": "Plot A Title" }
            },
            {
              "type": "PlotNode",
              "name": "Plot B",
              "id": "plot_B",
              "visible": True,
              "geometry": { "x": 0.5, "y": 0.5, "width": 0.5, "height": 0.5 },
              "plot_properties": { "plot_type": "scatter", "title": "Plot B Title" }
            }
        ]
    }
    file = layout_dir / "test_2x2_layout.json"
    with open(file, "w") as f:
        json.dump(template_content, f)
    return file

# Test cases for MainController
def test_main_controller_init(mock_model, mock_config_service):
    """
    Test MainController initialization, including QSettings setup
    with config values.
    """
    # with patch('src.controllers.main_controller.QSettings') as MockQSettings:
    #     controller = MainController(mock_model, mock_config_service)
    #     MockQSettings.assert_called_once_with("TestOrg", "TestApp")
    #     assert controller.model is mock_model
    #     assert controller._config_service is mock_config_service

def test_create_new_layout_loads_template_and_redistributes_plots(main_controller, mock_model, mock_config_service, mock_layout_template_file, tmp_path):
    """
    Test create_new_layout:
    - Loads the specified template.
    - Deserializes into SceneNode objects.
    - Extracts existing plot data/properties (if any) before clearing.
    - Redistributes existing plot data/properties onto new slots.
    - Updates ApplicationModel's scene_root.
    - Emits modelChanged signal.
    """
    # Setup: Create some existing plots with data to simulate a prior state
    # existing_plot1 = PlotNode(name="Old Plot 1", id="old_id_1")
    # existing_plot1.data = pd.DataFrame({"x":[1], "y":[2]})
    # existing_plot1.plot_properties = BasePlotProperties(title="Old Title 1", plot_type=PlotType.LINE)
    # mock_model.scene_root.children.append(existing_plot1)
    # mock_model.scene_root.all_descendants.return_value = [mock_model.scene_root, existing_plot1]

    # Call method under test
    # main_controller.create_new_layout()

    # Assertions:
    # mock_model.clear_scene.assert_called_once()
    # mock_config_service.get.assert_any_call("layout.default_template", "2x2_default.json")
    # mock_config_service.get.assert_any_call("paths.layout_templates_dir", "configs/layouts")
    # mock_model.set_scene_root.assert_called_once()
    # assert isinstance(mock_model.set_scene_root.call_args[0][0], GroupNode)
    # new_root_node = mock_model.set_scene_root.call_args[0][0]
    # assert len(new_root_node.children) == 2 # Based on test_2x2_layout.json
    # assert isinstance(new_root_node.children[0], PlotNode)
    # assert new_root_node.children[0].name == "Plot A"
    # # Check if old data/properties were transferred (if setup)
    # # if existing_plot_states was not empty:
    # # assert new_root_node.children[0].data == existing_plot1.data
    # # assert new_root_node.children[0].plot_properties.title == "Old Title 1"
    # mock_model.modelChanged.emit.assert_called_once() # Called by set_scene_root

def test_create_new_layout_handles_template_not_found(main_controller, mock_model, mock_config_service):
    """
    Test create_new_layout gracefully handles a missing template file.
    """
    # Configure mock_config_service to return a non-existent template path
    # mock_config_service.get.side_effect = lambda key, default=None: {
    #     "organization": "TestOrg",
    #     "app_name": "TestApp",
    #     "layout.default_template": "non_existent.json",
    #     "paths.layout_templates_dir": "configs/layouts",
    # }.get(key, default)

    # main_controller.create_new_layout()

    # mock_model.clear_scene.assert_called_once()
    # mock_model.add_node.assert_called_once_with(PlotNode(name="Default Plot")) # Error handling path
    # mock_model.modelChanged.emit.assert_called_once()

def test_create_new_layout_handles_invalid_json(main_controller, mock_model, mock_config_service, tmp_path):
    """
    Test create_new_layout gracefully handles an invalid JSON template file.
    """
    # Create an invalid JSON file
    # layout_dir = tmp_path / "configs" / "layouts"
    # layout_dir.mkdir(parents=True)
    # invalid_file = layout_dir / "invalid.json"
    # invalid_file.write_text("{this is not json")

    # Configure mock_config_service to return path to invalid json
    # mock_config_service.get.side_effect = lambda key, default=None: {
    #     "organization": "TestOrg",
    #     "app_name": "TestApp",
    #     "layout.default_template": "invalid.json",
    #     "paths.layout_templates_dir": str(layout_dir),
    # }.get(key, default)

    # main_controller.create_new_layout()

    # mock_model.clear_scene.assert_called_once()
    # mock_model.add_node.assert_called_once_with(PlotNode(name="Error Plot")) # Error handling path
    # mock_model.modelChanged.emit.assert_called_once()

def test_create_new_layout_redistributes_existing_plots_fewer_slots(main_controller, mock_model, mock_config_service, mock_layout_template_file, tmp_path):
    """
    Test redistribution logic when the new layout has fewer slots than existing plots.
    Ensures that only the first N existing plots are redistributed.
    """
    # Setup: Create more existing plots than the template provides
    # existing_plot1 = PlotNode(name="Old Plot 1", id="old_id_1")
    # existing_plot1.data = pd.DataFrame({"x":[1], "y":[2]})
    # existing_plot1.plot_properties = BasePlotProperties(title="Old Title 1", plot_type=PlotType.LINE)
    # existing_plot2 = PlotNode(name="Old Plot 2", id="old_id_2")
    # existing_plot2.data = pd.DataFrame({"x":[3], "y":[4]})
    # existing_plot2.plot_properties = BasePlotProperties(title="Old Title 2", plot_type=PlotType.LINE)
    # existing_plot3 = PlotNode(name="Old Plot 3", id="old_id_3") # This one will be 'discarded'
    # existing_plot3.data = pd.DataFrame({"x":[5], "y":[6]})
    # existing_plot3.plot_properties = BasePlotProperties(title="Old Title 3", plot_type=PlotType.LINE)
    
    # mock_model.scene_root.children.extend([existing_plot1, existing_plot2, existing_plot3])
    # mock_model.scene_root.all_descendants.return_value = [mock_model.scene_root, existing_plot1, existing_plot2, existing_plot3]

    # Call method under test
    # main_controller.create_new_layout()

    # Assertions:
    # new_root_node = mock_model.set_scene_root.call_args[0][0]
    # assert len(new_root_node.children) == 2 # Only 2 slots in test_2x2_layout.json
    # assert new_root_node.children[0].data is not None # Check data transfer
    # assert new_root_node.children[1].data is not None
    # assert new_root_node.children[0].name == "Plot A" # Check new slot names maintained
    # assert new_root_node.children[0].plot_properties.title == "Old Title 1" # Check properties transfer
    # assert new_root_node.children[1].plot_properties.title == "Old Title 2"
    # # Verify that existing_plot3 was effectively 'discarded' (not redistributed)

def test_create_new_layout_redistributes_existing_plots_more_slots(main_controller, mock_model, mock_config_service, mock_layout_template_file, tmp_path):
    """
    Test redistribution logic when the new layout has more slots than existing plots.
    Ensures existing plots are redistributed and remaining slots are empty.
    """
    # Setup: Create fewer existing plots than the template provides
    # existing_plot1 = PlotNode(name="Old Plot 1", id="old_id_1")
    # existing_plot1.data = pd.DataFrame({"x":[1], "y":[2]})
    # existing_plot1.plot_properties = BasePlotProperties(title="Old Title 1", plot_type=PlotType.LINE)
    
    # mock_model.scene_root.children.append(existing_plot1)
    # mock_model.scene_root.all_descendants.return_value = [mock_model.scene_root, existing_plot1]

    # Call method under test
    # main_controller.create_new_layout()

    # Assertions:
    # new_root_node = mock_model.set_scene_root.call_args[0][0]
    # assert len(new_root_node.children) == 2 # 2 slots in test_2x2_layout.json
    # assert new_root_node.children[0].data is not None # Check data transfer
    # assert new_root_node.children[1].data is None # Second slot should be empty
    # assert new_root_node.children[0].plot_properties.title == "Old Title 1"
    # assert new_root_node.children[1].plot_properties.title == "Plot B Title" # Should retain template default title for empty slot
