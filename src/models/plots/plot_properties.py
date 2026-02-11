from dataclasses import dataclass, field
from typing import Optional, Type

from src.models.plots.plot_types import PlotType


@dataclass
class PlotMapping:
    x: Optional[str]
    y: list[str]

    def update_from_dict(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


@dataclass
class AxesLimits:
    xlim: tuple[Optional[float], Optional[float]]
    ylim: tuple[Optional[float], Optional[float]]

    def update_from_dict(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


@dataclass
class BasePlotProperties:
    """
    Base class for plot properties. It contains properties that are common
    to all plot types.
    """

    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    plot_mapping: PlotMapping = field(default_factory=lambda: PlotMapping(x=None, y=[]))
    axes_limits: AxesLimits = field(
        default_factory=lambda: AxesLimits(xlim=(None, None), ylim=(None, None))
    )
    plot_type: PlotType = PlotType.LINE

    def update_from_dict(self, data: dict, exclude_geometry: bool = False):
        """
        Updates the properties of this object from a dictionary,
        optionally excluding geometry-related properties (if any exist in subclasses).
        """
        for key, value in data.items():
            # geometry is not part of BasePlotProperties
            if hasattr(self, key):
                current_attr = getattr(self, key)
                if isinstance(current_attr, (PlotMapping, AxesLimits)) and isinstance(
                    value, dict
                ):
                    current_attr.update_from_dict(value)
                elif key == "plot_type":
                    setattr(self, key, PlotType(value))
                else:
                    setattr(self, key, value)

    @staticmethod
    def create_properties_from_plot_type(
        new_plot_type: PlotType,
        current_properties: Optional["BasePlotProperties"] = None,
    ) -> "BasePlotProperties":
        """
        Creates a new PlotProperties object of the specified type,
        transferring common properties from an existing object if provided.
        """
        target_class = PLOT_TYPE_TO_PROPERTY_CLASS[new_plot_type]
        if current_properties:
            # Transfer common properties
            common_kwargs = {
                "title": current_properties.title,
                "xlabel": current_properties.xlabel,
                "ylabel": current_properties.ylabel,
                "plot_mapping": current_properties.plot_mapping,
                "axes_limits": current_properties.axes_limits,
                "plot_type": new_plot_type,
            }
            # Add specific properties if they exist in current_properties and target_class
            if new_plot_type == PlotType.SCATTER and isinstance(
                current_properties, ScatterPlotProperties
            ):
                common_kwargs["marker_size"] = current_properties.marker_size

            return target_class(**common_kwargs)
        else:
            return target_class(plot_type=new_plot_type)


@dataclass
class LinePlotProperties(BasePlotProperties):
    """Properties specific to a line plot."""

    pass


@dataclass
class ScatterPlotProperties(BasePlotProperties):
    """Properties specific to a scatter plot."""

    marker_size: int = 10  # TODO: Move into config
    plot_type: PlotType = PlotType.SCATTER


# Mapping of PlotType enum to their respective Property classes
PLOT_TYPE_TO_PROPERTY_CLASS: dict[PlotType, Type[BasePlotProperties]] = {
    PlotType.LINE: LinePlotProperties,
    PlotType.SCATTER: ScatterPlotProperties,
}
