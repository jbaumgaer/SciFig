from dataclasses import asdict, dataclass, field, fields, is_dataclass, replace
from typing import Any, Optional, Type, TypeVar, Union, get_type_hints, get_origin, get_args

from src.models.plots.plot_types import (
    ArtistType,
    AutolimitMode,
    CoordinateSystem,
    SpinePosition,
    TickDirection,
)
from src.shared.color import Color
from src.shared.units import Dimension, Unit
from src.shared.primitives import Alpha, ZOrder

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

                # Special Case: Coerce Color and Dimension from primitives during deserialization
                if field_type is Color:
                    kwargs[f.name] = Color.from_mpl(field_value)
                    continue
                if field_type is Dimension:
                    # Default to CM if unit missing in dict (usually raw float)
                    if isinstance(field_value, (int, float)):
                        kwargs[f.name] = Dimension(float(field_value), Unit.CM)
                    else:
                        kwargs[f.name] = Dimension(field_value["value"], Unit(field_value["unit"]))
                    continue
                if field_type is Alpha:
                    kwargs[f.name] = Alpha(float(field_value))
                    continue
                if field_type is ZOrder:
                    kwargs[f.name] = ZOrder(int(field_value))
                    continue

                origin = get_origin(field_type)
                if origin is Union:
                    args = get_args(field_type)
                    success = False
                    for possible_type in args:
                        # Skip None type in Union
                        if possible_type is type(None):
                            continue
                        
                        # Only attempt dataclass reconstruction if we have a dict
                        if is_dataclass(possible_type) and not isinstance(field_value, dict):
                            continue

                        try:
                            kwargs[f.name] = _from_dict_recursive(
                                possible_type, field_value
                            )
                            success = True
                            break
                        except Exception:
                            continue
                    if not success:
                        kwargs[f.name] = field_value
                elif origin is list:
                    item_type = get_args(field_type)[0]
                    kwargs[f.name] = [
                        _from_dict_recursive(item_type, item) for item in field_value
                    ]
                elif origin is dict:
                    val_type = get_args(field_type)[1]
                    kwargs[f.name] = {
                        k: _from_dict_recursive(val_type, v)
                        for k, v in field_value.items()
                    }
                elif origin is tuple:
                    # Coerce list to tuple and recursively hydrate elements
                    args = get_args(field_type)
                    if isinstance(field_value, (list, tuple)):
                        # Handle fixed-size tuples or homogeneous variable-size tuples
                        kwargs[f.name] = tuple([
                            _from_dict_recursive(args[i] if i < len(args) else args[0], item)
                            for i, item in enumerate(field_value)
                        ])
                    else:
                        kwargs[f.name] = field_value
                else:
                    kwargs[f.name] = _from_dict_recursive(field_type, field_value)
        return cls(**kwargs)
    return data


@dataclass(frozen=True)
class FontProperties:
    family: str
    style: str
    variant: str
    weight: str
    stretch: str
    size: Dimension  # Supports conversion from points
    # TODO: Inject not only the font family, but the actual font, maybe via a double enum?


@dataclass(frozen=True)
class TextProperties:
    text: str
    color: Color
    font: FontProperties
    # rotation: float = field(init=False)
    # va: str = field(init=False)
    # ha: str = field(init=False)
    # parse_math: bool = field(init=False)
    # alpha: float = field(init=False)


@dataclass(frozen=True)
class LineProperties:
    linewidth: Dimension
    linestyle: Union[str, tuple]
    color: Color
    marker: str
    markerfacecolor: Color
    markeredgecolor: Color
    markeredgewidth: Dimension
    markersize: Dimension


@dataclass(frozen=True)
class PatchProperties:
    facecolor: Color
    edgecolor: Color
    linewidth: Dimension
    force_edgecolor: bool


@dataclass(frozen=True)
class TickProperties:
    major_size: Dimension
    minor_size: Dimension
    major_width: Dimension
    minor_width: Dimension
    major_pad: Dimension
    minor_pad: Dimension
    direction: TickDirection
    color: Color
    labelcolor: Color
    labelsize: Dimension
    minor_visible: bool
    minor_ndivs: Union[str, int]


@dataclass(frozen=True)
class SpineProperties:
    visible: bool
    color: Color
    linewidth: Dimension
    position: SpinePosition


@dataclass(frozen=True)
class GridProperties:
    visible: bool
    color: Color
    linestyle: Union[str, tuple]
    linewidth: Dimension
    alpha: Alpha


@dataclass(frozen=True)
class ScalarMappableProperties:
    cmap: str
    norm_min: Optional[float]
    norm_max: Optional[float]
    has_colorbar: bool


@dataclass(frozen=True)
class AxisProperties:
    ticks: TickProperties
    margin: float # Unitless ratio
    autolimit_mode: AutolimitMode
    use_offset: bool
    offset_threshold: int
    scientific_limits: tuple[int, int]
    label: TextProperties
    limits: tuple[Optional[float], Optional[float]]
    # scale: str = field(init=False)


@dataclass(frozen=True)
class CoordinateProperties:
    # coord_type: CoordinateSystem
    pass


@dataclass(frozen=True)
class Cartesian2DProperties(CoordinateProperties):
    xaxis: AxisProperties
    yaxis: AxisProperties
    spines: dict[str, SpineProperties]
    facecolor: Color
    axis_below: Union[bool, str]
    prop_cycle: list[Color]
    coord_type: CoordinateSystem = CoordinateSystem.CARTESIAN_2D


@dataclass(frozen=True)
class Cartesian3DProperties(CoordinateProperties):
    xaxis: AxisProperties
    yaxis: AxisProperties
    zaxis: AxisProperties
    spines: dict[str, SpineProperties]
    facecolor: Color
    axis_below: Union[bool, str]
    prop_cycle: list[Color]
    pane_colors: dict[str, Color]
    coord_type: CoordinateSystem = CoordinateSystem.CARTESIAN_3D


@dataclass(frozen=True)
class PolarProperties(CoordinateProperties):
    theta_axis: AxisProperties
    r_axis: AxisProperties
    spine: SpineProperties
    coord_type: CoordinateSystem = CoordinateSystem.POLAR


@dataclass(frozen=True)
class BaseArtistProperties:
    visible: bool
    zorder: ZOrder


@dataclass(frozen=True)
class LineArtistProperties(BaseArtistProperties):
    visuals: LineProperties
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    artist_type: ArtistType = ArtistType.LINE


@dataclass(frozen=True)
class ScatterArtistProperties(BaseArtistProperties):
    visuals: LineProperties
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    artist_type: ArtistType = ArtistType.SCATTER


@dataclass(frozen=True)
class BarArtistProperties(BaseArtistProperties):
    visuals: PatchProperties
    width: float
    align: str
    artist_type: ArtistType = ArtistType.BAR


@dataclass(frozen=True)
class ImageArtistProperties(BaseArtistProperties):
    visuals: ScalarMappableProperties
    artist_type: ArtistType = ArtistType.IMAGE


@dataclass(frozen=True)
class MeshArtistProperties(BaseArtistProperties):
    visuals: ScalarMappableProperties
    artist_type: ArtistType = ArtistType.MESH


@dataclass(frozen=True)
class ContourArtistProperties(BaseArtistProperties):
    visuals: ScalarMappableProperties
    linewidth: Dimension
    levels: Union[int, list[float]]
    filled: bool
    artist_type: ArtistType = ArtistType.CONTOUR


@dataclass(frozen=True)
class HistogramArtistProperties(BaseArtistProperties):
    visuals: PatchProperties
    bins: Union[int, str, list]
    density: bool
    cumulative: bool
    artist_type: ArtistType = ArtistType.HISTOGRAM


@dataclass(frozen=True)
class StairArtistProperties(BaseArtistProperties):
    visuals: LineProperties
    baseline: float
    fill: bool
    artist_type: ArtistType = ArtistType.STAIR


@dataclass(frozen=True)
class PlotProperties:
    """The root property tree for a single PlotNode."""

    titles: dict[str, TextProperties]  # 'left', 'center', 'right'
    coords: CoordinateProperties
    legend: dict[str, Any]
    artists: list[Any] = field(
        default_factory=list
    )  # TODO: There needs to be some sort of gate_keeping to ensure that we don't accidentally mix incompatible artist types in one plot

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlotProperties":
        # 1. Resolve the specific Coordinate class (Fallback to Cartesian 2D)
        # TODO: In the future let's not do default fallbacks
        coords_data = data.get("coords", {})
        c_type_raw = coords_data.get("coord_type", CoordinateSystem.CARTESIAN_2D)

        # Ensure we have a valid enum (handles strings from JSON)
        try:
            c_type = (
                CoordinateSystem(c_type_raw)
                if not isinstance(c_type_raw, CoordinateSystem)
                else c_type_raw
            )
        except ValueError:
            c_type = CoordinateSystem.CARTESIAN_2D

        COORD_MAP = {
            CoordinateSystem.CARTESIAN_2D: Cartesian2DProperties,
            CoordinateSystem.CARTESIAN_3D: Cartesian3DProperties,
            CoordinateSystem.POLAR: PolarProperties,
        }

        coord_cls = COORD_MAP.get(c_type, Cartesian2DProperties)
        data["coords"] = _from_dict_recursive(coord_cls, coords_data)

        # 2. Resolve the specific Artist classes
        if "artists" in data and isinstance(data["artists"], list):
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
                a_type_raw = a_data.get("artist_type", ArtistType.LINE)
                try:
                    a_type = (
                        ArtistType(a_type_raw)
                        if not isinstance(a_type_raw, ArtistType)
                        else a_type_raw
                    )
                except ValueError:
                    a_type = ArtistType.LINE

                a_cls = ARTIST_MAP.get(a_type, LineArtistProperties)
                new_artists.append(_from_dict_recursive(a_cls, a_data))
            data["artists"] = new_artists
        else:
            # Fallback for sparse data: Ensure at least one artist slot exists
            # This allows the StyleService to populate it later if needed
            data["artists"] = []

        # 3. Final recursive reconstruction of the root
        return _from_dict_recursive(cls, data)
