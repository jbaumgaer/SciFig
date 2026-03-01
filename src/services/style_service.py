import logging
from dataclasses import is_dataclass
from typing import Any, Union

import matplotlib as mpl

from src.models.plots.plot_properties import (
    AxisProperties,
    BarArtistProperties,
    Cartesian2DProperties,
    Cartesian3DProperties,
    ContourArtistProperties,
    FontProperties,
    GridProperties,
    HistogramArtistProperties,
    ImageArtistProperties,
    LineArtistProperties,
    LineProperties,
    MeshArtistProperties,
    PatchProperties,
    PlotProperties,
    PolarProperties,
    ScalarMappableProperties,
    ScatterArtistProperties,
    SpineProperties,
    StairArtistProperties,
    TextProperties,
    TickProperties,
)
from src.models.plots.plot_types import (
    ArtistType,
    AutolimitMode,
    AxisKey,
    SpinePosition,
    TickDirection,
)
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


class ThemeIncompleteError(Exception):
    """Raised when an .mplstyle file is missing required keys for strict construction."""

    pass


class StyleService:
    """
    The Mandatory Factory for plot properties.
    Resolves flat .mplstyle keys into hierarchical dataclasses and enforces theme completeness.
    No default values are allowed; every property must be present in the theme.
    """

    # Exhaustive list of required keys covering the entire property tree.
    # Includes standard Matplotlib keys and custom SciFig keys for deep hierarchy.
    REQUIRED_KEYS = [
        # Font
        "font.family",
        "font.style",
        "font.variant",
        "font.weight",
        "font.stretch",
        "font.size",
        # Text
        "text.color",
        # Lines
        "lines.linewidth",
        "lines.linestyle",
        "lines.color",
        "lines.marker",
        "lines.markerfacecolor",
        "lines.markeredgecolor",
        "lines.markeredgewidth",
        "lines.markersize",
        # Patch
        "patch.facecolor",
        "patch.edgecolor",
        "patch.linewidth",
        "patch.force_edgecolor",
        # Ticks (TODO: z axis cannot be handled right now)
        "xtick.major.size",
        "xtick.minor.size",
        "xtick.major.width",
        "xtick.minor.width",
        "xtick.major.pad",
        "xtick.minor.pad",
        "xtick.direction",
        "xtick.color",
        "xtick.labelcolor",
        "xtick.labelsize",
        "xtick.minor.visible",
        "xtick.minor.ndivs",
        "ytick.major.size",
        "ytick.minor.size",
        "ytick.major.width",
        "ytick.minor.width",
        "ytick.major.pad",
        "ytick.minor.pad",
        "ytick.direction",
        "ytick.color",
        "ytick.labelcolor",
        "ytick.labelsize",
        "ytick.minor.visible",
        "ytick.minor.ndivs",
        # Spines
        "axes.edgecolor",
        "axes.linewidth",
        "axes.spines.bottom",
        "axes.spines.left",
        "axes.spines.top",
        "axes.spines.right",
        # Grid
        "axes.grid",
        "grid.color",
        "grid.linestyle",
        "grid.linewidth",
        "grid.alpha",
        # Axis/Coordinates
        "axes.facecolor",
        "axes.axisbelow",
        "axes.prop_cycle",
        "axes.xmargin",
        "axes.ymargin",
        "axes.autolimit_mode",
        "axes.formatter.useoffset",
        "axes.formatter.offset_threshold",
        "axes.formatter.limits",
        # Specialized Artist Keys
        "image.cmap",
        "contour.linewidth",
        "hist.bins",
        # 3D Specific
        "axes3d.pane_color_x",
        "axes3d.pane_color_y",
        "axes3d.pane_color_z",
    ]

    def __init__(self, event_aggregator: EventAggregator):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Initialize with current matplotlib defaults as baseline
        self._event_aggregator: EventAggregator = event_aggregator
        self._current_style: dict[str, Any] = dict(mpl.rcParams)

        # Registry mapping ArtistType to its creation method
        self._ARTIST_FACTORIES = {
            ArtistType.LINE: self._create_line_artist,
            ArtistType.SCATTER: self._create_scatter_artist,
            ArtistType.BAR: self._create_bar_artist,
            ArtistType.IMAGE: self._create_image_artist,
            ArtistType.MESH: self._create_mesh_artist,
            ArtistType.CONTOUR: self._create_contour_artist,
            ArtistType.HISTOGRAM: self._create_histogram_artist,
            ArtistType.STAIR: self._create_stair_artist,
            ArtistType.POLAR_LINE: self._create_line_artist,
            ArtistType.SURFACE: self._create_mesh_artist,
            ArtistType.BOXPLOT: self._create_line_artist,  # Placeholder
        }

        self._event_aggregator.subscribe(
            Events.INITIALIZE_PLOT_THEME_REQUESTED, self._on_initialize_theme_requested
        )
        self._event_aggregator.subscribe(
            Events.HYDRATE_PLOT_PROPERTIES_REQUESTED,
            self._on_hydrate_properties_requested,
        )

    def load_style(self, style_path: str):
        """Loads a new .mplstyle file and validates its completeness before applying."""
        try:
            # Use matplotlib's parser to handle the file correctly
            new_style = mpl.RcParams()
            new_style.update(mpl.rc_params_from_file(style_path, use_subprocess=False))
            self._validate_style(new_style)
            self._current_style = dict(new_style)
            self.logger.info(f"Successfully loaded and validated style: {style_path}")
        except Exception as e:
            self.logger.error(f"Failed to load style {style_path}: {e}")
            raise ThemeIncompleteError(f"Style validation failed for {style_path}: {e}")

    def create_properties_from_sparse(self, overrides: dict) -> PlotProperties:
        """
        Creates a fully initialized PlotProperties tree by first generating
        a themed base and then hydrating it with sparse overrides.
        """
        # 1. Determine the base plot type from overrides or default to Line
        # (Needed because themed properties are type-specific)
        p_type_raw = overrides.get("plot_type", ArtistType.LINE)
        try:
            p_type = (
                ArtistType(p_type_raw)
                if not isinstance(p_type_raw, ArtistType)
                else p_type_raw
            )
        except ValueError:
            p_type = ArtistType.LINE

        # 2. Create the complete base tree from the current theme
        base_props = self.create_themed_properties(p_type)

        # 3. Apply the sparse overrides
        self.hydrate(base_props, overrides)
        return base_props

    def hydrate(self, base_obj: Any, overrides: dict):
        """
        Recursively merges a sparse dictionary into a typed dataclass tree.
        Handles Enum resolution and type-safety checks.
        """
        for key, value in overrides.items():
            if not hasattr(base_obj, key) or key.startswith("_"):
                continue

            current_attr = getattr(base_obj, key)

            # Recursive Case: Nested Dataclasses
            if isinstance(value, dict) and is_dataclass(current_attr):
                self.hydrate(current_attr, value)

            # Recursive Case: Dicts of Dataclasses (e.g., spines, titles)
            elif isinstance(value, dict) and isinstance(current_attr, dict):
                for sub_key, sub_value in value.items():
                    # Resolve keys (especially for Spines which use Enums as keys)
                    resolved_key = self._resolve_key_type(type(current_attr), sub_key)
                    # For titles, sub_key is just 'left', 'center', 'right'
                    if resolved_key in current_attr:
                        self.hydrate(current_attr[resolved_key], sub_value)

            # Recursive Case: Lists (e.g., artists)
            elif isinstance(value, list) and isinstance(current_attr, list):
                self._hydrate_list(base_obj, key, current_attr, value)

            # Base Case: Leaf Node (Primitive or Enum)
            else:
                self._apply_leaf(base_obj, key, value)

        # Increment version to trigger renderer sync
        if hasattr(base_obj, "_version"):
            base_obj._version += 1

    def _resolve_key_type(self, dict_type: Any, key: str) -> Any:
        """Helper to resolve a string key into an Enum if the dict uses Enums as keys."""
        # Python's dict type hints are hard to inspect at runtime (e.g. dict[SpinePosition, SpineProperties])
        # We check common Enum-keyed dicts in SciFig
        try:
            # Check if SpinePosition values are in the key
            return SpinePosition(key)
        except ValueError:
            pass
        return key

    def _hydrate_list(
        self, parent: Any, attr_name: str, base_list: list, overrides: list
    ):
        """
        Hydrates lists of dataclasses. For SciFig artists, we re-initialize
        themed bases for each artist type in the template.
        """
        if attr_name == "artists":
            new_artists = []
            for a_overrides in overrides:
                a_type_raw = a_overrides.get("artist_type", ArtistType.LINE)
                try:
                    a_type = (
                        ArtistType(a_type_raw)
                        if not isinstance(a_type_raw, ArtistType)
                        else a_type_raw
                    )
                except ValueError:
                    a_type = ArtistType.LINE

                # Create themed base for this specific artist type
                factory = self._ARTIST_FACTORIES.get(a_type)
                if factory:
                    base_artist = factory()
                    self.hydrate(base_artist, a_overrides)
                    new_artists.append(base_artist)

            setattr(parent, attr_name, new_artists)
        else:
            # Generic list handling (e.g., prop_cycle) - Direct replacement
            setattr(parent, attr_name, overrides)

    def _apply_leaf(self, obj: Any, key: str, value: Any):
        """Applies a value to an object, resolving Enum strings if necessary."""
        from enum import Enum
        from typing import get_type_hints

        type_hints = get_type_hints(type(obj))
        expected_type = type_hints.get(key)

        # 1. Handle Enums (Strings from JSON -> Enum members)
        if expected_type:
            # Check for Union types (e.g. Optional[Enum], Union[bool, str])
            origin = getattr(expected_type, "__origin__", None)
            args = getattr(expected_type, "__args__", ())

            # Find the actual Enum class in the Union
            enum_cls = None
            if origin is Union:
                for arg in args:
                    if isinstance(arg, type) and issubclass(arg, Enum):
                        enum_cls = arg
                        break
            elif isinstance(expected_type, type) and issubclass(expected_type, Enum):
                enum_cls = expected_type

            if enum_cls and isinstance(value, str):
                try:
                    # Try custom parser first
                    if hasattr(enum_cls, "from_str"):
                        value = enum_cls.from_str(value)
                    else:
                        value = enum_cls(value)
                except ValueError:
                    self.logger.warning(
                        f"Hydration: Could not resolve '{value}' as {enum_cls.__name__}"
                    )

        # 2. Standard assignment
        try:
            setattr(obj, key, value)
        except Exception as e:
            self.logger.error(
                f"Hydration: Failed to set {key} on {type(obj).__name__}: {e}"
            )

    def create_themed_properties(self, plot_type: ArtistType) -> PlotProperties:
        """Factory method to create a fully initialized PlotProperties tree from the current theme."""
        if not self._current_style:
            raise RuntimeError(
                "StyleService: No style loaded. Call load_style() first."
            )

        # 1. Determine Coordinate System based on ArtistType
        if plot_type == ArtistType.SURFACE:
            coords = self._create_cartesian_3d()
        elif plot_type == ArtistType.POLAR_LINE:
            coords = self._create_polar()
        else:
            coords = self._create_cartesian_2d()

        # 2. Artist Initialization
        factory = self._ARTIST_FACTORIES.get(plot_type)
        artists = [factory()] if factory else []

        return PlotProperties(
            titles={
                "left": self._create_text(""),
                "center": self._create_text(""),
                "right": self._create_text(""),
            },
            coords=coords,
            legend={},
            artists=artists,
        )

    # --- Artist Factories ---
    # TODO: Lines are currently treated on a different footing. Because the linewidth can be set globally, I can take the global value and inherit it into LineProperties.
    # However, for other kwargs that would be passed to ax.plot, I cannot do that. Maybe I need to think about why this distinction exists

    def _on_initialize_theme_requested(self, node_id: str, plot_type: ArtistType):
        """Reactive handler to generate and publish themed properties."""
        try:
            props = self.create_themed_properties(plot_type)
            # Publish a request to change the 'plot_properties' path
            self._event_aggregator.publish(
                Events.CHANGE_PLOT_COMPONENT_REQUESTED,
                node_id=node_id,
                path="plot_properties",
                value=props,
            )
        except Exception as e:
            self.logger.error(f"StyleService: Theme error for node {node_id}: {e}")

    def _on_hydrate_properties_requested(self, node_id: str, overrides: dict):
        """
        Generates a themed base and then deep-merges the overrides into it.
        Publishes the final result as a property change request.
        """
        try:
            # 1. Determine artist type from overrides or default to Line
            # This is needed because themed property trees are type-specific.
            artist_list = overrides.get("artists", [{}])
            artist_data = artist_list[0] if artist_list else {}
            artist_type_raw = artist_data.get("artist_type", ArtistType.LINE)
            try:
                artist_type = (
                    ArtistType(artist_type_raw)
                    if not isinstance(artist_type_raw, ArtistType)
                    else artist_type_raw
                )
            except ValueError:
                artist_type = ArtistType.LINE

            # 2. Generate the "Complete" themed base
            props = self.create_themed_properties(artist_type)

            # 3. Deep Merge (Hydrate) the overrides into the base
            self.hydrate(props, overrides)

            # 4. Final Publish
            self._event_aggregator.publish(
                Events.CHANGE_PLOT_COMPONENT_REQUESTED,
                node_id=node_id,
                path="plot_properties",
                value=props,
            )
        except Exception as e:
            self.logger.error(
                f"StyleService: Hydration failed for node {node_id}: {e}", exc_info=True
            )

    def hydrate(self, base_obj: Any, overrides: dict):
        """
        Recursively merges a sparse dictionary into a typed dataclass tree.
        Handles Enum resolution and type-safety checks.
        """
        for key, value in overrides.items():
            if not hasattr(base_obj, key) or key.startswith("_"):
                continue

            current_attr = getattr(base_obj, key)

            # Case 1: Recursive Dataclasses
            if isinstance(value, dict) and is_dataclass(current_attr):
                self.hydrate(current_attr, value)

            # Case 2: Enum-keyed Dicts (Spines)
            elif isinstance(value, dict) and isinstance(current_attr, dict):
                for sub_key, sub_value in value.items():
                    resolved_key = self._resolve_key_type(type(current_attr), sub_key)
                    if resolved_key in current_attr:
                        self.hydrate(current_attr[resolved_key], sub_value)

            # Case 3: Lists (Artists)
            elif isinstance(value, list) and isinstance(current_attr, list):
                self._hydrate_list(base_obj, key, current_attr, value)

            # Case 4: Base Primitive / Enum
            else:
                self._apply_leaf(base_obj, key, value)

    def _resolve_key_type(self, dict_type: Any, key: str) -> Any:
        """Helper to resolve a string key into an Enum if the dict uses Enums as keys."""
        try:
            # Check for SpinePosition strings (Matplotlib standard)
            return SpinePosition(key)
        except ValueError:
            pass
        return key

    def _hydrate_list(
        self, parent: Any, attr_name: str, base_list: list, overrides: list
    ):
        """For artists, we re-initialize the themed base for each type in the list."""
        if attr_name == "artists":
            new_artists = []
            for a_overrides in overrides:
                a_type_raw = a_overrides.get("artist_type", ArtistType.LINE)
                try:
                    a_type = (
                        ArtistType(a_type_raw)
                        if not isinstance(a_type_raw, ArtistType)
                        else a_type_raw
                    )
                except ValueError:
                    a_type = ArtistType.LINE

                factory = self._ARTIST_FACTORIES.get(a_type)
                if factory:
                    base_artist = factory()
                    self.hydrate(base_artist, a_overrides)
                    new_artists.append(base_artist)
            setattr(parent, attr_name, new_artists)
        else:
            setattr(parent, attr_name, overrides)

    def _apply_leaf(self, obj: Any, key: str, value: Any):
        """Applies a value to an object, resolving Enum strings if necessary."""
        from enum import Enum
        from typing import Union, get_type_hints

        type_hints = get_type_hints(type(obj))
        expected_type = type_hints.get(key)

        if expected_type:
            # Handle Unions/Optional (look for Enums within the args)
            origin = getattr(expected_type, "__origin__", None)
            args = getattr(expected_type, "__args__", ())

            enum_cls = None
            if origin is Union:
                for arg in args:
                    if isinstance(arg, type) and issubclass(arg, Enum):
                        enum_cls = arg
                        break
            elif isinstance(expected_type, type) and issubclass(expected_type, Enum):
                enum_cls = expected_type

            if enum_cls and isinstance(value, str):
                try:
                    if hasattr(enum_cls, "from_str"):
                        value = enum_cls.from_str(value)
                    else:
                        value = enum_cls(value)
                except ValueError:
                    pass

        try:
            setattr(obj, key, value)
        except Exception as e:
            self.logger.error(f"StyleService.hydrate: Failed to set {key}: {e}")

    def _parse_numeric_or_str(self, val: Any) -> Any:
        """
        Attempts to convert a value to a float. If that fails (e.g., for aliases
        like 'medium' or 'large'), returns the value as-is.
        """
        try:
            return float(val)
        except (ValueError, TypeError):
            return val

    def create_themed_properties(self, plot_type: ArtistType) -> PlotProperties:
        """Factory method to create a fully initialized PlotProperties tree from the current theme."""
        if not self._current_style:
            raise RuntimeError(
                "StyleService: No style loaded. Call load_style() first."
            )

        # 1. Determine Coordinate System based on ArtistType
        if plot_type == ArtistType.SURFACE:
            coords = self._create_cartesian_3d()
        elif plot_type == ArtistType.POLAR_LINE:
            coords = self._create_polar()
        else:
            coords = self._create_cartesian_2d()

        # 2. Artist Initialization
        factory = self._ARTIST_FACTORIES.get(plot_type)
        artists = [factory()] if factory else []

        return PlotProperties(
            titles={
                "left": self._create_text(""),
                "center": self._create_text(""),
                "right": self._create_text(""),
            },
            coords=coords,
            legend={},
            artists=artists,
        )

    # --- Artist Factories ---

    def _create_line_artist(self) -> LineArtistProperties:
        return LineArtistProperties(
            visible=True,
            zorder=1,
            visuals=self._create_line(),
        )

    def _create_scatter_artist(self) -> ScatterArtistProperties:
        return ScatterArtistProperties(
            visible=True,
            zorder=1,
            visuals=self._create_line(),
        )

    def _create_bar_artist(self) -> BarArtistProperties:
        s = self._current_style
        return BarArtistProperties(
            visible=True,
            zorder=1,
            visuals=self._create_patch(),
            width=0.8,  # These are defaults for now because matplotlib doesn't have these RC params
            align="center",
        )

    def _create_image_artist(self) -> ImageArtistProperties:
        s = self._current_style
        return ImageArtistProperties(
            visible=True,
            zorder=1,
            visuals=self._create_mappable(),
        )

    def _create_mesh_artist(self) -> MeshArtistProperties:
        s = self._current_style
        return MeshArtistProperties(
            visible=True,
            zorder=1,
            visuals=self._create_mappable(),
        )

    def _create_contour_artist(self) -> ContourArtistProperties:
        s = self._current_style
        return ContourArtistProperties(
            visible=True,
            zorder=1,
            visuals=self._create_mappable(),
            linewidth=self._parse_numeric_or_str(s["contour.linewidth"]),
            levels=10,  # These are defaults for now because matplotlib doesn't have these RC params
            filled=True,
        )

    def _create_histogram_artist(self) -> HistogramArtistProperties:
        s = self._current_style
        return HistogramArtistProperties(
            visible=True,
            zorder=1,
            visuals=self._create_patch(),
            bins=s["hist.bins"],
            density=bool(s["hist.density"]),
            cumulative=bool(s["hist.cumulative"]),
        )

    def _create_stair_artist(self) -> StairArtistProperties:
        s = self._current_style
        return StairArtistProperties(
            visible=True,
            zorder=1,
            visuals=self._create_line(),
            baseline=0.0,  # These are defaults for now because matplotlib doesn't have these RC params
            fill=False,
        )

    # --- Visual Atom Factories ---

    def _create_font(self) -> FontProperties:
        s = self._current_style
        family = s["font.family"]
        return FontProperties(
            family=str(family[0] if isinstance(family, list) else family),
            style=str(s["font.style"]),
            variant=str(s["font.variant"]),
            weight=str(s["font.weight"]),
            stretch=str(s["font.stretch"]),
            size=self._parse_numeric_or_str(s["font.size"]),
        )

    def _create_text(self, content: str) -> TextProperties:
        s = self._current_style
        return TextProperties(
            text=content,
            color=s["text.color"],
            font=self._create_font(),
        )

    def _create_line(self) -> LineProperties:
        s = self._current_style
        return LineProperties(
            linewidth=self._parse_numeric_or_str(s["lines.linewidth"]),
            linestyle=s["lines.linestyle"],
            color=s["lines.color"],
            marker=str(s["lines.marker"]),
            markerfacecolor=s["lines.markerfacecolor"],
            markeredgecolor=s["lines.markeredgecolor"],
            markeredgewidth=self._parse_numeric_or_str(s["lines.markeredgewidth"]),
            markersize=self._parse_numeric_or_str(s["lines.markersize"]),
        )

    def _create_patch(self) -> PatchProperties:
        s = self._current_style
        return PatchProperties(
            facecolor=s["patch.facecolor"],
            edgecolor=s["patch.edgecolor"],
            linewidth=self._parse_numeric_or_str(s["patch.linewidth"]),
            force_edgecolor=bool(s["patch.force_edgecolor"]),
        )

    def _create_mappable(self) -> ScalarMappableProperties:
        s = self._current_style
        return ScalarMappableProperties(
            cmap=str(s["image.cmap"]), norm_min=None, norm_max=None, has_colorbar=False
        )

    # --- Coordinate Factories ---

    def _create_ticks(self, axis_key: AxisKey) -> TickProperties:
        s = self._current_style
        return TickProperties(
            major_size=self._parse_numeric_or_str(
                s[f"{axis_key.value}tick.major.size"]
            ),
            minor_size=self._parse_numeric_or_str(
                s[f"{axis_key.value}tick.minor.size"]
            ),
            major_width=self._parse_numeric_or_str(
                s[f"{axis_key.value}tick.major.width"]
            ),
            minor_width=self._parse_numeric_or_str(
                s[f"{axis_key.value}tick.minor.width"]
            ),
            major_pad=self._parse_numeric_or_str(s[f"{axis_key.value}tick.major.pad"]),
            minor_pad=self._parse_numeric_or_str(s[f"{axis_key.value}tick.minor.pad"]),
            direction=TickDirection.from_str(s[f"{axis_key.value}tick.direction"]),
            color=s[f"{axis_key.value}tick.color"],
            labelcolor=s[f"{axis_key.value}tick.labelcolor"],
            labelsize=self._parse_numeric_or_str(s[f"{axis_key.value}tick.labelsize"]),
            minor_visible=bool(s[f"{axis_key.value}tick.minor.visible"]),
            minor_ndivs=s[f"{axis_key.value}tick.minor.ndivs"],
        )

    def _create_spine(
        self, position: SpinePosition, is_visible: bool
    ) -> SpineProperties:
        s = self._current_style
        return SpineProperties(
            visible=is_visible,
            color=s["axes.edgecolor"],
            linewidth=self._parse_numeric_or_str(s["axes.linewidth"]),
            position=position,
        )

    def _create_grid(self) -> GridProperties:
        s = self._current_style
        return GridProperties(
            visible=bool(s["axes.grid"]),
            color=s["grid.color"],
            linestyle=s["grid.linestyle"],
            linewidth=self._parse_numeric_or_str(s["grid.linewidth"]),
            alpha=self._parse_numeric_or_str(s["grid.alpha"]),
        )

    def _create_axis(self, axis_key: AxisKey) -> AxisProperties:
        s = self._current_style
        return AxisProperties(
            ticks=self._create_ticks(axis_key),
            margin=self._parse_numeric_or_str(s[f"axes.{axis_key.value}margin"]),
            autolimit_mode=AutolimitMode.from_str(str(s["axes.autolimit_mode"])),
            use_offset=bool(s["axes.formatter.useoffset"]),
            offset_threshold=int(s["axes.formatter.offset_threshold"]),
            scientific_limits=tuple(int(x) for x in s["axes.formatter.limits"]),
            label=self._create_text(""),
            limits=(None, None),
        )

    def _create_cartesian_2d(self) -> Cartesian2DProperties:
        s = self._current_style
        return Cartesian2DProperties(
            xaxis=self._create_axis(AxisKey.X),
            yaxis=self._create_axis(AxisKey.Y),
            spines={
                SpinePosition.LEFT: self._create_spine(
                    SpinePosition.LEFT, bool(s["axes.spines.left"])
                ),
                SpinePosition.BOTTOM: self._create_spine(
                    SpinePosition.BOTTOM, bool(s["axes.spines.bottom"])
                ),
                SpinePosition.TOP: self._create_spine(
                    SpinePosition.TOP, bool(s["axes.spines.top"])
                ),
                SpinePosition.RIGHT: self._create_spine(
                    SpinePosition.RIGHT, bool(s["axes.spines.right"])
                ),
            },
            facecolor=str(s["axes.facecolor"]),
            axis_below=s["axes.axisbelow"],
            prop_cycle=list(s["axes.prop_cycle"].by_key()["color"]),
        )

    def _create_cartesian_3d(self) -> Cartesian3DProperties:
        s = self._current_style
        base = self._create_cartesian_2d()
        return Cartesian3DProperties(
            xaxis=base.xaxis,
            yaxis=base.yaxis,
            zaxis=self._create_axis(AxisKey.Z),
            spines=base.spines,  # TODO: 3D spine handling is more complex. This is a simplification.
            facecolor=base.facecolor,
            axis_below=base.axis_below,
            prop_cycle=base.prop_cycle,
            pane_colors={
                AxisKey.X: self._parse_rgba(s["axes3d.pane_color_x"]),
                AxisKey.Y: self._parse_rgba(s["axes3d.pane_color_y"]),
                AxisKey.Z: self._parse_rgba(s["axes3d.pane_color_z"]),
            },
        )

    def _create_polar(self) -> PolarProperties:
        return PolarProperties(
            theta_axis=self._create_axis(AxisKey.X),  # Maps x theme keys to theta
            r_axis=self._create_axis(AxisKey.Y),  # Maps y theme keys to r
            spine=self._create_spine(
                SpinePosition.BOTTOM, bool(self._current_style["axes.spines.bottom"])
            ),
        )

    def _parse_rgba(self, val: Any) -> tuple[float, float, float, float]:
        """Helper to ensure a value is a 4-tuple RGBA."""
        if not isinstance(val, (list, tuple)) or len(val) != 4:
            raise ValueError(f"Expected a 4-tuple RGBA value, got {val}")
        return tuple(val)
