from enum import Enum
import logging
from dataclasses import is_dataclass, fields
from typing import Any, Dict, List, Optional, Type

import matplotlib.figure
import matplotlib.axes
import matplotlib.patches as patches

from src.models.application_model import ApplicationModel
from src.models.nodes.group_node import GroupNode
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.rectangle_node import RectangleNode
from src.models.nodes.scene_node import SceneNode
from src.models.nodes.text_node import TextNode
from src.services.layout_manager import LayoutManager
from src.ui.renderers.plotting_strategies import CoordSyncStrategy, get_coord_strategy_registry, get_artist_strategy_registry

class Renderer:
    """
    A version-gated, recursive synchronizer that renders the scene graph 
    onto a Matplotlib figure.
    """

    def __init__(self, layout_manager: LayoutManager, application_model: ApplicationModel):
        self._layout_manager = layout_manager
        self._application_model = application_model
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Strategy registries for Coordinates and Artists
        self._coord_strategies = get_coord_strategy_registry()
        self._artist_strategies = get_artist_strategy_registry()
        
        # Track versions to avoid redundant reflection
        self._last_synced_versions: dict[str, int] = {} 
        self.logger.info("Renderer initialized.")

    def render(
        self,
        figure: matplotlib.figure.Figure,
        root_node: SceneNode,
        selection: list[SceneNode],
    ):
        """Renders the scene graph."""
        self.logger.info("Rendering scene graph.")
        
        self._render_plots(figure, root_node)

        # Render other node types (TextNode, RectangleNode, GroupNode)
        self._render_other_nodes(figure, root_node)

        # 3. Render highlights for selection
        self._render_highlights(figure, selection)
        self.logger.info("Scene graph rendering complete.")

    def _render_plots(self, figure: matplotlib.figure.Figure, root_node: SceneNode):
        """Renders PlotNodes using coordinate strategies for projection support."""
        plot_nodes = [n for n in root_node.all_descendants() if isinstance(n, PlotNode)]
        geometries = self._layout_manager.get_current_layout_geometries(plot_nodes)

        for node in plot_nodes:
            if node.id not in geometries or not node.plot_properties:
                continue
            
            rect = geometries[node.id]
            props = node.plot_properties
            
            # 1. Coordinate/Axes Creation
            coord_strategy = self._coord_strategies.get(props.coords.coord_type)
            if not coord_strategy:
                self.logger.warning(f"No coordinate strategy found for type {type(props.coords)}")
                continue

            if node.axes is None:
                # Delegate axes creation
                node.axes = coord_strategy.create_axes(figure, rect)
                node.axes.set_navigate(True)
                self.logger.debug(f"Created new axes for PlotNode {node.id} via {type(coord_strategy).__name__}")
            else:
                # Update geometry of existing axes
                node.axes.set_position(rect)

            # 2. Sync Properties (Version-Gated Orchestration)
            self._sync_plot_node(node, coord_strategy)

    def _sync_plot_node(self, node: PlotNode, coord_strategy: CoordSyncStrategy):
        """Orchestrates the recursive synchronization of a PlotNode."""
        props = node.plot_properties
        last_version = self._last_synced_versions.get(node.id, -1)
        
        if props._version <= last_version:
            return

        self.logger.debug(f"Syncing PlotNode {node.id} (v{props._version})")
        
        # 1. Sync Titles (left, center, right)
        for key, text_props in props.titles.items():
            path = f"titles.{key}"
            if key == "center":
                node.axes.set_title(text_props.text)
            elif hasattr(node.axes, f"set_{key}_title"):
                getattr(node.axes, f"set_{key}_title")(text_props.text)
            
            # Sync the common text properties (color, font, etc) on the title object
            self._sync_component(node.axes.title, text_props, path)

        # 2. Sync Coordinates (Axis, Spines) via Strategy
        coord_strategy.sync(node.axes, props.coords, "coords", self._sync_component)
        
        # 3. Sync Artists (Line, Scatter, Image, etc.) via Strategy
        self._sync_artists(node.axes, props, node)
        
        # Update the sync version
        self._last_synced_versions[node.id] = props._version

    def _sync_artists(self, ax: matplotlib.axes.Axes, props: Any, node: PlotNode):
        """Syncs the list of data artists by delegating to type-specific strategies."""
        for i, artist_props in enumerate(props.artists):
            path = f"artists.{i}"
            strategy = self._artist_strategies.get(artist_props.artist_type)
            
            if not strategy:
                self.logger.warning(f"No sync strategy found for artist type {artist_props.artist_type}")
                continue

            # 1. Identify or Create the Matplotlib Artist via Strategy
            mpl_artist = strategy.get_or_create_artist(ax, artist_props, i)
            
            # 2. Sync Visuals (Generic)
            if hasattr(artist_props, "visuals"):
                self._sync_component(mpl_artist, artist_props.visuals, f"{path}.visuals")

            # 3. Sync Data (Specialized Strategy)
            if node.data is not None:
                strategy.sync_data(mpl_artist, artist_props, node.data)

    def _sync_component(self, mpl_obj: Any, props_obj: Any, path: str):
        """Recursively maps dataclass fields to Matplotlib setters with picking support."""
        if not is_dataclass(props_obj):
            return

        # Tag for interactive picking (Matplotlib Picking API)
        if hasattr(mpl_obj, 'set_picker'):
            mpl_obj.set_picker(True)
            if hasattr(mpl_obj, 'set_gid'):
                mpl_obj.set_gid(path)

        for field in fields(props_obj):
            if field.name.startswith('_'):
                continue
                
            val = getattr(props_obj, field.name)
            # Resolve Enum to its value string for Matplotlib compatibility
            if isinstance(val, Enum):
                val = val.value
            
            # Recursive case for nested dataclasses
            if is_dataclass(val):
                try:
                    child_mpl = getattr(mpl_obj, field.name)
                    self._sync_component(child_mpl, val, f"{path}.{field.name}")
                except AttributeError:
                    # Fallback for common Matplotlib getters
                    if field.name == "label" and hasattr(mpl_obj, "get_label"):
                        self._sync_component(mpl_obj.get_label(), val, f"{path}.{field.name}")
                continue

            # Base case: Apply value via setter
            setter_name = f"set_{field.name}"
            if hasattr(mpl_obj, setter_name):
                self._apply_property(mpl_obj, setter_name, val)

    def _apply_property(self, mpl_obj: Any, setter_name: str, value: Any):
        """Standard setter application with position/limits overrides.
        TODO: Should the renderer be responsible for resolving this matplotlib specific logic?"""
        setter = getattr(mpl_obj, setter_name)
        try:
            if setter_name == "set_limits" and value: #TODO: This is not using my enum properly right now
                # Axis limits handling
                if "xaxis" in str(type(mpl_obj)).lower():
                    mpl_obj.get_axes().set_xlim(value)
                else:
                    mpl_obj.get_axes().set_ylim(value)
            else:
                setter(value)
        except Exception as e:
            self.logger.warning(f"Failed to apply {setter_name} on {type(mpl_obj)}: {e}")

    def _render_other_nodes(self, figure: matplotlib.figure.Figure, node: SceneNode):
        """Dispatches rendering of non-plot nodes."""
        if not node.visible or isinstance(node, PlotNode):
            return

        # Basic recursive rendering for GroupNodes
        if isinstance(node, GroupNode):
            for child in node.children:
                self._render_other_nodes(figure, child)
        else:
            # Placeholder for TextNode and RectangleNode
            pass

    def _render_highlights(self, figure: matplotlib.figure.Figure, selection: list[SceneNode]):
        """Highlights the selected node and focused sub-components."""
        for node in selection:
            if not isinstance(node, PlotNode):
                continue
            
            # Primary Node Highlight (Bounding Box)
            left, bottom, width, height = node.geometry
            highlight = patches.Rectangle(
                (left, bottom),
                width,
                height,
                facecolor="none",
                edgecolor="cornflowerblue",
                linewidth=2,
                transform=figure.transFigure,
                clip_on=False,
                # High zorder to appear on top
                zorder=1000,
            ) #TODO: These values should also be loaded in from a config file
            figure.add_artist(highlight)
            self.logger.debug(
                f"  Highlight rendered for PlotNode: {node.name} (ID: {node.id})."
            )
            
            # TODO: Add specific highlight for selected_path sub-components
