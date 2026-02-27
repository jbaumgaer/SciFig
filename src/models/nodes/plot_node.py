import dataclasses
import logging
from pathlib import Path
from typing import Optional

import matplotlib.axes
import pandas as pd

from src.models.nodes.scene_node import SceneNode
from src.models.plots.plot_properties import (
    ArtistType,
    PlotProperties,
)


class PlotNode(SceneNode):
    """
    A scene node representing a single Matplotlib Axes (a subplot).
    """

    def __init__(
        self, parent: Optional[SceneNode] = None, name: str = "Plot", id: Optional[str] = None
    ):
        super().__init__(parent, name, id)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"PlotNode initialized: {self.name} (ID: {self.id})")

        self.geometry: tuple[float, float, float, float] = (
            0.1,
            0.1,
            0.8,
            0.8,
        )  # TODO: This should be set by the layout manager, not hardcoded
        # TODO: Change this from a tuple to a x, y, width, height dataclass for better readability and maintainability
        self.plot_properties: Optional[PlotProperties] = None
        self.data: Optional[pd.DataFrame] = None
        self.axes: Optional[matplotlib.axes.Axes] = None  # Store the Matplotlib Axes object TODO: Is this not already stored in the plot_properties?
        self.data_file_path: Optional[Path] = None  # New attribute

    def hit_test(self, position: tuple[float, float]) -> Optional[SceneNode]:
        """
        Checks if the given position (in figure coordinates, 0-1) is within
        the bounds of this plot's *rendered* axes.
        """
        if self.axes is None:
            self.logger.debug(
                f"Hit test for {self.name} (ID: {self.id}): No axes to hit test against."
            )
            return None  # No axes to hit test against yet

        x, y = position

        # Get the bounding box of the axes in figure coordinates
        # Bbox is in display coordinates, so transform it to figure coordinates
        bbox = self.axes.get_window_extent().transformed(
            self.axes.figure.transFigure.inverted()
        )

        if bbox.x0 <= x <= bbox.x1 and bbox.y0 <= y <= bbox.y1:
            self.logger.debug(
                f"Hit test for {self.name} (ID: {self.id}): Hit at position ({x}, {y})."
            )
            return self
        self.logger.debug(
            f"Hit test for {self.name} (ID: {self.id}): Miss at position ({x}, {y}). Bbox: {bbox}"
        )
        return None

    def to_dict(self, exclude_geometry: bool = False) -> dict:
        """Serializes the plot node to a dictionary."""
        node_dict = super().to_dict()

        # Update data_path serialization to use the new data_file_path attribute
        # data_path = f"data/{self.id}.parquet" if self.data is not None else None # Old line
        data_path_str = str(self.data_file_path) if self.data_file_path else None

        # Exclude geometry if requested
        if not exclude_geometry:
            node_dict["geometry"] = {
                "x": self.geometry[0],
                "y": self.geometry[1],
                "width": self.geometry[2],
                "height": self.geometry[3],
            }

        node_dict.update(
            {
                "plot_properties": (
                    dataclasses.asdict(self.plot_properties)
                    if self.plot_properties
                    else None
                ),
                "data_file_path": data_path_str,  # Updated key and value
            }
        )
        self.logger.debug(
            f"PlotNode '{self.name}' (ID: {self.id}) serialized to dict. Exclude geometry: {exclude_geometry}"
        )
        return node_dict

    @classmethod
    def from_dict(
        cls, data: dict, parent: Optional[SceneNode] = None, temp_dir: Optional[Path] = None
    ) -> "PlotNode":
        """Creates a PlotNode from a dictionary."""
        node = super().from_dict(data, parent)
        # Correctly extract geometry from the dictionary
        geometry_dict = data["geometry"]
        node.geometry = (
            geometry_dict.get("x", 0.0),
            geometry_dict.get("y", 0.0),
            geometry_dict.get("width", 1.0),
            geometry_dict.get("height", 1.0),
        )
        node.logger.debug(f"PlotNode.from_dict: Geometry extracted: {node.geometry}")

        props_data = data.get("plot_properties")
        if props_data:
            node.logger.debug(
                f"PlotNode.from_dict: Deserializing plot properties for '{node.name}'."
            )

            # Determine the correct property class based on 'plot_type'
            plot_type_str = props_data.get("plot_type", "line")  # Use lowercase default
            plot_type = ArtistType(plot_type_str)
            node.logger.debug(f"PlotNode.from_dict: Determined plot_type: {plot_type}")

            # Create the properties object using the factory method
            node.plot_properties = BasePlotProperties.create_properties_from_plot_type(
                plot_type
            )

            # Reconstruct nested dataclasses manually
            mapping_data = props_data.get("plot_mapping", {})
            props_data["plot_mapping"] = PlotMapping(
                x=mapping_data.get("x"), y=mapping_data.get("y", [])
            )
            limits_data = props_data.get("axes_limits", {})
            props_data["axes_limits"] = AxesLimits(
                xlim=tuple(limits_data.get("xlim", (None, None))),
                ylim=tuple(limits_data.get("ylim", (None, None))),
            )

            # Now update it from the dict, allowing the update_from_dict to handle specific properties
            node.plot_properties.update_from_dict(props_data)
            node.logger.debug(f"Plot properties for '{node.name}' updated from dict.")

        # Updated data loading logic to use data_file_path
        data_file_path_str = data.get("data_file_path")
        if data_file_path_str:
            node.data_file_path = Path(data_file_path_str)
            if (
                temp_dir and node.data_file_path.is_absolute()
            ):  # Only load if absolute path is provided and temp_dir is contextually relevant
                full_path = (
                    temp_dir / node.data_file_path.name
                )  # Assuming filename in temp_dir matches
            else:
                full_path = (
                    node.data_file_path
                )  # Assume path is relative to project or absolute in external location

            if full_path.exists():
                node.data = pd.read_parquet(full_path)
                node.logger.debug(
                    f"PlotNode '{node.name}' loaded data from {full_path}."
                )
            else:
                node.logger.warning(
                    f"PlotNode '{node.name}': Data file not found at {full_path}. Data not loaded."
                )
        else:
            node.logger.debug(f"PlotNode '{node.name}': No data file path specified.")

        return node
