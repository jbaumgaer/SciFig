import logging
from typing import Any
import matplotlib as mpl
from src.models.plots.plot_types import ArtistType, AutolimitMode, AxisKey, CoordinateSystem, SpinePosition, TickDirection
from src.models.plots.plot_properties import (
    PlotProperties, TextProperties, FontProperties, LineProperties,
    PatchProperties, TickProperties, SpineProperties, GridProperties,
    AxisProperties, Cartesian2DProperties, Cartesian3DProperties, PolarProperties,
    LineArtistProperties, ScatterArtistProperties, BarArtistProperties,
    ImageArtistProperties, MeshArtistProperties, ContourArtistProperties,
    HistogramArtistProperties, StairArtistProperties, ScalarMappableProperties
)

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
        "font.family", "font.style", "font.variant", "font.weight", "font.stretch", "font.size",
        # Text
        "text.color",
        # Lines
        "lines.linewidth", "lines.linestyle", "lines.color", "lines.marker",
        "lines.markerfacecolor", "lines.markeredgecolor", "lines.markeredgewidth",
        "lines.markersize",
        # Patch
        "patch.facecolor", "patch.edgecolor", "patch.linewidth", "patch.force_edgecolor",
        # Ticks (TODO: z axis cannot be handled right now)
        "xtick.major.size", "xtick.minor.size", "xtick.major.width", "xtick.minor.width",
        "xtick.major.pad", "xtick.minor.pad", "xtick.direction", "xtick.color",
        "xtick.labelcolor", "xtick.labelsize", "xtick.minor.visible", "xtick.minor.ndivs",
        "ytick.major.size", "ytick.minor.size", "ytick.major.width", "ytick.minor.width",
        "ytick.major.pad", "ytick.minor.pad", "ytick.direction", "ytick.color",
        "ytick.labelcolor", "ytick.labelsize", "ytick.minor.visible", "ytick.minor.ndivs",
        # Spines
        "axes.edgecolor", "axes.linewidth", "axes.spines.bottom", "axes.spines.left",
        "axes.spines.top", "axes.spines.right",
        # Grid
        "axes.grid", "grid.color", "grid.linestyle", "grid.linewidth", "grid.alpha",
        # Axis/Coordinates
        "axes.facecolor", "axes.axisbelow", "axes.prop_cycle", "axes.xmargin", "axes.ymargin",
        "axes.autolimit_mode", "axes.formatter.useoffset", "axes.formatter.offset_threshold",
        "axes.formatter.limits",
        # Specialized Artist Keys
        "image.cmap", "contour.linewidth", "hist.bins",
        # 3D Specific
        "axes3d.pane_color_x", "axes3d.pane_color_y", "axes3d.pane_color_z"
    ]

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Initialize with current matplotlib defaults as baseline
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
            ArtistType.BOXPLOT: self._create_line_artist, # Placeholder
        }

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

    def _validate_style(self, style: dict[str, Any]):
        """Perform an exhaustive check for required keys. No defaults allowed."""
        missing = [k for k in self.REQUIRED_KEYS if k not in style]
        if missing:
            raise ThemeIncompleteError(f"Theme is incomplete. Missing required keys: {missing}")

    def create_themed_properties(self, plot_type: ArtistType) -> PlotProperties:
        """Factory method to create a fully initialized PlotProperties tree from the current theme."""
        if not self._current_style:
            raise RuntimeError("StyleService: No style loaded. Call load_style() first.")
            
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
                "right": self._create_text("")
            },
            coords=coords,
            legend={},
            artists=artists
        )

    # --- Artist Factories ---
    #TODO: Lines are currently treated on a different footing. Because the linewidth can be set globally, I can take the global value and inherit it into LineProperties.
    # However, for other kwargs that would be passed to ax.plot, I cannot do that. Maybe I need to think about why this distinction exists 


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
            width=0.8, # These are defaults for now because matplotlib doesn't have these RC params
            align="center"
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
            linewidth=float(s["contour.linewidth"]),
            levels=10, #Defaults for now because matplotlib doesn't provide them
            filled=True
        )

    def _create_histogram_artist(self) -> HistogramArtistProperties:
        s = self._current_style
        return HistogramArtistProperties(
            visible=True, 
            zorder=1,
            visuals=self._create_patch(),
            bins=s["hist.bins"], # Can be str or int
            density=bool(s["hist.density"]),
            cumulative=bool(s["hist.cumulative"])
        )

    def _create_stair_artist(self) -> StairArtistProperties:
        s = self._current_style
        return StairArtistProperties(
            visible=True, 
            zorder=1,
            visuals=self._create_line(),
            baseline=0.0, # Default for now because matplotlib doesn't have this RC param
            fill=False
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
            size=float(s["font.size"])
        )

    def _create_text(self, content: str) -> TextProperties:
        s = self._current_style
        return TextProperties(
            text=content,
            color=str(s["text.color"]),
            font=self._create_font(),
        )

    def _create_line(self) -> LineProperties:
        s = self._current_style
        return LineProperties(
            linewidth=float(s["lines.linewidth"]),
            linestyle=str(s["lines.linestyle"]),
            color=str(s["lines.color"]),
            marker=str(s["lines.marker"]),
            markerfacecolor=str(s["lines.markerfacecolor"]),
            markeredgecolor=str(s["lines.markeredgecolor"]),
            markeredgewidth=float(s["lines.markeredgewidth"]),
            markersize=float(s["lines.markersize"]),
        )

    def _create_patch(self) -> PatchProperties:
        s = self._current_style
        return PatchProperties(
            facecolor=str(s["patch.facecolor"]),
            edgecolor=str(s["patch.edgecolor"]),
            linewidth=float(s["patch.linewidth"]),
            force_edgecolor=bool(s["patch.force_edgecolor"]),
        )

    def _create_mappable(self) -> ScalarMappableProperties:
        s = self._current_style
        return ScalarMappableProperties(
            cmap=str(s["image.cmap"]),
            norm_min=None, norm_max=None,
            has_colorbar=False
        ) #TODO: No default values

    # --- Coordinate Factories ---

    def _create_ticks(self, axis_key: AxisKey) -> TickProperties:
        s = self._current_style
        return TickProperties(
            major_size=float(s[f"{axis_key.value}tick.major.size"]),
            minor_size=float(s[f"{axis_key.value}tick.minor.size"]),
            major_width=float(s[f"{axis_key.value}tick.major.width"]),
            minor_width=float(s[f"{axis_key.value}tick.minor.width"]),
            major_pad=float(s[f"{axis_key.value}tick.major.pad"]),
            minor_pad=float(s[f"{axis_key.value}tick.minor.pad"]),
            direction=TickDirection.from_str(s[f"{axis_key.value}tick.direction"]),
            color=str(s[f"{axis_key.value}tick.color"]),
            labelcolor=str(s[f"{axis_key.value}tick.labelcolor"]),
            labelsize=float(s[f"{axis_key.value}tick.labelsize"]),
            minor_visible=bool(s[f"{axis_key.value}tick.minor.visible"]),
            minor_ndivs=int(s[f"{axis_key.value}tick.minor.ndivs"])
        )

    def _create_spine(self, position: SpinePosition, is_visible: bool) -> SpineProperties:
        s = self._current_style
        return SpineProperties(
            visible=is_visible,
            color=str(s["axes.edgecolor"]),
            linewidth=float(s["axes.linewidth"]),
            position=position
        )

    def _create_grid(self) -> GridProperties:
        s = self._current_style
        return GridProperties(
            visible=bool(s["axes.grid"]),
            color=str(s["grid.color"]),
            linestyle=str(s["grid.linestyle"]),
            linewidth=float(s["grid.linewidth"]),
            alpha=float(s["grid.alpha"]),
        )

    def _create_axis(self, axis_key: AxisKey) -> AxisProperties:
        s = self._current_style
        return AxisProperties(
            ticks=self._create_ticks(axis_key),
            margin=float(s[f"axes.{axis_key.value}margin"]),
            autolimit_mode=AutolimitMode.from_str(str(s["axes.autolimit_mode"])),
            use_offset=bool(s["axes.formatter.useoffset"]),
            offset_threshold=int(s["axes.formatter.offset_threshold"]),
            scientific_limits=tuple(int(x) for x in s["axes.formatter.limits"])
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
                SpinePosition.RIGHT: self._create_spine(SpinePosition.RIGHT, bool(s["axes.spines.right"]))
            },
            facecolor=str(s["axes.facecolor"]),
            axis_below=s["axes.axisbelow"],
            prop_cycle=list(s["axes.prop_cycle"].by_key()["color"])
        )

    def _create_cartesian_3d(self) -> Cartesian3DProperties:
        s = self._current_style
        base = self._create_cartesian_2d()
        return Cartesian3DProperties(
            xaxis=base.xaxis, yaxis=base.yaxis,
            zaxis=self._create_axis(AxisKey.Z),
            spines=base.spines, #TODO: 3D spine handling is more complex. This is a simplification.
            facecolor=base.facecolor,
            axis_below=base.axis_below,
            prop_cycle=base.prop_cycle,
            pane_colors={
                AxisKey.X: self._parse_rgba(s["axes3d.pane_color_x"]),
                AxisKey.Y: self._parse_rgba(s["axes3d.pane_color_y"]),
                AxisKey.Z: self._parse_rgba(s["axes3d.pane_color_z"])
            }
        )

    def _create_polar(self) -> PolarProperties:
        return PolarProperties(
            theta_axis=self._create_axis(AxisKey.X), # Maps x theme keys to theta
            r_axis=self._create_axis(AxisKey.Y),     # Maps y theme keys to r
            spine=self._create_spine(SpinePosition.BOTTOM, bool(self._current_style["axes.spines.bottom"]))
        )

    def _parse_rgba(self, val: Any) -> tuple[float, float, float, float]:
        """Helper to ensure a value is a 4-tuple RGBA."""
        if not isinstance(val, (list, tuple)) or len(val) != 4:
            raise ValueError(f"Expected a 4-tuple RGBA value, got {val}")
        return tuple(val)
