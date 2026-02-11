from src.models.plots.plot_properties import (
    AxesLimits,
    PlotMapping,
    ScatterPlotProperties,
)
from src.models.plots.plot_types import PlotType


class TestScatterPlotProperties:
    def test_scatter_plot_properties_initialization_defaults(self):
        """
        Test that ScatterPlotProperties initializes with default marker_size and
        inherited default values from BasePlotProperties.
        """
        props = ScatterPlotProperties()
        assert props.title == ""
        assert props.xlabel == ""
        assert props.ylabel == ""
        assert isinstance(props.plot_mapping, PlotMapping)
        assert props.plot_mapping.x is None
        assert props.plot_mapping.y == []
        assert isinstance(props.axes_limits, AxesLimits)
        assert props.axes_limits.xlim == (None, None)
        assert props.axes_limits.ylim == (None, None)
        assert props.plot_type == PlotType.SCATTER  # Default for ScatterPlotProperties
        assert props.marker_size == 10

    def test_scatter_plot_properties_initialization_custom_marker_size(self):
        """
        Test that ScatterPlotProperties initializes correctly with a custom marker_size.
        """
        props = ScatterPlotProperties(marker_size=25)
        assert props.marker_size == 25
        assert props.plot_type == PlotType.SCATTER  # Still default

    def test_scatter_plot_properties_initialization_with_custom_base_and_scatter_values(
        self,
    ):
        """
        Test that ScatterPlotProperties initializes correctly with provided custom values
        for both base properties and marker_size.
        """
        custom_mapping = PlotMapping(x="x_data", y=["y_data"])
        custom_limits = AxesLimits(xlim=(0, 50), ylim=(-2, 2))
        props = ScatterPlotProperties(
            title="Custom Scatter Plot",
            xlabel="Data X",
            ylabel="Data Y",
            plot_mapping=custom_mapping,
            axes_limits=custom_limits,
            plot_type=PlotType.SCATTER,  # Explicitly set
            marker_size=30,
        )
        assert props.title == "Custom Scatter Plot"
        assert props.xlabel == "Data X"
        assert props.ylabel == "Data Y"
        assert props.plot_mapping is custom_mapping
        assert props.axes_limits is custom_limits
        assert props.plot_type == PlotType.SCATTER
        assert props.marker_size == 30

    def test_scatter_plot_properties_update_from_dict_marker_size(self):
        """
        Test that update_from_dict correctly updates the marker_size property.
        """
        props = ScatterPlotProperties(marker_size=10)
        data = {"marker_size": 20}
        props.update_from_dict(data)
        assert props.marker_size == 20

    def test_scatter_plot_properties_update_from_dict_inherited_properties(self):
        """
        Test that update_from_dict on ScatterPlotProperties also updates
        inherited properties from BasePlotProperties.
        """
        props = ScatterPlotProperties(title="Original", marker_size=10)
        data = {
            "title": "Updated Scatter Title",
            "xlabel": "X Axis",
            "plot_mapping": {"x": "source_x", "y": ["source_y"]},
            "marker_size": 15,
        }
        props.update_from_dict(data)

        assert props.title == "Updated Scatter Title"
        assert props.xlabel == "X Axis"
        assert props.plot_mapping.x == "source_x"
        assert props.marker_size == 15
        assert props.plot_type == PlotType.SCATTER  # Remains Scatter
