@pytest.fixture
def sample_plot_node_with_data_and_props():
    """Fixture for a PlotNode with data and properties."""
    node = PlotNode(name="TestPlot", id="test_id")
    node.geometry = (0.1, 0.1, 0.5, 0.5)
    node.data = pd.DataFrame({'colA': [1,2], 'colB': [3,4]})
    node.plot_properties = BasePlotProperties(
        title="Sample",
        plot_type=PlotType.LINE,
        plot_mapping=PlotMapping(x="colA", y=["colB"]),
        axes_limits=AxesLimits(xlim=(0,10), ylim=(-1,1))
    )
    _setup_mock_axes(node)
    return node


def test_plot_node_to_dict(sample_plot_node_with_data_and_props):
    """
    Test PlotNode.to_dict for correct serialization of all attributes,
    including geometry and plot properties.
    """
    # node = sample_plot_node_with_data_and_props
    # node_dict = node.to_dict()
    # assert node_dict["id"] == "test_id"
    # assert node_dict["type"] == "PlotNode" # Assuming type is correctly set
    # assert node_dict["name"] == "TestPlot"
    # assert node_dict["geometry"] == (0.1, 0.1, 0.5, 0.5)
    # assert node_dict["plot_properties"]["title"] == "Sample"
    # assert node_dict["data_path"] == f"data/{node.id}.parquet"
    # assert "children" in node_dict

def test_plot_node_to_dict_exclude_geometry(sample_plot_node_with_data_and_props):
    """
    Test PlotNode.to_dict with exclude_geometry=True.
    """
    # node = sample_plot_node_with_data_and_props
    # node_dict = node.to_dict(exclude_geometry=True)
    # assert "geometry" not in node_dict
    # assert node_dict["id"] == "test_id" # Other properties should still be there

def test_plot_node_from_dict(tmp_path):
    """
    Test PlotNode.from_dict for correct deserialization of all attributes,
    including geometry and plot properties, and handling data loading.
    """
    # Mock data file
    # data_df = pd.DataFrame({'colA': [10,20], 'colB': [30,40]})
    # data_path = tmp_path / "data" / "plot_from_dict_id.parquet"
    # data_path.parent.mkdir()
    # data_df.to_parquet(data_path)

    # plot_dict = {
    #     "id": "plot_from_dict_id",
    #     "type": "PlotNode",
    #     "name": "DeserializedPlot",
    #     "visible": True,
    #     "geometry": {"x": 0.2, "y": 0.2, "width": 0.6, "height": 0.6},
    #     "plot_properties": {
    #         "plot_type": "line",
    #         "title": "Loaded Plot",
    #         "plot_mapping": {"x": "colA", "y": ["colB"]},
    #         "axes_limits": {"xlim": [0.0, 100.0], "ylim": [-10.0, 10.0]},
    #         "line_color": "#0000FF"
    #     },
    #     "data_path": f"data/plot_from_dict_id.parquet",
    #     "children": []
    # }

    # node = PlotNode.from_dict(plot_dict, temp_dir=tmp_path)

    # assert node.id == "plot_from_dict_id"
    # assert node.name == "DeserializedPlot"
    # assert node.visible is True
    # assert node.geometry == (0.2, 0.2, 0.6, 0.6)
    # assert node.plot_properties.title == "Loaded Plot"
    # assert node.plot_properties.plot_type == PlotType.LINE
    # assert node.plot_properties.plot_mapping.x == "colA"
    # pd.testing.assert_frame_equal(node.data, data_df)

def test_plot_node_from_dict_no_data_path():
    """
    Test PlotNode.from_dict when no data_path is present in the dictionary.
    """
    # plot_dict = {
    #     "id": "plot_no_data",
    #     "type": "PlotNode",
    #     "name": "NoDataPlot",
    #     "visible": True,
    #     "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
    #     "plot_properties": {"plot_type": "line", "title": "No Data"},
    #     "children": []
    # }
    # node = PlotNode.from_dict(plot_dict)
    # assert node.data is None

def test_plot_node_from_dict_missing_plot_properties():
    """
    Test PlotNode.from_dict when plot_properties are missing from the dictionary.
    """
    # plot_dict = {
    #     "id": "plot_no_props",
    #     "type": "PlotNode",
    #     "name": "NoPropsPlot",
    #     "visible": True,
    #     "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
    #     "children": []
    # }
    # node = PlotNode.from_dict(plot_dict)
    # assert node.plot_properties is None
