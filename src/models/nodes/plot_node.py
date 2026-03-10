import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.models.nodes.scene_node import SceneNode
from src.models.plots.plot_properties import PlotProperties
from src.shared.geometry import Rect


class PlotNode(SceneNode):
    """
    A scene node representing a single Matplotlib Axes (a subplot).
    Maintains properties and data in a headless, serializable format.
    """

    def __init__(
        self,
        parent: Optional[SceneNode] = None,
        name: str = "Plot",
        id: Optional[str] = None,
    ):
        super().__init__(parent, name, id)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"PlotNode initialized: {self.name} (ID: {self.id})")

        # Geometry in physical centimeters (cm).
        # TODO: This should never have default values
        self.geometry: Rect = Rect(2.0, 2.0, 8.0, 8.0)
        
        self.plot_properties: Optional[PlotProperties] = None
        self.data: Optional[pd.DataFrame] = None
        self.data_file_path: Optional[Path] = None

    def hit_test(self, position: tuple[float, float]) -> Optional[SceneNode]:
        """
        Checks if the given physical position (cm) is within
        the bounds of this plot's geometry.
        """
        if self.geometry.contains(*position):
            self.logger.debug(
                f"Hit test for {self.name} (ID: {self.id}): Hit at {position} cm."
            )
            return self
        return None

    def to_dict(self, exclude_geometry: bool = False) -> dict:
        """Serializes the plot node to a dictionary."""
        node_dict = super().to_dict()

        if not exclude_geometry:
            node_dict["geometry"] = {
                "x": self.geometry.x,
                "y": self.geometry.y,
                "width": self.geometry.width,
                "height": self.geometry.height,
            }

        # Handle both object and dict (sparse) properties
        props_data = None
        if self.plot_properties:
            if isinstance(self.plot_properties, dict):
                props_data = self.plot_properties
            else:
                props_data = self.plot_properties.to_dict()

        node_dict.update(
            {
                "plot_properties": props_data,
                "data_file_path": (
                    str(self.data_file_path) if self.data_file_path else None
                ),
            }
        )
        return node_dict

    @classmethod
    def from_dict(
        cls,
        data: dict,
        parent: Optional[SceneNode] = None,
        temp_dir: Optional[Path] = None,
    ) -> "PlotNode":
        """Creates a PlotNode from a dictionary using recursive property reconstruction."""
        node = super().from_dict(data, parent)

        # 1. Geometry reconstruction (Physical CM)
        geom_data = data.get("geometry", {})
        node.geometry = Rect(
            x=geom_data.get("x", 0.0),
            y=geom_data.get("y", 0.0),
            width=geom_data.get("width", 5.0),
            height=geom_data.get("height", 5.0),
        )
        # TODO: This should never have default values, but throw an error if it cannot get recovered

        # 2. Hierarchical PlotProperties reconstruction
        props_data = data.get("plot_properties")
        if props_data:
            # Check if it's a complete tree (with versioning) or a sparse dict (template)
            if isinstance(props_data, dict) and "_version" in props_data:
                node.plot_properties = PlotProperties.from_dict(props_data)
                node.logger.debug(
                    f"PlotNode '{node.name}': Strict property reconstruction complete."
                )
            else:
                # Store as sparse dict for deferred reactive hydration
                node.plot_properties = props_data
                node.logger.debug(
                    f"PlotNode '{node.name}': Sparse property dict stored for deferred hydration."
                )

        # 3. Data loading
        path_str = data.get("data_file_path")
        if path_str:
            node.data_file_path = Path(path_str)
            # Logic for temp_dir relative loading
            load_path = node.data_file_path
            if temp_dir and not load_path.is_absolute():
                load_path = temp_dir / load_path.name

            if load_path.exists() and load_path.suffix == ".parquet":
                node.data = pd.read_parquet(load_path)
                node.logger.debug(
                    f"PlotNode '{node.name}' loaded data from {load_path}.parquet"
                )
            elif load_path.exists() and load_path.suffix == ".csv":
                node.data = pd.read_csv(load_path, sep=";")  # Default project separator
                # TODO: This should be handled by the data service, not the plot node

                node.logger.debug(
                    f"PlotNode '{node.name}' loaded data from {load_path}.csv"
                )
            else:
                node.logger.warning(
                    f"PlotNode '{node.name}': Data file not found at {load_path}. Data not loaded."
                )
        else:
            node.logger.debug(
                f"PlotNode '{node.name}': No data file path specified or file does not exist."
            )

        return node
