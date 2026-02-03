from typing import Optional
import dataclasses

import pandas as pd

from .plot_properties import BasePlotProperties
from .scene_node import SceneNode


class PlotNode(SceneNode):
    """
    A scene node representing a single Matplotlib Axes (a subplot).
    """

    def __init__(self, parent: SceneNode | None = None, name: str = "Plot"):
        super().__init__(parent, name)

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
