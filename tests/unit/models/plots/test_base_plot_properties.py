import pytest
from src.models.plots.plot_properties import BasePlotProperties, PlotMapping, AxesLimits, LinePlotProperties, ScatterPlotProperties
from src.models.plots.plot_types import PlotType

class TestBasePlotProperties:
    def test_base_plot_properties_initialization_defaults(self):
        """
        Test that BasePlotProperties initializes with default values.
        """
        props = BasePlotProperties()
        assert props.title == ""
        assert props.xlabel == ""
        assert props.ylabel == ""
        assert isinstance(props.plot_mapping, PlotMapping)
        assert props.plot_mapping.x is None
        assert props.plot_mapping.y == []
        assert isinstance(props.axes_limits, AxesLimits)
        assert props.axes_limits.xlim == (None, None)
        assert props.axes_limits.ylim == (None, None)
        assert props.plot_type == PlotType.LINE

    def test_base_plot_properties_initialization_with_custom_values(self):
        """
        Test that BasePlotProperties initializes correctly with provided values.
        """
        custom_mapping = PlotMapping(x="time", y=["data"])
        custom_limits = AxesLimits(xlim=(0, 10), ylim=(-1, 1))
        props = BasePlotProperties(
            title="Custom Title",
            xlabel="Custom X",
            ylabel="Custom Y",
            plot_mapping=custom_mapping,
            axes_limits=custom_limits,
            plot_type=PlotType.SCATTER
        )
        assert props.title == "Custom Title"
        assert props.xlabel == "Custom X"
        assert props.ylabel == "Custom Y"
        assert props.plot_mapping is custom_mapping
        assert props.axes_limits is custom_limits
        assert props.plot_type == PlotType.SCATTER

    def test_base_plot_properties_update_from_dict_common_properties(self):
        """
        Test that update_from_dict correctly updates common properties
        like title, xlabel, ylabel.
        """
        props = BasePlotProperties()
        data = {"title": "New Title", "xlabel": "New X", "ylabel": "New Y"}
        props.update_from_dict(data)
        assert props.title == "New Title"
        assert props.xlabel == "New X"
        assert props.ylabel == "New Y"
        assert props.plot_type == PlotType.LINE # Should remain default

    def test_base_plot_properties_update_from_dict_nested_properties(self):
        """
        Test that update_from_dict correctly updates nested dataclasses
        like plot_mapping and axes_limits.
        """
        props = BasePlotProperties()
        data = {
            "plot_mapping": {"x": "col_A", "y": ["col_B"]},
            "axes_limits": {"xlim": (0.0, 100.0), "ylim": (-5.0, 5.0)}
        }
        props.update_from_dict(data)
        assert props.plot_mapping.x == "col_A"
        assert props.plot_mapping.y == ["col_B"]
        assert props.axes_limits.xlim == (0.0, 100.0)
        assert props.axes_limits.ylim == (-5.0, 5.0)

    def test_base_plot_properties_update_from_dict_plot_type_conversion(self):
        """
        Test that update_from_dict correctly converts plot_type string to PlotType enum.
        """
        props = BasePlotProperties()
        data = {"plot_type": "scatter"}
        props.update_from_dict(data)
        assert props.plot_type == PlotType.SCATTER

    def test_base_plot_properties_update_from_dict_unspecified_properties(self):
        """
        Test that update_from_dict ignores properties not defined in the class.
        """
        props = BasePlotProperties()
        data = {"non_existent_prop": "value", "title": "New Title"}
        props.update_from_dict(data)
        assert not hasattr(props, "non_existent_prop")
        assert props.title == "New Title"
        assert props.plot_type == PlotType.LINE # Should remain default

    def test_base_plot_properties_update_from_dict_nested_partial_update(self):
        """
        Test that partial updates to nested PlotMapping and AxesLimits work correctly.
        """
        props = BasePlotProperties()
        props.plot_mapping.x = "initial_x"
        props.plot_mapping.y = ["initial_y"]
        props.axes_limits.xlim = (10, 20)
        props.axes_limits.ylim = (-10, 10)

        data = {
            "plot_mapping": {"x": "updated_x"},
            "axes_limits": {"ylim": (-5, 5)}
        }
        props.update_from_dict(data)

        assert props.plot_mapping.x == "updated_x"
        assert props.plot_mapping.y == ["initial_y"] # Should remain unchanged
        assert props.axes_limits.xlim == (10, 20) # Should remain unchanged
        assert props.axes_limits.ylim == (-5, 5)

    @pytest.mark.parametrize("new_plot_type, expected_class", [
        (PlotType.LINE, LinePlotProperties),
        (PlotType.SCATTER, ScatterPlotProperties)
    ])
    def test_create_properties_from_plot_type_no_current_properties(self, new_plot_type, expected_class):
        """
        Test create_properties_from_plot_type when no current_properties are provided.
        """
        new_props = BasePlotProperties.create_properties_from_plot_type(new_plot_type)
        assert isinstance(new_props, expected_class)
        assert new_props.plot_type == new_plot_type
        # Ensure default values are set
        assert new_props.title == ""
        assert new_props.plot_mapping.x is None

    def test_create_properties_from_plot_type_with_existing_line_to_scatter(self):
        """
        Test converting from LinePlotProperties to ScatterPlotProperties,
        transferring common properties and marker_size if applicable.
        """
        current_props = LinePlotProperties(
            title="Line Title",
            xlabel="Line X",
            plot_mapping=PlotMapping(x="data_x", y=["data_y"]),
            axes_limits=AxesLimits(xlim=(0, 10), ylim=(0, 20))
        )
        new_props = BasePlotProperties.create_properties_from_plot_type(
            PlotType.SCATTER,
            current_properties=current_props
        )

        assert isinstance(new_props, ScatterPlotProperties)
        assert new_props.plot_type == PlotType.SCATTER
        assert new_props.title == "Line Title"
        assert new_props.xlabel == "Line X"
        assert new_props.plot_mapping.x == "data_x"
        assert new_props.axes_limits.xlim == (0, 10)
        assert new_props.marker_size == 10 # Default for ScatterPlotProperties

    def test_create_properties_from_plot_type_with_existing_scatter_to_line(self):
        """
        Test converting from ScatterPlotProperties to LinePlotProperties,
        transferring common properties (marker_size should be ignored).
        """
        current_props = ScatterPlotProperties(
            title="Scatter Title",
            ylabel="Scatter Y",
            plot_mapping=PlotMapping(x="other_x", y=["other_y"]),
            marker_size=25
        )
        new_props = BasePlotProperties.create_properties_from_plot_type(
            PlotType.LINE,
            current_properties=current_props
        )

        assert isinstance(new_props, LinePlotProperties)
        assert new_props.plot_type == PlotType.LINE
        assert new_props.title == "Scatter Title"
        assert new_props.ylabel == "Scatter Y"
        assert new_props.plot_mapping.x == "other_x"
        assert not hasattr(new_props, "marker_size") # LinePlotProperties does not have marker_size

    def test_create_properties_from_plot_type_with_existing_same_type(self):
        """
        Test creating properties of the same type, ensuring properties are transferred.
        """
        current_props = LinePlotProperties(
            title="Original Title",
            xlabel="Original X",
            plot_mapping=PlotMapping(x="x_val", y=["y_val"])
        )
        new_props = BasePlotProperties.create_properties_from_plot_type(
            PlotType.LINE,
            current_properties=current_props
        )
        assert isinstance(new_props, LinePlotProperties)
        assert new_props.title == "Original Title"
        assert new_props.xlabel == "Original X"
        assert new_props.plot_mapping.x == "x_val"
        assert new_props.plot_type == PlotType.LINE

    def test_create_properties_from_plot_type_with_existing_scatter_to_scatter_with_marker_size(self):
        """
        Test creating ScatterPlotProperties from existing ScatterPlotProperties,
        ensuring marker_size is transferred.
        """
        current_props = ScatterPlotProperties(
            title="Original Scatter",
            marker_size=30,
            plot_mapping=PlotMapping(x="sx", y=["sy"])
        )
        new_props = BasePlotProperties.create_properties_from_plot_type(
            PlotType.SCATTER,
            current_properties=current_props
        )
        assert isinstance(new_props, ScatterPlotProperties)
        assert new_props.title == "Original Scatter"
        assert new_props.plot_mapping.x == "sx"
        assert new_props.marker_size == 30
        assert new_props.plot_type == PlotType.SCATTER
