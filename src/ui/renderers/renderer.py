import logging
from dataclasses import is_dataclass, fields
from typing import Any

import matplotlib.figure
import matplotlib.axes
import matplotlib.patches as patches
import pandas as pd

from src.models.application_model import ApplicationModel
from src.models.nodes.group_node import GroupNode
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.rectangle_node import RectangleNode
from src.models.nodes.scene_node import SceneNode
from src.models.nodes.text_node import TextNode
from src.models.plots.plot_properties import PlotProperties
from src.services.layout_manager import LayoutManager

class Renderer:
    """
    A version-gated, recursive synchronizer that renders the scene graph 
    onto a Matplotlib figure.
    """

    def __init__(self, layout_manager: LayoutManager, application_model: ApplicationModel):
        self._layout_manager = layout_manager
        self._application_model = application_model
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Track versions to avoid redundant reflection
        self._last_synced_versions: dict[str, int] = {} 
        self.logger.info("Renderer initialized.")

    def render(
        self,
        figure: matplotlib.figure.Figure,
        root_node: SceneNode,
        selection: list[SceneNode],
    ):
        """Renders the scene graph, optimizing via version gating."""
        self.logger.info("Rendering scene graph.")
        
        self._render_plots(figure, root_node)  # New helper for plot nodes

        # Render other node types (TextNode, RectangleNode, GroupNode)
        self._render_other_nodes(figure, root_node)  # Modified _render_node


        # 3. Render highlights for selection
        self._render_highlights(figure, selection)
        self.logger.info("Scene graph rendering complete.")

    def _render_plots(self, figure: matplotlib.figure.Figure, root_node: SceneNode):
        """
        Renders all PlotNodes on the figure based on calculated geometries.
        TODO: Don't just reach into the application model or the layout manager. Ask them instead
        """
                
        plot_nodes = [n for n in root_node.all_descendants() if isinstance(n, PlotNode)]
        # TODO: Right now, this is very focussed on PlotNodes, and not on textnodes etc.
        geometries = self._layout_manager.get_current_layout_geometries(plot_nodes)

        for node in plot_nodes:
            if node.id not in geometries:
                continue
            
            # 1. Ensure Axes exists and has correct geometry
            rect = geometries[node.id]
            if node.axes is None:
                # Create a new axes for this plot node
                node.axes = figure.add_axes(rect)
                node.axes.set_navigate(True)
                self.logger.debug(f"Created new axes for PlotNode {node.id} at {rect}")
            else:
                # Update geometry of existing axes
                node.axes.set_position(rect)
                self.logger.debug(f"Updated axes position for PlotNode {node.id} to {rect}")

            # 2. Sync Properties (Version-Gated)
            if node.plot_properties:
                self._sync_plot_node(node)
    
    def _sync_plot_node(self, node: PlotNode):
        """Orchestrates the recursive synchronization of a PlotNode."""
        props = node.plot_properties
        last_version = self._last_synced_versions.get(node.id, -1)
        
        if props._version <= last_version:
            return

        self.logger.debug(f"Syncing PlotNode {node.id} (v{props._version})")
        
        # Sync titles (left, center, right)
        for key, text_props in props.titles.items():
            path = f"titles.{key}"
            # Matplotlib uses specialized setters for title alignment
            if key == "center":
                node.axes.set_title(text_props.text)
            elif hasattr(node.axes, f"set_{key}_title"):
                getattr(node.axes, f"set_{key}_title")(text_props.text)
            
            # Sync the common text properties (color, font, etc) on the title object
            # Note: node.axes.title is usually the center title artist
            self._sync_component(node.axes.title, text_props, path)

        # Sync Coordinates (Axis, Spines)
        self._sync_coordinates(node.axes, props.coords, "coords")
        
        # Sync Artists (Line, Scatter, etc.)
        self._sync_artists(node.axes, props, node)
        
        # Update the sync version
        self._last_synced_versions[node.id] = props._version

    def _sync_artists(self, ax: matplotlib.axes.Axes, props: PlotProperties, node: PlotNode):
        """Syncs the list of data artists (Lines, Scatters, etc.) on the axes."""
        # We ensure the number of Matplotlib artists matches the number of property objects
        # For simplicity in this pass, we sync existing artists or create new ones
        
        for i, artist_props in enumerate(props.artists):
            path = f"artists.{i}"
            
            # 1. Identify or Create the Matplotlib Artist
            # We use the list index as a simple key; in a more robust system, we'd use stable IDs
            try:
                # Check if we already have an artist at this index in the Axes
                mpl_artist = ax.get_lines()[i] if "Line" in str(type(artist_props)) else ax.collections[i]
            except IndexError:
                # Create a new artist based on type
                if "Line" in str(type(artist_props)):
                    mpl_artist, = ax.plot([], [])
                elif "Scatter" in str(type(artist_props)):
                    mpl_artist = ax.scatter([], [])
                else:
                    continue

            # 2. Sync Visuals (Generic)
            if hasattr(artist_props, "visuals"):
                self._sync_component(mpl_artist, artist_props.visuals, f"{path}.visuals")

            # 3. Sync Data (Specialized)
            if node.data is not None:
                self._sync_artist_data(mpl_artist, artist_props, node.data)

    def _sync_artist_data(self, mpl_artist: Any, artist_props: Any, data: pd.DataFrame):
        """Performs the actual plotting/data update for an artist."""
        try:
            if hasattr(artist_props, "x_column") and hasattr(artist_props, "y_column"):
                x = data[artist_props.x_column]
                y = data[artist_props.y_column]
                
                if hasattr(mpl_artist, "set_data"): # Line2D
                    mpl_artist.set_data(x, y)
                elif hasattr(mpl_artist, "set_offsets"): # PathCollection (Scatter)
                    import numpy as np
                    mpl_artist.set_offsets(np.column_stack((x, y)))
                    
        except Exception as e:
            self.logger.warning(f"Failed to sync data for artist: {e}")


    def _sync_coordinates(self, ax: matplotlib.axes.Axes, coords: Any, path: str):
        """Syncs Axis and Spine properties."""
        # Axis sync
        self._sync_component(ax.xaxis, coords.xaxis, f"{path}.xaxis")
        self._sync_component(ax.yaxis, coords.yaxis, f"{path}.yaxis")
        
        # Spines sync
        if hasattr(coords, "spines"):
            for spine_key, spine_props in coords.spines.items():
                if spine_key in ax.spines:
                    mpl_spine = ax.spines[spine_key]
                    self._sync_component(mpl_spine, spine_props, f"{path}.spines.{spine_key}")

    def _sync_component(self, mpl_obj: Any, props_obj: Any, path: str):
        """
        Recursively maps dataclass fields to Matplotlib setters.
        Enables interactive picking by tagging every artist with its property path.
        """
        if not is_dataclass(props_obj):
            return

        # Tag for interactive picking (Matplotlib Picking API)
        if hasattr(mpl_obj, 'set_picker'):
            mpl_obj.set_picker(True)
            if hasattr(mpl_obj, 'set_gid'):
                # GID stores the Property Path for the SelectionTool to resolve
                mpl_obj.set_gid(path)

        for field in fields(props_obj):
            if field.name.startswith('_'):
                continue
                
            val = getattr(props_obj, field.name)
            
            # Recursive case for nested dataclasses
            if is_dataclass(val):
                # Resolve the corresponding Matplotlib child object
                try:
                    child_mpl = getattr(mpl_obj, field.name)
                    self._sync_component(child_mpl, val, f"{path}.{field.name}")
                except AttributeError:
                    # Fallback for common Matplotlib getters if property name doesn't match attribute
                    if field.name == "label" and hasattr(mpl_obj, "get_label"):
                        self._sync_component(mpl_obj.get_label(), val, f"{path}.{field.name}")
                continue

            # Base case: Apply value via setter
            setter_name = f"set_{field.name}"
            if hasattr(mpl_obj, setter_name):
                self._apply_property(mpl_obj, setter_name, val)

    def _apply_property(self, mpl_obj: Any, setter_name: str, value: Any):
        """Applies property with special handling for non-standard Matplotlib signatures."""
        setter = getattr(mpl_obj, setter_name)
        try:
            # Matplotlib special cases
            if setter_name == "set_position" and isinstance(value, tuple):
                # Spines use set_position(('outward', 10))
                setter(value)
            elif setter_name == "set_limits" and value:
                # Axis limits
                if "xaxis" in str(type(mpl_obj)).lower():
                    mpl_obj.get_axes().set_xlim(value)
                else:
                    mpl_obj.get_axes().set_ylim(value)
            else:
                setter(value)
        except Exception as e:
            self.logger.warning(f"Failed to apply {setter_name} on {type(mpl_obj)}: {e}")


    def _render_other_nodes(self, figure: matplotlib.figure.Figure, node: SceneNode):
        """
        Dispatches rendering of a node based on its type, excluding PlotNodes.
        The specific render function is responsible for rendering the node
        and recursively calling _render_other_nodes for its children if it's a composite node.
        """
        if not node.visible or isinstance(node, PlotNode):  # Skip PlotNodes here
            self.logger.debug(
                f"Node {node.name} (ID: {node.id}) is not visible or is a PlotNode. Skipping rendering."
            )
            return

        render_func = self._render_strategies.get(type(node))
        if render_func:
            render_func(figure, node)
        else:
            # For GroupNodes, we need to recursively render children
            if isinstance(node, GroupNode):
                self.logger.debug(
                    f"Rendering GroupNode: {node.name} (ID: {node.id}), Children: {len(node.children)}"
                )
                for child in node.children:
                    self._render_other_nodes(figure, child)  # Recursive call
            else:
                self.logger.warning(
                    f"No renderer found for node type {type(node).__name__}. Node ID: {node.id}, Name: {node.name}"
                )

    def _render_group_node(self, figure: matplotlib.figure.Figure, node: GroupNode):
        """
        Renders a GroupNode by recursively rendering its children.
        A GroupNode itself has no direct visual representation.
        """
        self.logger.debug(
            f"Rendering GroupNode: {node.name} (ID: {node.id}), Children: {len(node.children)}"
        )
        for child in node.children:
            self._render_node(figure, child)

    def _render_rectangle_node(
        self, figure: matplotlib.figure.Figure, node: RectangleNode
    ):
        """
        Renders a single RectangleNode.
        """
        self.logger.debug(
            f"Rendering RectangleNode: {node.name} (ID: {node.id}). (Placeholder)"
        )
        # Placeholder for rendering a rectangle
        pass

    def _render_text_node(self, figure: matplotlib.figure.Figure, node: TextNode):
        """
        Renders a single TextNode.
        """
        self.logger.debug(
            f"Rendering TextNode: {node.name} (ID: {node.id}). (Placeholder)"
        )
        # Placeholder for rendering text
        pass

    def _render_highlights(
        self, figure: matplotlib.figure.Figure, selection: list[SceneNode]
    ):
        """Highlights the selected node and its active sub-component."""
        selected_path = self._application_model.selected_path #TODO: Bad. We're reaching into the application model
        
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

