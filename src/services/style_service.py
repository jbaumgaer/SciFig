import logging
from typing import Any, Dict, Optional, List
import matplotlib as mpl
from src.models.plots.plot_types import PlotType
from src.models.plots.plot_properties import (
    PlotProperties, TextProperties, FontProperties, LineProperties,
    PatchProperties, TickProperties, SpineProperties, GridProperties,
    AxisProperties, Cartesian2DProperties
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

    # Expanded list of required keys covering the entire property tree.
    # Note: Some keys are custom scifig-specific keys (e.g., text.va) to ensure strictness.
    REQUIRED_KEYS = [
        # Font
        "font.family", "font.style", "font.variant", "font.weight", "font.stretch", "font.size",
        # Text
        "text.color", "text.alpha", "text.rotation", "text.va", "text.ha", "text.parse_math",
        # Lines
        "lines.linewidth", "lines.linestyle", "lines.color", "lines.marker",
        "lines.markerfacecolor", "lines.markeredgecolor", "lines.markeredgewidth",
        "lines.markersize", "lines.antialiased", "lines.alpha",
        # Patch
        "patch.facecolor", "patch.edgecolor", "patch.linewidth", "patch.alpha",
        "patch.force_edgecolor", "patch.antialiased", "patch.hatch",
        # Ticks (X and Y)
        "xtick.major.size", "xtick.minor.size", "xtick.major.width", "xtick.minor.width",
        "xtick.major.pad", "xtick.minor.pad", "xtick.direction", "xtick.color",
        "xtick.labelcolor", "xtick.labelsize", "xtick.minor.visible",
        "ytick.major.size", "ytick.minor.size", "ytick.major.width", "ytick.minor.width",
        "ytick.major.pad", "ytick.minor.pad", "ytick.direction", "ytick.color",
        "ytick.labelcolor", "ytick.labelsize", "ytick.minor.visible",
        # Spines
        "axes.edgecolor", "axes.linewidth", "axes.spines.visible", "axes.spines.position_type", "axes.spines.position_val",
        # Grid
        "axes.grid", "grid.color", "grid.linestyle", "grid.linewidth", "grid.alpha",
        # Axis/Coordinates
        "axes.facecolor", "axes.axisbelow", "axes.prop_cycle", "axes.xmargin", "axes.ymargin",
        "axes.autolimit_mode", "axes.formatter.useoffset", "axes.formatter.offset_threshold",
        "axes.formatter.limits_min", "axes.formatter.limits_max"
    ]

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._current_style: Dict[str, Any] = {}

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

    def _validate_style(self, style: Dict[str, Any]):
        """Perform an exhaustive check for required keys. No defaults allowed."""
        missing = [k for k in self.REQUIRED_KEYS if k not in style]
        if missing:
            raise ThemeIncompleteError(f"Theme is incomplete. Missing required keys: {missing}")

    def create_themed_properties(self, plot_type: PlotType) -> PlotProperties:
        """Factory method to create a fully initialized PlotProperties tree from the current theme."""
        if not self._current_style:
            raise RuntimeError("StyleService: No style loaded. Call load_style() first.")
            
        return PlotProperties(
            titles={
                "left": self._create_text(""),
                "center": self._create_text(""),
                "right": self._create_text("")
            },
            coords=self._create_cartesian_2d(),
            legend={},
            plot_type=plot_type,
            artists=[]
        )

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
            alpha=float(s["text.alpha"]),
            font=self._create_font(),
            rotation=float(s["text.rotation"]),
            va=str(s["text.va"]),
            ha=str(s["text.ha"]),
            parse_math=bool(s["text.parse_math"])
        )

    def _create_ticks(self, prefix: str) -> TickProperties:
        s = self._current_style
        return TickProperties(
            major_size=float(s[f"{prefix}tick.major.size"]),
            minor_size=float(s[f"{prefix}tick.minor.size"]),
            major_width=float(s[f"{prefix}tick.major.width"]),
            minor_width=float(s[f"{prefix}tick.minor.width"]),
            major_pad=float(s[f"{prefix}tick.major.pad"]),
            minor_pad=float(s[f"{prefix}tick.minor.pad"]),
            direction=str(s[f"{prefix}tick.direction"]),
            color=str(s[f"{prefix}tick.color"]),
            labelcolor=str(s[f"{prefix}tick.labelcolor"]),
            labelsize=float(s[f"{prefix}tick.labelsize"]),
            minor_visible=bool(s[f"{prefix}tick.minor.visible"]),
            major_top=True,
            major_bottom=True,
            minor_top=True,
            minor_bottom=True,
            minor_ndivs=4 # TODO: Default value is not good
        )

    def _create_spine(self) -> SpineProperties:
        s = self._current_style
        return SpineProperties(
            visible=bool(s["axes.spines.visible"]),
            color=str(s["axes.edgecolor"]),
            linewidth=float(s["axes.linewidth"]),
            position=(str(s["axes.spines.position_type"]), float(s["axes.spines.position_val"]))
        )

    def _create_grid(self) -> GridProperties:
        s = self._current_style
        return GridProperties(
            visible=bool(s["axes.grid"]),
            color=str(s["grid.color"]),
            linestyle=str(s["grid.linestyle"]),
            linewidth=float(s["grid.linewidth"]),
            alpha=float(s["grid.alpha"]),
            axis="both", # TODO: Default value is not good
            which="major" # TODO: Default value is not good
        )

    def _create_axis(self, prefix: str) -> AxisProperties:
        s = self._current_style
        return AxisProperties(
            label=self._create_text(""),
            limits=(None, None),
            scale="linear", # TODO: Default value is not good
            ticks=self._create_ticks(prefix),
            grid=self._create_grid(),
            margin=float(s[f"axes.{prefix}margin"]),
            autolimit_mode=str(s["axes.autolimit_mode"]),
            use_offset=bool(s["axes.formatter.useoffset"]),
            offset_threshold=int(s["axes.formatter.offset_threshold"]),
            scientific_limits=(int(s["axes.formatter.limits_min"]), int(s["axes.formatter.limits_max"]))
        )

    def _create_cartesian_2d(self) -> Cartesian2DProperties:
        s = self._current_style
        return Cartesian2DProperties(
            xaxis=self._create_axis("x"),
            yaxis=self._create_axis("y"),
            spines={
                "left": self._create_spine(),
                "bottom": self._create_spine(),
                "top": self._create_spine(),
                "right": self._create_spine()
            },
            facecolor=str(s["axes.facecolor"]),
            axis_below=s["axes.axisbelow"],
            prop_cycle=list(s["axes.prop_cycle"].by_key()["color"])
        )
