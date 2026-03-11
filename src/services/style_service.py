import logging
import re
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
    
    Inheritance Rule (Path B): If a non-standard key (like 'ztick') is missing, 
    the service inherits the value from a related standard key (like 'xtick') 
    within the same theme.
    #TODO: THis file still contains hard coded default values
    """

    # Exhaustive list of standard Matplotlib keys required for every theme.
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
        # Ticks (Standard X and Y)
        "xtick.major.size",
        "xtick.minor.size",
        "xtick.major.width",
        "xtick.minor.width",
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
        "axes3d.xaxis.panecolor",
        "axes3d.yaxis.panecolor",
        "axes3d.zaxis.panecolor",
    ]

    def __init__(self, event_aggregator: EventAggregator):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._event_aggregator: EventAggregator = event_aggregator
        self._current_style: dict[str, Any] = dict(mpl.rcParams)

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
            ArtistType.BOXPLOT: self._create_line_artist,
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
            # 1. Strict Validation: Check for explicit key presence in the raw file
            # This avoids Matplotlib's default-population behavior.
            with open(style_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
            self._validate_style_raw(raw_content)
            
            # 2. Matplotlib Parsing: Handle normalization and complex types
            new_style = mpl.RcParams()
            new_style.update(mpl.rc_params_from_file(style_path))
            self._current_style = dict(new_style)
            self.logger.info(f"Successfully loaded and validated style: {style_path}")
        except Exception as e:
            self.logger.error(f"Failed to load style {style_path}: {e}")
            raise ThemeIncompleteError(f"Style validation failed for {style_path}: {e}")

    def _validate_style_raw(self, raw_content: str):
        """Checks if all required keys are explicitly defined in the raw style string."""
        # Normalize: Remove comments and whitespace
        lines = [re.sub(r"#.*", "", line).strip() for line in raw_content.splitlines()]
        defined_keys = {line.split(":")[0].strip() for line in lines if ":" in line}
        
        missing = [key for key in self.REQUIRED_KEYS if key not in defined_keys]
        if missing:
            raise ThemeIncompleteError(f"Theme missing required keys: {missing}")

    def create_properties_from_sparse(self, overrides: dict) -> PlotProperties:
        """Creates a fully initialized PlotProperties tree from base theme + overrides."""
        p_type_raw = overrides.get("plot_type", ArtistType.LINE)
        try:
            p_type = ArtistType(p_type_raw) if not isinstance(p_type_raw, ArtistType) else p_type_raw
        except ValueError:
            p_type = ArtistType.LINE

        base_props = self.create_themed_properties(p_type)
        self.hydrate(base_props, overrides)
        return base_props

    def hydrate(self, base_obj: Any, overrides: dict):
        """Recursively merges a sparse dictionary into a typed dataclass tree."""
        for key, value in overrides.items():
            if not hasattr(base_obj, key) or key.startswith("_"):
                continue

            current_attr = getattr(base_obj, key)

            if isinstance(value, dict) and is_dataclass(current_attr):
                self.hydrate(current_attr, value)
            elif isinstance(value, dict) and isinstance(current_attr, dict):
                for sub_key, sub_value in value.items():
                    resolved_key = self._resolve_key_type(type(current_attr), sub_key)
                    if resolved_key in current_attr:
                        self.hydrate(current_attr[resolved_key], sub_value)
            elif isinstance(value, list) and isinstance(current_attr, list):
                self._hydrate_list(base_obj, key, current_attr, value)
            else:
                self._apply_leaf(base_obj, key, value)

    def _resolve_key_type(self, dict_type: Any, key: str) -> Any:
        try:
            return SpinePosition(key)
        except ValueError:
            pass
        return key

    def _hydrate_list(self, parent: Any, attr_name: str, base_list: list, overrides: list):
        if attr_name == "artists":
            new_artists = []
            for a_overrides in overrides:
                a_type_raw = a_overrides.get("artist_type", ArtistType.LINE)
                try:
                    a_type = ArtistType(a_type_raw) if not isinstance(a_type_raw, ArtistType) else a_type_raw
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
        from enum import Enum
        from typing import get_type_hints

        type_hints = get_type_hints(type(obj))
        expected_type = type_hints.get(key)

        if expected_type:
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
            self.logger.error(f"Hydration: Failed to set {key} on {type(obj).__name__}: {e}")

    def create_themed_properties(self, plot_type: ArtistType) -> PlotProperties:
        """Factory method to create a fully initialized PlotProperties tree from the current theme."""
        if not self._current_style:
            raise RuntimeError("StyleService: No style loaded.")

        if plot_type == ArtistType.SURFACE:
            coords = self._create_cartesian_3d()
        elif plot_type == ArtistType.POLAR_LINE:
            coords = self._create_polar()
        else:
            coords = self._create_cartesian_2d()

        factory = self._ARTIST_FACTORIES.get(plot_type)
        artists = [factory()] if factory else []

        return PlotProperties(
            titles={"left": self._create_text(""), "center": self._create_text(""), "right": self._create_text("")},
            coords=coords,
            legend={},
            artists=artists,
        )

    def _on_initialize_theme_requested(self, node_id: str, plot_type: ArtistType):
        try:
            props = self.create_themed_properties(plot_type)
            self._event_aggregator.publish(Events.CHANGE_PLOT_NODE_PROPERTY_REQUESTED, node_id=node_id, path="plot_properties", value=props)
        except Exception as e:
            self.logger.error(f"StyleService: Theme error for node {node_id}: {e}")

    def _on_hydrate_properties_requested(self, node_id: str, overrides: dict):
        try:
            # 1. Check for 'Full Property Tree' (Project Load case)
            core_keys = ("titles", "coords", "legend", "artists")
            if all(k in overrides for k in core_keys):
                self.logger.debug(f"StyleService: Full property tree detected for {node_id}. Reconstructing.")
                props = PlotProperties.from_dict(overrides)
            else:
                # 2. 'Sparse Template' (Template case)
                artist_list = overrides.get("artists", [{}])
                artist_data = artist_list[0] if artist_list else {}
                artist_type_raw = artist_data.get("artist_type", ArtistType.LINE)
                try:
                    artist_type = ArtistType(artist_type_raw) if not isinstance(artist_type_raw, ArtistType) else artist_type_raw
                except ValueError:
                    artist_type = ArtistType.LINE

                props = self.create_themed_properties(artist_type)
                self.hydrate(props, overrides)
            
            self._event_aggregator.publish(Events.CHANGE_PLOT_NODE_PROPERTY_REQUESTED, node_id=node_id, path="plot_properties", value=props)
        except Exception as e:
            self.logger.error(f"StyleService: Hydration failed for node {node_id}: {e}", exc_info=True)

    def _parse_numeric_or_str(self, val: Any) -> Any:
        try:
            return float(val)
        except (ValueError, TypeError):
            return val

    # --- Factories ---

    def _create_line_artist(self) -> LineArtistProperties:
        return LineArtistProperties(visible=True, zorder=1, visuals=self._create_line())

    def _create_scatter_artist(self) -> ScatterArtistProperties:
        return ScatterArtistProperties(visible=True, zorder=1, visuals=self._create_line())

    def _create_bar_artist(self) -> BarArtistProperties:
        return BarArtistProperties(visible=True, zorder=1, visuals=self._create_patch(), width=0.8, align="center")

    def _create_image_artist(self) -> ImageArtistProperties:
        return ImageArtistProperties(visible=True, zorder=1, visuals=self._create_mappable())

    def _create_mesh_artist(self) -> MeshArtistProperties:
        return MeshArtistProperties(visible=True, zorder=1, visuals=self._create_mappable())

    def _create_contour_artist(self) -> ContourArtistProperties:
        s = self._current_style
        return ContourArtistProperties(visible=True, zorder=1, visuals=self._create_mappable(), linewidth=self._parse_numeric_or_str(s["contour.linewidth"]), levels=10, filled=True)

    def _create_histogram_artist(self) -> HistogramArtistProperties:
        s = self._current_style
        return HistogramArtistProperties(visible=True, zorder=1, visuals=self._create_patch(), bins=s.get("hist.bins", "auto"), density=False, cumulative=False)

    def _create_stair_artist(self) -> StairArtistProperties:
        return StairArtistProperties(visible=True, zorder=1, visuals=self._create_line(), baseline=0.0, fill=False)

    def _create_font(self) -> FontProperties:
        s = self._current_style
        family = s["font.family"]
        return FontProperties(family=str(family[0] if isinstance(family, list) else family), style=str(s["font.style"]), variant=str(s["font.variant"]), weight=str(s["font.weight"]), stretch=str(s["font.stretch"]), size=self._parse_numeric_or_str(s["font.size"]))

    def _create_text(self, content: str) -> TextProperties:
        s = self._current_style
        return TextProperties(text=content, color=s["text.color"], font=self._create_font())

    def _create_line(self) -> LineProperties:
        s = self._current_style
        return LineProperties(linewidth=self._parse_numeric_or_str(s["lines.linewidth"]), linestyle=s["lines.linestyle"], color=s["lines.color"], marker=str(s["lines.marker"]), markerfacecolor=s["lines.markerfacecolor"], markeredgecolor=s["lines.markeredgecolor"], markeredgewidth=self._parse_numeric_or_str(s["lines.markeredgewidth"]), markersize=self._parse_numeric_or_str(s["lines.markersize"]))

    def _create_patch(self) -> PatchProperties:
        s = self._current_style
        return PatchProperties(facecolor=s["patch.facecolor"], edgecolor=s["patch.edgecolor"], linewidth=self._parse_numeric_or_str(s["patch.linewidth"]), force_edgecolor=bool(s["patch.force_edgecolor"]))

    def _create_mappable(self) -> ScalarMappableProperties:
        s = self._current_style
        return ScalarMappableProperties(cmap=str(s["image.cmap"]), norm_min=None, norm_max=None, has_colorbar=False)

    def _create_ticks(self, axis_key: AxisKey) -> TickProperties:
        s = self._current_style
        # Path B: Smart Inheritance
        # If ztick keys are missing (non-standard), inherit from xtick within the same theme.
        prefix = axis_key.value if f"{axis_key.value}tick.major.size" in s else "x"
        
        return TickProperties(
            major_size=self._parse_numeric_or_str(s[f"{prefix}tick.major.size"]),
            minor_size=self._parse_numeric_or_str(s[f"{prefix}tick.minor.size"]),
            major_width=self._parse_numeric_or_str(s[f"{prefix}tick.major.width"]),
            minor_width=self._parse_numeric_or_str(s[f"{prefix}tick.minor.width"]),
            major_pad=self._parse_numeric_or_str(s.get(f"{prefix}tick.major.pad", 3.5)),
            minor_pad=self._parse_numeric_or_str(s.get(f"{prefix}tick.minor.pad", 3.4)),
            direction=TickDirection.from_str(s[f"{prefix}tick.direction"]),
            color=s[f"{prefix}tick.color"],
            labelcolor=s[f"{prefix}tick.labelcolor"],
            labelsize=self._parse_numeric_or_str(s[f"{prefix}tick.labelsize"]),
            minor_visible=bool(s[f"{prefix}tick.minor.visible"]),
            minor_ndivs=s.get(f"{prefix}tick.minor.ndivs", 2),
        )

    def _create_spine(self, position: SpinePosition, is_visible: bool) -> SpineProperties:
        s = self._current_style
        return SpineProperties(visible=is_visible, color=s["axes.edgecolor"], linewidth=self._parse_numeric_or_str(s["axes.linewidth"]), position=position)

    def _create_grid(self) -> GridProperties:
        s = self._current_style
        return GridProperties(visible=bool(s["axes.grid"]), color=s["grid.color"], linestyle=s["grid.linestyle"], linewidth=self._parse_numeric_or_str(s["grid.linewidth"]), alpha=self._parse_numeric_or_str(s["grid.alpha"]))

    def _create_axis(self, axis_key: AxisKey) -> AxisProperties:
        s = self._current_style
        # Path B: Inherit missing zmargin from xmargin if not explicitly in theme
        margin_key = f"axes.{axis_key.value}margin"
        margin = self._parse_numeric_or_str(s.get(margin_key, s.get("axes.xmargin", 0.0)))
        
        return AxisProperties(
            ticks=self._create_ticks(axis_key),
            margin=margin,
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
                SpinePosition.LEFT: self._create_spine(SpinePosition.LEFT, bool(s["axes.spines.left"])),
                SpinePosition.BOTTOM: self._create_spine(SpinePosition.BOTTOM, bool(s["axes.spines.bottom"])),
                SpinePosition.TOP: self._create_spine(SpinePosition.TOP, bool(s["axes.spines.top"])),
                SpinePosition.RIGHT: self._create_spine(SpinePosition.RIGHT, bool(s["axes.spines.right"])),
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
            spines=base.spines,
            facecolor=base.facecolor,
            axis_below=base.axis_below,
            prop_cycle=base.prop_cycle,
            pane_colors={
                AxisKey.X: self._parse_rgba(s["axes3d.xaxis.panecolor"]),
                AxisKey.Y: self._parse_rgba(s["axes3d.yaxis.panecolor"]),
                AxisKey.Z: self._parse_rgba(s["axes3d.zaxis.panecolor"]),
            },
        )

    def _create_polar(self) -> PolarProperties:
        return PolarProperties(
            theta_axis=self._create_axis(AxisKey.X),
            r_axis=self._create_axis(AxisKey.Y),
            spine=self._create_spine(SpinePosition.BOTTOM, bool(self._current_style["axes.spines.bottom"])),
        )

    def _parse_rgba(self, val: Any) -> tuple[float, float, float, float]:
        if not isinstance(val, (list, tuple)) or len(val) != 4:
            raise ValueError(f"Expected 4-tuple RGBA, got {val}")
        return tuple(val)
