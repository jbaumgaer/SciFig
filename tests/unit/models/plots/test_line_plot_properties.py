from src.models.plots.plot_properties import AxesLimits, LinePlotProperties, PlotMapping
from src.models.plots.plot_types import ArtistType


class TestLinePlotProperties:
    def test_line_plot_properties_initialization_defaults(self):
        """
        Test that LinePlotProperties initializes with default values inherited from BasePlotProperties.
        """
        props = LinePlotProperties()
        assert props.title == ""
        assert props.xlabel == ""
        assert props.ylabel == ""
        assert isinstance(props.plot_mapping, PlotMapping)
        assert props.plot_mapping.x is None
        assert props.plot_mapping.y == []
        assert isinstance(props.axes_limits, AxesLimits)
        assert props.axes_limits.xlim == (None, None)
        assert props.axes_limits.ylim == (None, None)
        assert props.plot_type == ArtistType.LINE

    def test_line_plot_properties_initialization_with_custom_base_values(self):
        """
        Test that LinePlotProperties initializes correctly with provided custom values for base properties.
        """
        custom_mapping = PlotMapping(x="time", y=["temp"])
        custom_limits = AxesLimits(xlim=(0, 10), ylim=(20, 30))
        props = LinePlotProperties(
            title="Temp Over Time",
            xlabel="Time (s)",
            ylabel="Temperature (C)",
            plot_mapping=custom_mapping,
            axes_limits=custom_limits,
            plot_type=ArtistType.LINE,  # Explicitly set, though it's the default
        )
        assert props.title == "Temp Over Time"
        assert props.xlabel == "Time (s)"
        assert props.ylabel == "Temperature (C)"
        assert props.plot_mapping is custom_mapping
        assert props.axes_limits is custom_limits
        assert props.plot_type == ArtistType.LINE

    def test_line_plot_properties_update_from_dict(self):
        """
        Test that update_from_dict on LinePlotProperties behaves as in BasePlotProperties.
        """
        props = LinePlotProperties()
        data = {
            "title": "Updated Line Title",
            "xlabel": "Updated X",
            "plot_mapping": {"x": "data_x_col", "y": ["data_y_col"]},
        }
        props.update_from_dict(data)

        assert props.title == "Updated Line Title"
        assert props.xlabel == "Updated X"
        assert props.ylabel == ""  # Unchanged
        assert props.plot_mapping.x == "data_x_col"
        assert props.plot_mapping.y == ["data_y_col"]
        assert props.plot_type == ArtistType.LINE  # Unchanged
