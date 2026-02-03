from typing import Optional
import dataclasses
from pathlib import Path

import pandas as pd

from .plot_properties import BasePlotProperties, LinePlotProperties, ScatterPlotProperties, PlotMapping, AxesLimits
from .scene_node import SceneNode


class PlotNode(SceneNode):
    """
    A scene node representing a single Matplotlib Axes (a subplot).
    """

    def __init__(self, parent: SceneNode | None = None, name: str = "Plot", id: str | None = None):
        super().__init__(parent, name, id)

        # Properties migrated from the old ArtistModel
        self.geometry: tuple[float, float, float, float] = (0.1, 0.1, 0.8, 0.8)
        self.plot_properties: Optional[BasePlotProperties] = None
        self.data: pd.DataFrame | None = None

    def hit_test(self, position: tuple[float, float]) -> SceneNode | None:
        """
        Checks if the given position (in figure coordinates, 0-1) is within
        the bounds of this plot's geometry.
        """
        x, y = position
        left, bottom, width, height = self.geometry
        if left <= x <= left + width and bottom <= y <= bottom + height:
            return self
        return None

    def to_dict(self) -> dict:
        """Serializes the plot node to a dictionary."""
        node_dict = super().to_dict()
        
        data_path = f"data/{self.id}.parquet" if self.data is not None else None
        
        node_dict.update({
            "geometry": self.geometry,
            "plot_properties": dataclasses.asdict(self.plot_properties) if self.plot_properties else None,
            "data_path": data_path,
        })
        return node_dict

    @classmethod
    def from_dict(cls, data: dict, parent: SceneNode | None = None, temp_dir: Path | None = None) -> "PlotNode":
        """Creates a PlotNode from a dictionary."""
        node = super().from_dict(data, parent)
        node.geometry = tuple(data["geometry"])
        
        props_data = data.get("plot_properties")
        if props_data:
            # Here we would need a way to know which properties class to use.
            # For now, we assume LinePlotProperties, but this should be improved.
            # A 'plot_type' key in the props_data could drive this.
            prop_class = LinePlotProperties # Simple assumption for now
            # We need to reconstruct nested dataclasses manually
            mapping_data = props_data.get("plot_mapping", {})
            limits_data = props_data.get("axes_limits", {})
            props_data["plot_mapping"] = PlotMapping(**mapping_data)
            props_data["axes_limits"] = AxesLimits(**limits_data)
            
            node.plot_properties = prop_class(**props_data)

        data_path = data.get("data_path")
        if data_path and temp_dir:
            full_path = temp_dir / data_path
            if full_path.exists():
                node.data = pd.read_parquet(full_path)

        return node
