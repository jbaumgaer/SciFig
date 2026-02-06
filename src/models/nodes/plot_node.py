import dataclasses
import logging
from pathlib import Path
from typing import Optional

import matplotlib.axes
import pandas as pd

from src.models.plots.plot_properties import (
    AxesLimits,
    BasePlotProperties,
    PlotMapping,
    PlotType,
)
from src.models.nodes.scene_node import SceneNode


class PlotNode(SceneNode):
    """
    A scene node representing a single Matplotlib Axes (a subplot).
    """

    def __init__(
        self, parent: SceneNode | None = None, name: str = "Plot", id: str | None = None
    ):
        super().__init__(parent, name, id)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"PlotNode initialized: {self.name} (ID: {self.id})")


        # Properties migrated from the old ArtistModel
        self.geometry: tuple[float, float, float, float] = (0.1, 0.1, 0.8, 0.8)
        self.plot_properties: Optional[BasePlotProperties] = None
        self.data: pd.DataFrame | None = None
        self.axes: matplotlib.axes.Axes | None = None # Store the Matplotlib Axes object

    def hit_test(self, position: tuple[float, float]) -> SceneNode | None:
        """
        Checks if the given position (in figure coordinates, 0-1) is within
        the bounds of this plot's *rendered* axes.
        """
        if self.axes is None:
            self.logger.debug(f"Hit test for {self.name} (ID: {self.id}): No axes to hit test against.")
            return None # No axes to hit test against yet

        x, y = position

        # Get the bounding box of the axes in figure coordinates
        # Bbox is in display coordinates, so transform it to figure coordinates
        bbox = self.axes.get_window_extent().transformed(self.axes.figure.transFigure.inverted())

        if bbox.x0 <= x <= bbox.x1 and bbox.y0 <= y <= bbox.y1:
            self.logger.debug(f"Hit test for {self.name} (ID: {self.id}): Hit at position ({x}, {y}).")
            return self
        self.logger.debug(f"Hit test for {self.name} (ID: {self.id}): Miss at position ({x}, {y}). Bbox: {bbox}")
        return None

    def to_dict(self, exclude_geometry: bool = False) -> dict:
        """Serializes the plot node to a dictionary."""
        node_dict = super().to_dict()

        data_path = f"data/{self.id}.parquet" if self.data is not None else None

        # Exclude geometry if requested
        if not exclude_geometry:
            node_dict["geometry"] = self.geometry

        node_dict.update(
            {
                "plot_properties": (
                    dataclasses.asdict(self.plot_properties)
                    if self.plot_properties
                    else None
                ),
                "data_path": data_path,
            }
        )
        self.logger.debug(f"PlotNode '{self.name}' (ID: {self.id}) serialized to dict. Exclude geometry: {exclude_geometry}")
        return node_dict

    @classmethod
    def from_dict(
        cls, data: dict, parent: SceneNode | None = None, temp_dir: Path | None = None
    ) -> "PlotNode":
        """Creates a PlotNode from a dictionary."""
        node = super().from_dict(data, parent)
        # Correctly extract geometry from the dictionary
        geometry_dict = data["geometry"]
        node.geometry = (
            geometry_dict.get("x", 0.0),
            geometry_dict.get("y", 0.0),
            geometry_dict.get("width", 1.0),
            geometry_dict.get("height", 1.0)
        )
        node.logger.debug(f"PlotNode.from_dict: Geometry extracted: {node.geometry}")


        props_data = data.get("plot_properties")
        if props_data:
            node.logger.debug(f"PlotNode.from_dict: Deserializing plot properties for '{node.name}'.")
            # We need to reconstruct nested dataclasses manually
            mapping_data = props_data.get("plot_mapping", {})
            props_data["plot_mapping"] = PlotMapping(
                x=mapping_data.get("x"),
                y=mapping_data.get("y", [])
            )
            limits_data = props_data.get("axes_limits", {})
            props_data["axes_limits"] = AxesLimits(
                xlim=limits_data.get("xlim", (None, None)),
                ylim=limits_data.get("ylim", (None, None))
            )

            # Determine the correct property class based on 'plot_type'
            plot_type_str = props_data.get("plot_type", "line") # Use lowercase default
            plot_type = PlotType(plot_type_str)
            node.logger.debug(f"PlotNode.from_dict: Determined plot_type: {plot_type}")

            # Create the properties object using the factory method
            node.plot_properties = BasePlotProperties.create_properties_from_plot_type(
                plot_type
            )
            # Now update it from the dict, allowing the update_from_dict to handle specific properties
            node.plot_properties.update_from_dict(props_data)
            node.logger.debug(f"Plot properties for '{node.name}' updated from dict.")

        data_path = data.get("data_path")
        if data_path and temp_dir:
            full_path = temp_dir / data_path
            if full_path.exists():
                node.data = pd.read_parquet(full_path)
                node.logger.debug(f"PlotNode '{node.name}' loaded data from {full_path}.")
            else:
                node.logger.warning(f"PlotNode '{node.name}': Data file not found at {full_path}. Data not loaded.")
        elif data_path:
            node.logger.debug(f"PlotNode '{node.name}': Data path {data_path} specified, but temp_dir not provided. Data not loaded.")
        else:
            node.logger.debug(f"PlotNode '{node.name}': No data path specified.")


        return node
