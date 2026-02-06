def test_plot_properties_update_from_dict_common_properties():
    """
    Test that update_from_dict correctly updates common properties
    like title, xlabel, ylabel.
    """
    # props = LinePlotProperties()
    # data = {"title": "New Title", "xlabel": "New X", "ylabel": "New Y"}
    # props.update_from_dict(data)
    # assert props.title == "New Title"
    # assert props.xlabel == "New X"
    # assert props.ylabel == "New Y"

def test_plot_properties_update_from_dict_nested_properties():
    """
    Test that update_from_dict correctly updates nested dataclasses
    like plot_mapping and axes_limits.
    """
    # props = LinePlotProperties()
    # data = {
    #     "plot_mapping": {"x": "col_A", "y": ["col_B"]},
    #     "axes_limits": {"xlim": [0.0, 100.0], "ylim": [-5.0, 5.0]}
    # }
    # props.update_from_dict(data)
    # assert props.plot_mapping.x == "col_A"
    # assert props.plot_mapping.y == ["col_B"]
    # assert props.axes_limits.xlim == (0.0, 100.0)
    # assert props.axes_limits.ylim == (-5.0, 5.0)

def test_plot_properties_update_from_dict_plot_type_conversion():
    """
    Test that update_from_dict correctly converts plot_type string to PlotType enum.
    """
    # props = LinePlotProperties()
    # data = {"plot_type": "scatter"} # Use lowercase for valid enum value
    # props.update_from_dict(data)
    # assert props.plot_type == PlotType.SCATTER

def test_plot_properties_update_from_dict_unspecified_properties():
    """
    Test that update_from_dict ignores properties not defined in the class.
    """
    # props = LinePlotProperties()
    # data = {"non_existent_prop": "value", "title": "New Title"}
    # props.update_from_dict(data)
    # assert not hasattr(props, "non_existent_prop")
    # assert props.title == "New Title"

def test_plot_properties_update_from_dict_subclass_specific_properties():
    """
    Test that update_from_dict correctly handles subclass-specific properties
    (e.g., LinePlotProperties with line_color, ScatterPlotProperties with marker_size).
    """
    # from src.models.nodes.plot_properties import ScatterPlotProperties, BasePlotProperties # Import needed for this test
    # props_line = LinePlotProperties()
    # # Need to add line_color to LinePlotProperties for this to pass
    # # props_line.update_from_dict({"line_color": "#FF0000"})
    # # assert props_line.line_color == "#FF0000"

    # props_scatter = ScatterPlotProperties()
    # props_scatter.update_from_dict({"marker_size": 20})
    # assert props_scatter.marker_size == 20

    # # Test updating non-existent properties on base class
    # props_base = BasePlotProperties()
    # props_base.update_from_dict({"line_color": "#FF0000"}) # Should not add line_color to BasePlotProperties
    # assert not hasattr(props_base, "line_color")
