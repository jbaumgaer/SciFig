import logging
import math
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Optional

import matplotlib.patches as patches
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from src.models.application_model import ApplicationModel
from src.models.nodes.group_node import GroupNode
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.services.event_aggregator import EventAggregator
from src.services.layout_manager import LayoutManager
from src.shared.events import Events
from src.ui.renderers.plotting_strategies import (
    CoordSyncStrategy,
    get_artist_strategy_registry,
    get_coord_strategy_registry,
)


class Renderer:
    """
    A version-gated, recursive synchronizer that renders the scene graph
    onto a Matplotlib figure. Owns the lifecycle of live Matplotlib artists.
    """

    _GETTER_MAP = {
        # 1. Axis Objects: SciFig 'xaxis' field -> ax.xaxis object
        ("Axes", "xaxis"): lambda obj: obj.xaxis,
        ("Axes", "yaxis"): lambda obj: obj.yaxis,
        ("Axes", "zaxis"): lambda obj: obj.zaxis if hasattr(obj, "zaxis") else None,
        ("Axes", "spines"): lambda obj: obj.spines,
        # 2. Ticks & Labels: SciFig 'ticks' field maps to the Axis object itself
        # (because tick_params is called on the Axis)
        ("XAxis", "ticks"): lambda obj: obj,
        ("YAxis", "ticks"): lambda obj: obj,
        ("ZAxis", "ticks"): lambda obj: obj,
        # 3. Axis Labels: SciFig 'label' field -> axis.label (Text object)
        ("XAxis", "label"): lambda obj: obj.label,
        ("YAxis", "label"): lambda obj: obj.label,
        ("ZAxis", "label"): lambda obj: obj.label,
        # 4. Logical Redirects: Recurse on same object for visual atoms
        ("Line2D", "visuals"): lambda obj: obj,
        ("PathCollection", "visuals"): lambda obj: obj,
        ("Text", "font"): lambda obj: obj,
    }

    _SETTER_MAP = {
        # --- Axis Structural Properties (Delegate from Axis to parent Axes) ---
        ("XAxis", "limits"): lambda obj, val: (
            (obj.axes.set_xlim(*val), obj.axes.set_autoscalex_on(False))
            if any(v is not None for v in val)
            else (
                obj.axes.set_autoscalex_on(True),
                obj.axes.relim(),
                obj.axes.autoscale_view(scalex=True, scaley=False),
            )
        ),
        ("YAxis", "limits"): lambda obj, val: (
            (obj.axes.set_ylim(*val), obj.axes.set_autoscaley_on(False))
            if any(v is not None for v in val)
            else (
                obj.axes.set_autoscaley_on(True),
                obj.axes.relim(),
                obj.axes.autoscale_view(scalex=False, scaley=True),
            )
        ),
        ("ZAxis", "limits"): lambda obj, val: (
            obj.axes.set_zlim(*val) if any(v is not None for v in val) else None
        ),
        ("XAxis", "margin"): lambda obj, val: obj.axes.set_xmargin(val),
        ("YAxis", "margin"): lambda obj, val: obj.axes.set_ymargin(val),
        # --- Tick Parameters (The 'Mega-Setter' Translation) ---
        # We use which='major'/'minor' to target the specific SciFig sub-fields
        ("XAxis", "major_size"): lambda obj, val: obj.set_tick_params(
            which="major", size=val
        ),
        ("XAxis", "minor_size"): lambda obj, val: obj.set_tick_params(
            which="minor", size=val
        ),
        ("XAxis", "major_width"): lambda obj, val: obj.set_tick_params(
            which="major", width=val
        ),
        ("XAxis", "minor_width"): lambda obj, val: obj.set_tick_params(
            which="minor", width=val
        ),
        ("XAxis", "major_pad"): lambda obj, val: obj.set_tick_params(
            which="major", pad=val
        ),
        ("XAxis", "minor_pad"): lambda obj, val: obj.set_tick_params(
            which="minor", pad=val
        ),
        ("XAxis", "direction"): lambda obj, val: obj.set_tick_params(direction=val),
        ("XAxis", "color"): lambda obj, val: obj.set_tick_params(color=val),
        ("XAxis", "labelcolor"): lambda obj, val: obj.set_tick_params(labelcolor=val),
        ("XAxis", "labelsize"): lambda obj, val: obj.set_tick_params(labelsize=val),
        ("YAxis", "major_size"): lambda obj, val: obj.set_tick_params(
            which="major", size=val
        ),
        ("YAxis", "minor_size"): lambda obj, val: obj.set_tick_params(
            which="minor", size=val
        ),
        ("YAxis", "major_width"): lambda obj, val: obj.set_tick_params(
            which="major", width=val
        ),
        ("YAxis", "minor_width"): lambda obj, val: obj.set_tick_params(
            which="minor", width=val
        ),
        ("YAxis", "major_pad"): lambda obj, val: obj.set_tick_params(
            which="major", pad=val
        ),
        ("YAxis", "minor_pad"): lambda obj, val: obj.set_tick_params(
            which="minor", pad=val
        ),
        ("YAxis", "direction"): lambda obj, val: obj.set_tick_params(direction=val),
        ("YAxis", "color"): lambda obj, val: obj.set_tick_params(color=val),
        ("YAxis", "labelcolor"): lambda obj, val: obj.set_tick_params(labelcolor=val),
        ("YAxis", "labelsize"): lambda obj, val: obj.set_tick_params(labelsize=val),
        ("ZAxis", "major_size"): lambda obj, val: obj.set_tick_params(
            which="major", size=val
        ),
        ("ZAxis", "minor_size"): lambda obj, val: obj.set_tick_params(
            which="minor", size=val
        ),
        ("ZAxis", "major_width"): lambda obj, val: obj.set_tick_params(
            which="major", width=val
        ),
        ("ZAxis", "minor_width"): lambda obj, val: obj.set_tick_params(
            which="minor", width=val
        ),
        ("ZAxis", "major_pad"): lambda obj, val: obj.set_tick_params(
            which="major", pad=val
        ),
        ("ZAxis", "minor_pad"): lambda obj, val: obj.set_tick_params(
            which="minor", pad=val
        ),
        ("ZAxis", "direction"): lambda obj, val: obj.set_tick_params(direction=val),
        ("ZAxis", "color"): lambda obj, val: obj.set_tick_params(color=val),
        ("ZAxis", "labelcolor"): lambda obj, val: obj.set_tick_params(labelcolor=val),
        ("ZAxis", "labelsize"): lambda obj, val: obj.set_tick_params(labelsize=val),
        # --- Spines ---
        ("Spine", "color"): lambda obj, val: obj.set_edgecolor(val),
        ("Spine", "position"): lambda obj, val: (
            obj.set_position(val)
            if val not in ("left", "right", "bottom", "top")
            else None
        ),
        # --- Formatters ---
        ("XAxis", "use_offset"): lambda obj, val: (
            obj.get_major_formatter().set_useOffset(val)
            if hasattr(obj.get_major_formatter(), "set_useOffset")
            else None
        ),
        ("XAxis", "scientific_limits"): lambda obj, val: (
            obj.get_major_formatter().set_powerlimits(val)
            if hasattr(obj.get_major_formatter(), "set_powerlimits")
            else None
        ),
        # --- Spines ---
        ("Spine", "position"): lambda obj, val: (
            obj.set_position(val)
            if val not in ("left", "right", "bottom", "top")
            else None
        ),
        # --- Scalar Mappables (Images/Meshes) ---
        ("ScalarMappable", "norm_min"): lambda obj, val: obj.set_clim(vmin=val),
        ("ScalarMappable", "norm_max"): lambda obj, val: obj.set_clim(vmax=val),
        ("QuadMesh", "norm_min"): lambda obj, val: obj.set_clim(vmin=val),
        ("QuadMesh", "norm_max"): lambda obj, val: obj.set_clim(vmax=val),
    }

    def __init__(
        self,
        layout_manager: LayoutManager,
        application_model: ApplicationModel,
        event_aggregator: EventAggregator,
    ):
        self._layout_manager = layout_manager
        self._application_model = application_model
        self._event_aggregator = event_aggregator
        self.logger = logging.getLogger(self.__class__.__name__)

        # Strategy registries for Coordinates and Artists
        self._coord_strategies = get_coord_strategy_registry()
        self._artist_strategies = get_artist_strategy_registry()

        # Track live artists by node ID (since nodes are now headless)
        self._axes_registry: dict[str, Axes] = {}
        # Track versions to avoid redundant reflection
        self._last_synced_versions: dict[str, int] = {}
        self.logger.info("Renderer initialized.")

    def sync_back_limits(self, node_id: str):
        """
        Reads the current 'real' limits from the Matplotlib axes and
        publishes a request to update the model if they differ significantly.
        This ensures that Matplotlib's autoscale (including margins) is synced back.
        """
        ax = self._axes_registry.get(node_id)
        if not ax:
            return

        node = self._application_model.scene_root.find_node_by_id(node_id)
        if not (node and isinstance(node, PlotNode)):
            return

        props = node.plot_properties
        if not (props and props.coords):
            return

        # 1. X-Axis Sync
        mpl_xlim = ax.get_xlim()
        # In SciFig, limits are (min, max)
        model_xlim = props.coords.xaxis.limits
        if self._limits_differ(mpl_xlim, model_xlim):
            self.logger.debug(f"Syncing back X-limits for node {node_id}: {mpl_xlim}")
            self._event_aggregator.publish(
                Events.CHANGE_PLOT_COMPONENT_REQUESTED,
                node_id=node_id,
                path="coords.xaxis.limits",
                value=tuple(mpl_xlim),
            )

        # 2. Y-Axis Sync
        mpl_ylim = ax.get_ylim()
        model_ylim = props.coords.yaxis.limits
        if self._limits_differ(mpl_ylim, model_ylim):
            self.logger.debug(f"Syncing back Y-limits for node {node_id}: {mpl_ylim}")
            self._event_aggregator.publish(
                Events.CHANGE_PLOT_COMPONENT_REQUESTED,
                node_id=node_id,
                path="coords.yaxis.limits",
                value=tuple(mpl_ylim),
            )

    def _limits_differ(
        self,
        mpl_limits: tuple[float, float],
        model_limits: tuple[Optional[float], Optional[float]],
        tol: float = 1e-5,
    ) -> bool:
        """Checks if two sets of limits differ significantly."""
        for m_lim, model_lim in zip(mpl_limits, model_limits):
            if model_lim is None:
                return True  # If model is None, it definitely differs from a numeric value
            if not math.isclose(m_lim, model_lim, rel_tol=tol):
                return True
        return False

    def render(
        self,
        figure: Figure,
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

    def handle_node_removal(self, parent_id: str, removed_node_id: str):
        """Cleanup handler to destroy Matplotlib artists when a node is deleted."""
        if removed_node_id in self._axes_registry:
            ax = self._axes_registry.pop(removed_node_id)
            fig = ax.figure
            if fig:
                fig.delaxes(ax)
            self._last_synced_versions.pop(removed_node_id, None)
            self.logger.info(
                f"Destroyed Matplotlib axes for deleted node {removed_node_id}"
            )

    def _render_plots(self, figure: Figure, root_node: SceneNode):
        """Renders PlotNodes using coordinate strategies for projection support."""
        plot_nodes = [n for n in root_node.all_descendants(of_type=PlotNode)]
        geometries = self._layout_manager.get_current_layout_geometries(plot_nodes)

        for node in plot_nodes:
            # Defensive check: Skip nodes that haven't been hydrated yet (still dicts from template)
            if (
                node.id not in geometries
                or not node.plot_properties
                or isinstance(node.plot_properties, dict)
            ):
                continue

            rect = geometries[node.id]
            props = node.plot_properties

            # 1. Coordinate/Axes Retrieval or Creation
            coord_strategy = self._coord_strategies.get(props.coords.coord_type)
            if not coord_strategy:
                self.logger.warning(
                    f"No coordinate strategy found for type {type(props.coords)}"
                )
                continue

            ax = self._axes_registry.get(node.id)
            if ax is None:
                # Delegate axes creation
                ax = coord_strategy.create_axes(figure, rect)
                ax.set_navigate(True)
                self._axes_registry[node.id] = ax
                self.logger.debug(
                    f"Created new axes for PlotNode {node.id} via {type(coord_strategy).__name__}"
                )
            else:
                # Update geometry of existing axes
                ax.set_position(rect)

            # 2. Sync Properties (Version-Gated Orchestration)
            self._sync_plot_node(ax, node, coord_strategy)

    def _sync_plot_node(
        self, ax: Axes, node: PlotNode, coord_strategy: CoordSyncStrategy
    ):
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
                ax.set_title(text_props.text)
            elif hasattr(ax, f"set_{key}_title"):
                getattr(ax, f"set_{key}_title")(text_props.text)

            # Sync the common text properties (color, font, etc) on the title object
            self._sync_component(ax.title, text_props, path)

        # 2. Sync Artists (Line, Scatter, Image, etc.) via Strategy
        self._sync_artists(ax, props, node)

        # 3. Sync Coordinates (Axis, Spines) via Strategy
        coord_strategy.sync(ax, props.coords, "coords", self._sync_component)

        # Update the sync version
        self._last_synced_versions[node.id] = props._version

    def _sync_artists(self, ax: Axes, props: Any, node: PlotNode):
        """Syncs the list of data artists by delegating to type-specific strategies."""
        for i, artist_props in enumerate(props.artists):
            path = f"artists.{i}"
            strategy = self._artist_strategies.get(artist_props.artist_type)

            if not strategy:
                self.logger.warning(
                    f"No sync strategy found for artist type {artist_props.artist_type}"
                )
                continue

            # 1. Identify or Create the Matplotlib Artist via Strategy
            mpl_artist = strategy.get_or_create_artist(ax, artist_props, i)

            # 2. Sync Visuals (Generic)
            if hasattr(artist_props, "visuals"):
                self._sync_component(
                    mpl_artist, artist_props.visuals, f"{path}.visuals"
                )

            # 3. Sync Data (Specialized Strategy)
            if node.data is not None:
                strategy.sync_data(mpl_artist, artist_props, node.data)

    def _sync_component(self, mpl_obj: Any, props_obj: Any, path: str):
        """Recursively maps dataclass fields to Matplotlib setters with picking support."""
        if not is_dataclass(props_obj):
            return

        # Tag for interactive picking (Matplotlib Picking API)
        if hasattr(mpl_obj, "set_picker"):
            mpl_obj.set_picker(True)
            if hasattr(mpl_obj, "set_gid"):
                mpl_obj.set_gid(path)

        for field in fields(props_obj):
            if field.name.startswith("_"):
                continue

            val = getattr(props_obj, field.name)
            # Resolve Enum to its value string for Matplotlib compatibility
            if isinstance(val, Enum):
                val = val.value

            # Recursive case for nested dataclasses
            if is_dataclass(val):
                child_mpl = self._resolve_mpl_child(mpl_obj, field.name)
                if child_mpl:
                    self._sync_component(child_mpl, val, f"{path}.{field.name}")
                continue

            # Base case: Apply primitive or enum value
            self._apply_property(mpl_obj, field.name, val)

    def _resolve_mpl_child(self, mpl_obj: Any, field_name: str) -> Optional[Any]:
        """Resolves a SciFig field to a Matplotlib child object using translation overrides."""
        obj_type = type(mpl_obj).__name__

        # 1. Check for explicit translation
        if (obj_type, field_name) in self.__class__._GETTER_MAP:
            return self.__class__._GETTER_MAP[(obj_type, field_name)](mpl_obj)

        # 2. Default: Look for direct attribute
        if hasattr(mpl_obj, field_name):
            return getattr(mpl_obj, field_name)

        # 3. Fallback for common Matplotlib naming conventions (get_X)
        getter_name = f"get_{field_name}"
        if hasattr(mpl_obj, getter_name):
            return getattr(mpl_obj, getter_name)()

        return None

    def _apply_property(self, mpl_obj: Any, field_name: str, value: Any):
        """Applies a SciFig property to a Matplotlib object using translation overrides."""
        obj_type = type(mpl_obj).__name__

        # 1. Ignore 'inherit' values which are Matplotlib RC defaults but invalid for some setters
        if value == "inherit":
            return

        # 2. Check for explicit setter translation (Solves the 'limits' problem)
        if (obj_type, field_name) in self.__class__._SETTER_MAP:
            try:
                self.__class__._SETTER_MAP[(obj_type, field_name)](mpl_obj, value)
                return
            except Exception as e:
                self.logger.warning(
                    f"Translation failed for {obj_type}.{field_name}: {e}"
                )
                return

        # 2. Generic fallback: set_<field_name>
        setter_name = f"set_{field_name}"
        if hasattr(mpl_obj, setter_name):
            try:
                getattr(mpl_obj, setter_name)(value)
            except Exception as e:
                self.logger.warning(
                    f"Failed to apply generic setter {setter_name} on {obj_type}: {e}"
                )

    def _render_other_nodes(self, figure: Figure, node: SceneNode):
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

    def _render_highlights(self, figure: Figure, selection: list[SceneNode]):
        """Highlights the selected node and focused sub-components."""
        # Cleanup old highlights by removing artists tagged with 'gid=highlight'
        for artist in list(figure.artists):
            if artist.get_gid() == "selection_highlight":
                artist.remove()

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
                gid="selection_highlight",  # Tag for removal
                # High zorder to appear on top
                zorder=1000,
            )  # TODO: These values should also be loaded in from a config file
            figure.add_artist(highlight)
            self.logger.debug(
                f"  Highlight rendered for PlotNode: {node.name} (ID: {node.id})."
            )

            # TODO: Add specific highlight for selected_path sub-components
