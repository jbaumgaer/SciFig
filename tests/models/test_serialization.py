import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from matplotlib.figure import Figure

from src.models.application_model import ApplicationModel
from src.models.nodes import SceneNode, GroupNode, PlotNode
from src.models.nodes.plot_properties import AxesLimits, LinePlotProperties, PlotMapping
from src.models.nodes.scene_node import node_factory


def test_scene_node_to_dict():
    """Tests the serialization of a basic SceneNode."""
    node = SceneNode(name="TestNode")
    node_dict = node.to_dict()

    assert node_dict["id"] == node.id
    assert node_dict["class_name"] == "SceneNode"
    assert node_dict["name"] == "TestNode"
    assert node_dict["visible"] is True
    assert node_dict["children"] == []


def test_scene_node_from_dict():
    """Tests the deserialization of a basic SceneNode."""
    data = {
        "id": "12345",
        "class_name": "SceneNode",
        "name": "LoadedNode",
        "visible": False,
        "children": [],
    }
    node = SceneNode.from_dict(data)

    assert node.id == "12345"
    assert node.name == "LoadedNode"
    assert node.visible is False
    assert node.children == []


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


def test_group_node_from_dict():
    """Tests the deserialization of a GroupNode."""
    data = {
        "id": "group1",
        "class_name": "GroupNode",
        "name": "LoadedGroup",
        "visible": True,
        "children": [],
    }
    node = GroupNode.from_dict(data)

    assert node.id == "group1"
    assert node.name == "LoadedGroup"
    assert node.visible is True
    assert node.children == []


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


def test_plot_node_from_dict_without_data():
    """Tests the deserialization of a PlotNode without data."""
    data = {
        "id": "plot1",
        "class_name": "PlotNode",
        "name": "LoadedPlot",
        "visible": True,
        "geometry": [0.1, 0.1, 0.8, 0.8],
        "plot_properties": {
            "title": "Loaded Title",
            "xlabel": "X",
            "ylabel": "Y",
            "plot_type": "line",
            "plot_mapping": {"x": "colX", "y": ["colY"]},
            "axes_limits": {"xlim": [None, None], "ylim": [0.0, 10.0]},
        },
        "data_path": None,
        "children": [],
    }
    node = PlotNode.from_dict(data)

    assert node.id == "plot1"
    assert node.name == "LoadedPlot"
    assert node.geometry == (0.1, 0.1, 0.8, 0.8)
    assert node.plot_properties.title == "Loaded Title"
    assert node.data is None


def test_plot_node_from_dict_with_data():
    """Tests the deserialization of a PlotNode with data from a parquet file."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        data_dir = temp_dir / "data"
        data_dir.mkdir()

        # Create dummy parquet file
        dummy_df = pd.DataFrame({"x": [10, 20], "y": [30, 40]})
        plot_id = "plot_with_data_id"
        dummy_parquet_path = data_dir / f"{plot_id}.parquet"
        dummy_df.to_parquet(dummy_parquet_path)

        data = {
            "id": plot_id,
            "class_name": "PlotNode",
            "name": "LoadedPlotWithData",
            "visible": True,
            "geometry": [0.1, 0.1, 0.8, 0.8],
            "plot_properties": None,
            "data_path": f"data/{plot_id}.parquet",
            "children": [],
        }
        node = PlotNode.from_dict(data, temp_dir=temp_dir)

        assert node.id == plot_id
        assert node.name == "LoadedPlotWithData"
        assert node.data is not None
        pd.testing.assert_frame_equal(node.data, dummy_df)


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


def test_application_model_load_from_dict():
    """Tests loading the ApplicationModel from a dictionary."""
    fig = Figure()
    model = ApplicationModel(figure=fig)

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        data_dir = temp_dir / "data"
        data_dir.mkdir()

        # Create dummy parquet file for a plot
        dummy_df = pd.DataFrame({"val": [1, 2]})
        plot_id = "plot_in_model"
        dummy_parquet_path = data_dir / f"{plot_id}.parquet"
        dummy_df.to_parquet(dummy_parquet_path)

        # Create a sample project dictionary
        project_data = {
            "version": "1.0",
            "scene_root": {
                "id": "root_id",
                "class_name": "GroupNode",
                "name": "root",
                "visible": True,
                "children": [
                    {
                        "id": "group_id",
                        "class_name": "GroupNode",
                        "name": "Loaded Group",
                        "visible": True,
                        "children": [
                            {
                                "id": plot_id,
                                "class_name": "PlotNode",
                                "name": "Loaded Plot",
                                "visible": True,
                                "geometry": [0.1, 0.1, 0.8, 0.8],
                                "plot_properties": None,
                                "data_path": f"data/{plot_id}.parquet",
                                "children": [],
                            }
                        ],
                    }
                ],
            },
        }

        model.load_from_dict(project_data, temp_dir)

        assert model.scene_root.name == "root"
        assert len(model.scene_root.children) == 1
        
        loaded_group = model.scene_root.children[0]
        assert isinstance(loaded_group, GroupNode)
        assert loaded_group.name == "Loaded Group"
        assert len(loaded_group.children) == 1

        loaded_plot = loaded_group.children[0]
        assert isinstance(loaded_plot, PlotNode)
        assert loaded_plot.id == plot_id
        assert loaded_plot.name == "Loaded Plot"
        assert loaded_plot.data is not None
        pd.testing.assert_frame_equal(loaded_plot.data, dummy_df)
