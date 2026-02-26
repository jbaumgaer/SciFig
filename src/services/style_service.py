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
    """Raised when an .mplstyle file is missing required keys."""
    pass

class StyleService:
    """
    The Mandatory Factory for plot properties.
    Resolves flat .mplstyle keys into hierarchical dataclasses.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Initialize with default matplotlib rcParams
        self._current_style: Dict[str, Any] = dict(mpl.rcParams)

    def load_style(self, style_path: str):
        """Loads a new .mplstyle file and validates its completeness."""
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
        """
        Ensures all keys required for the 'Strict' dataclasses are present.
        This is a fail-fast check.
        """
        required_keys = [
            "font.family", "font.size", "text.color",
            "lines.linewidth", "lines.color", "patch.facecolor",
            "axes.facecolor", "axes.edgecolor", "axes.linewidth",
            "xtick.major.size", "xtick.major.width", "xtick.direction",
            "grid.color", "grid.linestyle"
        ]
        missing = [k for k in required_keys if k not in style]
        if missing:
            raise ThemeIncompleteError(f"Missing required style keys: {missing}")

    def create_themed_properties(self, plot_type: PlotType) -> PlotProperties:
        """
        Factory method to create a fully initialized PlotProperties tree
        derived from the current style.
        """
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
        # Font family is often a list in rcParams
        family = s["font.family"]
        if isinstance(family, list):
            family = family[0]
        
        return FontProperties(
            family=str(family),
            style=str(s.get("font.style", "normal")),
            variant=str(s.get("font.variant", "normal")),
            weight=str(s.get("font.weight", "normal")),
            stretch=str(s.get("font.stretch", "normal")),
            size=float(s["font.size"])
        )

    def _create_text(self, content: str) -> TextProperties:
        s = self._current_style
        return TextProperties(
            text=content,
            color=str(s["text.color"]),
            alpha=1.0,
            font=self._create_font(),
            rotation=0.0,
            va="baseline",
            ha="center",
            parse_math=bool(s.get("text.parse_math", True))
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
            antialiased=bool(s["lines.antialiased"]),
            alpha=1.0
        )

    def _create_ticks(self, axis_prefix: str = "x") -> TickProperties:
        s = self._current_style
        # We use 'x' keys as defaults for the hierarchy, can be customized per axis if needed
        return TickProperties(
            major_size=float(s[f"{axis_prefix}tick.major.size"]),
            minor_size=float(s[f"{axis_prefix}tick.minor.size"]),
            major_width=float(s[f"{axis_prefix}tick.major.width"]),
            minor_width=float(s[f"{axis_prefix}tick.minor.width"]),
            major_pad=float(s[f"{axis_prefix}tick.major.pad"]),
            minor_pad=float(s[f"{axis_prefix}tick.minor.pad"]),
            direction=str(s[f"{axis_prefix}tick.direction"]),
            color=str(s[f"{axis_prefix}tick.color"]),
            labelcolor=str(s[f"{axis_prefix}tick.labelcolor"] if s[f"{axis_prefix}tick.labelcolor"] != "inherit" else s[f"{axis_prefix}tick.color"]),
            labelsize=float(s[f"{axis_prefix}tick.labelsize"]) if isinstance(s[f"{axis_prefix}tick.labelsize"], (int, float)) else 10.0,
            minor_visible=bool(s[f"{axis_prefix}tick.minor.visible"]),
            major_top=True, major_bottom=True,
            minor_top=True, minor_bottom=True,
            minor_ndivs=4
        )

    def _create_spine(self) -> SpineProperties:
        s = self._current_style
        return SpineProperties(
            visible=True,
            color=str(s["axes.edgecolor"]),
            linewidth=float(s["axes.linewidth"]),
            position=("outward", 0.0)
        )

    def _create_grid(self) -> GridProperties:
        s = self._current_style
        return GridProperties(
            visible=bool(s["axes.grid"]),
            color=str(s["grid.color"]),
            linestyle=str(s["grid.linestyle"]),
            linewidth=float(s["grid.linewidth"]),
            alpha=float(s.get("grid.alpha", 1.0)),
            axis="both",
            which="major"
        )

    def _create_axis(self, prefix: str = "x") -> AxisProperties:
        s = self._current_style
        return AxisProperties(
            label=self._create_text(""),
            limits=(None, None),
            scale="linear",
            ticks=self._create_ticks(prefix),
            grid=self._create_grid(),
            margin=float(s[f"axes.{prefix}margin"]),
            autolimit_mode=str(s["axes.autolimit_mode"]),
            use_offset=True,
            offset_threshold=4,
            scientific_limits=(-7, 7)
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
