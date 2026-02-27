from dataclasses import dataclass, field, asdict, fields, is_dataclass
from typing import Optional, Any, Union, Type, TypeVar, get_type_hints
from src.models.plots.plot_types import ArtistType, AutolimitMode, CoordinateSystem, SpinePosition, TickDirection

T = TypeVar("T")

def _from_dict_recursive(cls: Type[T], data: Any) -> T:
    """Helper to recursively reconstruct dataclasses from dicts."""
    if not isinstance(data, dict):
        return data
    
    if is_dataclass(cls):
        type_hints = get_type_hints(cls)
        kwargs = {}
        for f in fields(cls):
            if f.name in data:
                field_value = data[f.name]
                field_type = type_hints[f.name]
                
                origin = getattr(field_type, "__origin__", None)
                if origin is Union:
                    args = field_type.__args__
                    success = False
                    for possible_type in args:
                        try:
                            if possible_type is type(None):
                                continue
                            kwargs[f.name] = _from_dict_recursive(possible_type, field_value)
                            success = True
                            break
                        except Exception:
                            continue
                    if not success:
                        kwargs[f.name] = field_value
                elif origin is list:
                    item_type = field_type.__args__[0]
                    kwargs[f.name] = [_from_dict_recursive(item_type, item) for item in field_value]
                elif origin is dict:
                    val_type = field_type.__args__[1]
                    kwargs[f.name] = {k: _from_dict_recursive(val_type, v) for k, v in field_value.items()}
                else:
                    kwargs[f.name] = _from_dict_recursive(field_type, field_value)
        return cls(**kwargs)
    return data

@dataclass
class FontProperties:
    family: str
    style: str
    variant: str
    weight: str
    stretch: str
    size: float
    #TODO: Inject not only the font family, but the actual font, maybe via a double enum?

@dataclass
class TextProperties:
    text: str
    color: str
    font: FontProperties
    # rotation: float = field(init=False)
    # va: str = field(init=False)
    # ha: str = field(init=False)
    # parse_math: bool = field(init=False)
    # alpha: float = field(init=False)

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

@dataclass
class PatchProperties:
    facecolor: str
    edgecolor: str
    linewidth: float
    force_edgecolor: bool

@dataclass
class TickProperties:
    major_size: float
    minor_size: float
    major_width: float
    minor_width: float
    major_pad: float
    minor_pad: float
    direction: TickDirection
    color: str
    labelcolor: str
    labelsize: float
    minor_visible: bool
    minor_ndivs: int

@dataclass
class SpineProperties:
    visible: bool
    color: str
    linewidth: float
    position: SpinePosition

@dataclass
class GridProperties:
    visible: bool
    color: str
    linestyle: str
    linewidth: float
    alpha: float

@dataclass
class ScalarMappableProperties:
    cmap: str
    norm_min: Optional[float]
    norm_max: Optional[float]
    has_colorbar: bool

@dataclass
class AxisProperties:
    ticks: TickProperties
    margin: float
    autolimit_mode: AutolimitMode
    use_offset: bool
    offset_threshold: int
    scientific_limits: tuple[int, int]
    # label: TextProperties = field(init=False)
    # limits: tuple[Optional[float], Optional[float]] = field(init=False)
    # scale: str = field(init=False)

@dataclass
class CoordinateProperties:
    coord_type: CoordinateSystem

@dataclass
class Cartesian2DProperties(CoordinateProperties):
    xaxis: AxisProperties
    yaxis: AxisProperties
    spines: dict[str, SpineProperties]
    facecolor: str
    axis_below: Union[bool, str]
    prop_cycle: list[str]
    coord_type: CoordinateSystem = CoordinateSystem.CARTESIAN_2D

@dataclass
class Cartesian3DProperties(Cartesian2DProperties):
    zaxis: AxisProperties
    pane_colors: dict[str, tuple[float, float, float, float]]
    coord_type: CoordinateSystem = CoordinateSystem.CARTESIAN_3D

@dataclass
class PolarProperties(CoordinateProperties):
    theta_axis: AxisProperties
    r_axis: AxisProperties
    spine: SpineProperties
    coord_type: CoordinateSystem = CoordinateSystem.POLAR

@dataclass
class BaseArtistProperties:
    visible: bool
    zorder: int
    artist_type: ArtistType

@dataclass
class LineArtistProperties(BaseArtistProperties):
    visuals: LineProperties
    artist_type: ArtistType = ArtistType.LINE

@dataclass
class ScatterArtistProperties(BaseArtistProperties):
    visuals: LineProperties
    artist_type: ArtistType = ArtistType.SCATTER

@dataclass
class BarArtistProperties(BaseArtistProperties):
    visuals: PatchProperties
    width: float
    align: str
    artist_type: ArtistType = ArtistType.BAR

@dataclass
class ImageArtistProperties(BaseArtistProperties):
    visuals: ScalarMappableProperties
    artist_type: ArtistType = ArtistType.IMAGE

@dataclass
class MeshArtistProperties(BaseArtistProperties):
    visuals: ScalarMappableProperties
    artist_type: ArtistType = ArtistType.MESH

@dataclass
class ContourArtistProperties(BaseArtistProperties):
    visuals: ScalarMappableProperties
    linewidth: float
    levels: Union[int, list[float]]
    filled: bool
    artist_type: ArtistType = ArtistType.CONTOUR

@dataclass
class HistogramArtistProperties(BaseArtistProperties):
    visuals: PatchProperties
    bins: Union[int, str]
    density: bool
    cumulative: bool
    artist_type: ArtistType = ArtistType.HISTOGRAM

@dataclass
class StairArtistProperties(BaseArtistProperties):
    visuals: LineProperties
    baseline: float
    fill: bool
    artist_type: ArtistType = ArtistType.STAIR

@dataclass
class PlotProperties:
    """The root property tree for a single PlotNode."""
    titles: dict[str, TextProperties] # 'left', 'center', 'right'
    coords: CoordinateProperties
    legend: dict[str, Any]
    artists: list[Any] = field(default_factory=list) #TODO: There needs to be some sort of gate_keeping to ensure that we don't accidentally mix incompatible artist types
    _version: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlotProperties":
        # 1. Resolve the specific Coordinate class
        coords_data = data.get("coords", {})
        c_type = coords_data.get("coord_type")

        COORD_MAP = {
            CoordinateSystem.CARTESIAN_2D: Cartesian2DProperties,
            CoordinateSystem.CARTESIAN_3D: Cartesian3DProperties,
            CoordinateSystem.POLAR: PolarProperties,
        }
        # Reconstruct the coordinate branch first
        coord_cls = COORD_MAP.get(c_type)
        if coord_cls is None:
            raise ValueError(f"Unknown coordinate type: {c_type}")
        data["coords"] = _from_dict_recursive(coord_cls, coords_data)

        # 2. Resolve the specific Artist classes
        if "artists" in data:
            ARTIST_MAP = {
                ArtistType.LINE: LineArtistProperties,
                ArtistType.SCATTER: ScatterArtistProperties,
                ArtistType.BAR: BarArtistProperties,
                ArtistType.IMAGE: ImageArtistProperties,
                ArtistType.MESH: MeshArtistProperties,
                ArtistType.CONTOUR: ContourArtistProperties,
                ArtistType.HISTOGRAM: HistogramArtistProperties,
                ArtistType.STAIR: StairArtistProperties,
            }
            new_artists = []
            for a_data in data["artists"]:
                a_type = a_data.get("artist_type")
                a_cls = ARTIST_MAP.get(a_type)
                if a_cls is None:
                    raise ValueError(f"Unknown artist type: {a_type}")
                new_artists.append(_from_dict_recursive(a_cls, a_data))
            data["artists"] = new_artists

        # 3. Final recursive reconstruction of the root
        return _from_dict_recursive(cls, data)
