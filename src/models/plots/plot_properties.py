from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Union
from src.models.plots.plot_types import PlotType

@dataclass
class FontProperties:
    family: str
    style: str
    variant: str
    weight: str
    stretch: str
    size: float

@dataclass
class TextProperties:
    text: str
    color: str
    alpha: float
    font: FontProperties
    rotation: float
    va: str
    ha: str
    parse_math: bool

@dataclass
class LineProperties:
    linewidth: float
    linestyle: str
    color: str
    marker: str
    markerfacecolor: str
    markeredgecolor: str
    markeredgewidth: float
    markersize: float
    antialiased: bool
    alpha: float

@dataclass
class PatchProperties:
    facecolor: str
    edgecolor: str
    linewidth: float
    alpha: float
    force_edgecolor: bool
    antialiased: bool
    hatch: Optional[str]

@dataclass
class TickProperties:
    major_size: float
    minor_size: float
    major_width: float
    minor_width: float
    major_pad: float
    minor_pad: float
    direction: str
    color: str
    labelcolor: str
    labelsize: float
    minor_visible: bool
    major_top: bool
    major_bottom: bool
    minor_top: bool
    minor_bottom: bool
    minor_ndivs: int

@dataclass
class SpineProperties:
    visible: bool
    color: str
    linewidth: float
    position: tuple[str, float]

@dataclass
class GridProperties:
    visible: bool
    color: str
    linestyle: str
    linewidth: float
    alpha: float
    axis: str
    which: str

@dataclass
class AxisProperties:
    label: TextProperties
    limits: tuple[Optional[float], Optional[float]]
    scale: str
    ticks: TickProperties
    grid: GridProperties
    margin: float
    autolimit_mode: str
    use_offset: bool
    offset_threshold: int
    scientific_limits: tuple[int, int]

@dataclass
class Cartesian2DProperties:
    xaxis: AxisProperties
    yaxis: AxisProperties
    spines: Dict[str, SpineProperties]
    facecolor: str
    axis_below: Union[bool, str]
    prop_cycle: List[str]

@dataclass
class Cartesian3DProperties(Cartesian2DProperties):
    zaxis: AxisProperties
    pane_colors: Dict[str, tuple[float, float, float, float]]

@dataclass
class PolarProperties:
    theta_axis: AxisProperties
    r_axis: AxisProperties
    spine: SpineProperties

@dataclass
class ScalarMappableProperties:
    cmap: str
    norm_min: Optional[float]
    norm_max: Optional[float]
    has_colorbar: bool

# --- Artist Level Properties (Data + Visuals) ---

@dataclass
class BaseArtistProperties:
    label: str
    visible: bool
    zorder: int

@dataclass
class LineArtistProperties(BaseArtistProperties):
    visuals: LineProperties
    x_column: str
    y_column: str

@dataclass
class ScatterArtistProperties(BaseArtistProperties):
    visuals: LineProperties
    x_column: str
    y_column: str
    size_column: Optional[str] = None
    color_column: Optional[str] = None

@dataclass
class BarArtistProperties(BaseArtistProperties):
    visuals: PatchProperties
    x_column: str
    y_column: str
    width: float
    align: str

@dataclass
class ImageArtistProperties(BaseArtistProperties):
    visuals: ScalarMappableProperties
    data_column: str  # Column containing 2D matrix/array
    interpolation: str
    origin: str
    extent: Optional[tuple[float, ...]]

@dataclass
class MeshArtistProperties(BaseArtistProperties):
    visuals: ScalarMappableProperties
    x_column: str
    y_column: str
    z_column: str
    shading: str
    antialiased: bool

@dataclass
class ContourArtistProperties(BaseArtistProperties):
    visuals: ScalarMappableProperties
    z_column: str
    levels: Union[int, List[float]]
    filled: bool

@dataclass
class HistogramArtistProperties(BaseArtistProperties):
    visuals: PatchProperties
    data_column: str
    bins: Union[int, str]
    density: bool
    cumulative: bool

@dataclass
class StairArtistProperties(BaseArtistProperties):
    visuals: LineProperties
    data_column: str
    baseline: float
    fill: bool

@dataclass
class PlotProperties:
    """The root property tree for a single PlotNode."""
    titles: Dict[str, TextProperties] # 'left', 'center', 'right'
    coords: Union[Cartesian2DProperties, Cartesian3DProperties, PolarProperties]
    legend: Dict[str, Any]
    plot_type: PlotType
    artists: List[Any] = field(default_factory=list)
    _version: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlotProperties":
        # Implementation will be completed during the serialization refactor
        pass
