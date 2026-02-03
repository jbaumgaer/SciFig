import pandas as pd
from matplotlib.figure import Figure

from src.models.application_model import ApplicationModel
from src.models.nodes import SceneNode, GroupNode, PlotNode
from src.models.nodes.plot_properties import LinePlotProperties


def test_scene_node_to_dict():
    """Tests the serialization of a basic SceneNode."""
    node = SceneNode(name="TestNode")
    node_dict = node.to_dict()

    assert node_dict["id"] == node.id
    assert node_dict["class_name"] == "SceneNode"
    assert node_dict["name"] == "TestNode"
    assert node_dict["visible"] is True
    assert node_dict["children"] == []


def test_group_node_to_dict():
    """Tests the serialization of a GroupNode with children."""
    root = GroupNode(name="root")
    child1 = SceneNode(parent=root, name="child1")
    child2 = SceneNode(parent=root, name="child2")

    root_dict = root.to_dict()

    assert root_dict["class_name"] == "GroupNode"
    assert len(root_dict["children"]) == 2
    assert root_dict["children"][0]["name"] == "child1"
    assert root_dict["children"][1]["name"] == "child2"


def test_plot_node_to_dict_without_data():
    """Tests the serialization of a PlotNode without data."""
    node = PlotNode(name="My Plot")
    node.geometry = (0.1, 0.1, 0.8, 0.8)
    node.plot_properties = LinePlotProperties(title="My Title")
    
    node_dict = node.to_dict()

    assert node_dict["class_name"] == "PlotNode"
    assert node_dict["name"] == "My Plot"
    assert node_dict["geometry"] == (0.1, 0.1, 0.8, 0.8)
    assert node_dict["plot_properties"]["title"] == "My Title"
    assert node_dict["data_path"] is None


def test_plot_node_to_dict_with_data():
    """Tests the serialization of a PlotNode with data."""
    node = PlotNode(name="My Data Plot")
    node.data = pd.DataFrame({"x": [1, 2], "y": [3, 4]})

    node_dict = node.to_dict()

    assert node_dict["class_name"] == "PlotNode"
    assert node_dict["data_path"] == f"data/{node.id}.parquet"


def test_application_model_to_dict():
    """Tests the serialization of the entire ApplicationModel."""
    fig = Figure()
    model = ApplicationModel(figure=fig)
    
    # Add some nodes to the model
    group = GroupNode(parent=model.scene_root, name="My Group")
    plot = PlotNode(parent=group, name="My Plot")
    
    model_dict = model.to_dict()

    assert model_dict["version"] == "1.0"
    assert "scene_root" in model_dict
    
    root_dict = model_dict["scene_root"]
    assert root_dict["name"] == "root"
    assert len(root_dict["children"]) == 1
    
    group_dict = root_dict["children"][0]
    assert group_dict["name"] == "My Group"
    assert len(group_dict["children"]) == 1

    plot_dict = group_dict["children"][0]
    assert plot_dict["name"] == "My Plot"
