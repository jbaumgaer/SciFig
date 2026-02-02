from src.models.nodes.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
)


def test_plot_properties_creation():
    """Test that a PlotProperties object can be created with valid data."""
    plot_mapping = PlotMapping(x="time", y=["temp"])
    axes_limits = AxesLimits(xlim=(0, 10), ylim=(-5, 5))
    props = LinePlotProperties(
        title="Test Title",
        xlabel="Time",
        ylabel="Temperature",
        plot_mapping=plot_mapping,
        axes_limits=axes_limits,
    )
    assert props.title == "Test Title"
    assert props.xlabel == "Time"
    assert props.ylabel == "Temperature"
    assert props.plot_mapping == plot_mapping
    assert props.axes_limits == axes_limits


def test_plot_properties_equality():
    """Test that two PlotProperties objects with the same values are equal."""
    plot_mapping1 = PlotMapping(x="time", y=["temp"])
    axes_limits1 = AxesLimits(xlim=(0, 10), ylim=(-5, 5))
    props1 = LinePlotProperties(
        title="Test Title",
        xlabel="Time",
        ylabel="Temperature",
        plot_mapping=plot_mapping1,
        axes_limits=axes_limits1,
    )

    plot_mapping2 = PlotMapping(x="time", y=["temp"])
    axes_limits2 = AxesLimits(xlim=(0, 10), ylim=(-5, 5))
    props2 = LinePlotProperties(
        title="Test Title",
        xlabel="Time",
        ylabel="Temperature",
        plot_mapping=plot_mapping2,
        axes_limits=axes_limits2,
    )

    assert props1 == props2


def test_plot_properties_inequality():
    """Test that two PlotProperties objects with different values are not equal."""
    plot_mapping1 = PlotMapping(x="time", y=["temp"])
    axes_limits1 = AxesLimits(xlim=(0, 10), ylim=(-5, 5))
    props1 = LinePlotProperties(
        title="Test Title",
        xlabel="Time",
        ylabel="Temperature",
        plot_mapping=plot_mapping1,
        axes_limits=axes_limits1,
    )

    plot_mapping2 = PlotMapping(x="time", y=["temp"])
    axes_limits2 = AxesLimits(xlim=(0, 10), ylim=(-5, 5))
    props2 = LinePlotProperties(
        title="Different Title",
        xlabel="Time",
        ylabel="Temperature",
        plot_mapping=plot_mapping2,
        axes_limits=axes_limits2,
    )

    assert props1 != props2
