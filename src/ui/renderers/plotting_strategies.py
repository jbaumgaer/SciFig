from abc import ABC, abstractmethod
from typing import Any, Callable

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from src.models.plots.plot_types import ArtistType, CoordinateSystem

# --- Coordinate Sync Strategies ---


class CoordSyncStrategy(ABC):
    """Base strategy for creating axes and syncing coordinate structural elements."""

    @abstractmethod
    def create_axes(self, figure: Figure, rect: list[float]) -> Axes:
        pass

    @abstractmethod
    def sync(self, ax: Axes, props: Any, path: str, component_syncer: Callable):
        pass


class Cartesian2DStrategy(CoordSyncStrategy):
    def create_axes(self, figure, rect):
        return figure.add_axes(rect)

    def sync(self, ax, props, path, component_syncer):
        component_syncer(ax.xaxis, props.xaxis, f"{path}.xaxis")
        component_syncer(ax.yaxis, props.yaxis, f"{path}.yaxis")
        if hasattr(props, "spines"):
            for key, spine_props in props.spines.items():
                if key in ax.spines:
                    component_syncer(
                        ax.spines[key], spine_props, f"{path}.spines.{key}"
                    )


class Cartesian3DStrategy(CoordSyncStrategy):
    def create_axes(self, figure, rect):
        # Local import to avoid global dependency on mplot3d if not needed
        return figure.add_axes(rect, projection="3d")

    def sync(self, ax, props, path, component_syncer):
        component_syncer(ax.xaxis, props.xaxis, f"{path}.xaxis")
        component_syncer(ax.yaxis, props.yaxis, f"{path}.yaxis")
        if hasattr(props, "zaxis"):
            component_syncer(ax.zaxis, props.zaxis, f"{path}.zaxis")


class PolarStrategy(CoordSyncStrategy):
    def create_axes(self, figure, rect):
        return figure.add_axes(rect, projection="polar")

    def sync(self, ax, props, path, component_syncer):
        component_syncer(ax.xaxis, props.theta_axis, f"{path}.theta_axis")
        component_syncer(ax.yaxis, props.r_axis, f"{path}.r_axis")
        if hasattr(props, "spine") and "polar" in ax.spines:
            component_syncer(ax.spines["polar"], props.spine, f"{path}.spine")


# --- Artist Sync Strategies ---


class ArtistSyncStrategy(ABC):
    """Base strategy for creating and syncing specific Matplotlib data artists."""

    @abstractmethod
    def get_or_create_artist(self, ax: Axes, props: Any, index: int) -> Any:
        pass

    @abstractmethod
    def sync_data(self, mpl_artist: Any, props: Any, data: pd.DataFrame):
        pass


class LineSyncStrategy(ArtistSyncStrategy):
    def get_or_create_artist(self, ax, props, index):
        lines = ax.get_lines()
        if index < len(lines):
            return lines[index]
        (line,) = ax.plot([], [])
        return line

    def sync_data(self, mpl_artist, props, data):
        if not (hasattr(props, "x_column") and hasattr(props, "y_column")):
            return
        x, y = data[props.x_column], data[props.y_column]
        if hasattr(mpl_artist, "set_3d_properties") and hasattr(props, "z_column"):
            mpl_artist.set_data(x, y)
            mpl_artist.set_3d_properties(data[props.z_column])
        else:
            mpl_artist.set_data(x, y)


class ScatterSyncStrategy(ArtistSyncStrategy):
    def get_or_create_artist(self, ax, props, index):
        # Scatters are stored in collections
        if index < len(ax.collections):
            return ax.collections[index]
        return ax.scatter([], [])

    def sync_data(self, mpl_artist, props, data):
        if not (hasattr(props, "x_column") and hasattr(props, "y_column")):
            return
        x, y = data[props.x_column], data[props.y_column]
        offsets = np.column_stack((x, y))
        mpl_artist.set_offsets(offsets)
        if hasattr(props, "z_column") and hasattr(mpl_artist, "set_3d_properties"):
            mpl_artist.set_3d_properties(data[props.z_column], "z")


class ImageSyncStrategy(ArtistSyncStrategy):
    def get_or_create_artist(self, ax, props, index):
        images = ax.get_images()
        if index < len(images):
            return images[index]
        return ax.imshow(np.zeros((2, 2)), visible=False)

    def sync_data(self, mpl_artist, props, data):
        if hasattr(props, "data_column"):
            mpl_artist.set_data(data[props.data_column])


class MeshSyncStrategy(ArtistSyncStrategy):
    def get_or_create_artist(self, ax, props, index):
        # Mesh plots are also in collections (QuadMesh)
        if index < len(ax.collections):
            return ax.collections[index]
        return ax.pcolormesh(np.zeros((2, 2)), visible=False)

    def sync_data(self, mpl_artist, props, data):
        if hasattr(props, "z_column"):
            # QuadMesh expects a flattened array for set_array
            mpl_artist.set_array(data[props.z_column].values.flatten())


# --- Strategy Registries ---


def get_coord_strategy_registry() -> dict[CoordinateSystem, CoordSyncStrategy]:
    """Returns a mapping of CoordinateSystem enum values to their corresponding sync strategies."""
    return {
        CoordinateSystem.CARTESIAN_2D: Cartesian2DStrategy(),
        CoordinateSystem.CARTESIAN_3D: Cartesian3DStrategy(),
        CoordinateSystem.POLAR: PolarStrategy(),
    }


def get_artist_strategy_registry() -> dict[ArtistType, ArtistSyncStrategy]:
    return {
        ArtistType.LINE: LineSyncStrategy(),
        ArtistType.SCATTER: ScatterSyncStrategy(),
        ArtistType.BAR: ScatterSyncStrategy(),  # Placeholder
        ArtistType.IMAGE: ImageSyncStrategy(),
        ArtistType.MESH: MeshSyncStrategy(),
        ArtistType.CONTOUR: ImageSyncStrategy(),  # Placeholder
        ArtistType.HISTOGRAM: ScatterSyncStrategy(),  # Placeholder
        ArtistType.STAIR: LineSyncStrategy(),  # Placeholder
    }
