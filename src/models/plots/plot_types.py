from enum import Enum

class SpinePosition(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"

    @classmethod
    def from_str(cls, s: str) -> "SpinePosition":
        s = s.lower()
        if s in ("top", "bottom", "left", "right"):
            return cls(s)
        raise ValueError(f"Invalid SpinePosition string: {s}")


class AxisKey(str, Enum):
    X = "x"
    Y = "y"
    Z = "z"

    @classmethod
    def from_str(cls, s: str) -> "AxisKey":
        s = s.lower()
        if s in ("x", "y", "z"):
            return cls(s)
        raise ValueError(f"Invalid AxisKey string: {s}")
    

class AutolimitMode(str, Enum):
    DATA = "data"
    ROUND_NUMBERS = "round_numbers"
    
    @classmethod
    def from_str(cls, s: str) -> "AutolimitMode":
        s = s.lower()
        if s in ("data", "round_numbers"):
            return cls(s)
        raise ValueError(f"Invalid AutolimitMode string: {s}")
    

class RelativeFontSize(str, Enum):
    XX_SMALL = "xx-small"
    X_SMALL = "x-small"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    X_LARGE = "x-large"
    XX_LARGE = "xx-large"

    @classmethod
    def from_str(cls, s: str) -> "RelativeFontSize":
        s = s.lower()
        if s in ("xx-small", "x-small", "small", "medium", "large", "x-large", "xx-large"):
            return cls(s)
        raise ValueError(f"Invalid RelativeFontSize string: {s}")
    

class FontStretch(str, Enum):
    """This enum is not currently implemented"""
    ULTRA_CONDENSED = "ultra-condensed"
    EXTRA_CONDENSED = "extra-condensed"
    CONDENSED = "condensed"
    SEMI_CONDENSED = "semi-condensed"
    NORMAL = "normal"
    SEMI_EXPANDED = "semi-expanded"
    EXPANDED = "expanded"
    EXTRA_EXPANDED = "extra-expanded"
    ULTRA_EXPANDED = "ultra-expanded"
    WIDER = "wider"
    NARROWER = "narrower"

    @classmethod
    def from_str(cls, s: str) -> "FontStretch":
        s = s.lower()
        if s in (
            "ultra-condensed", "extra-condensed", "condensed", "semi-condensed",
            "normal", "semi-expanded", "expanded", "extra-expanded",
            "ultra-expanded", "wider", "narrower"
        ):
            return cls(s)
        raise ValueError(f"Invalid FontStretch string: {s}")


class FontWeight(str, Enum):
    NORMAL = "normal"
    BOLD = "bold"
    BOLDER = "bolder"
    LIGHTER = "lighter"
    _100 = "100"
    _200 = "200"
    _300 = "300"
    _400 = "400" # Normal
    _500 = "500"
    _600 = "600"
    _700 = "700" # Bold
    _800 = "800"
    _900 = "900"

    @classmethod
    def from_str(cls, s: str) -> "FontWeight":
        s = s.lower()
        if s in ("normal", "bold", "bolder", "lighter", "100", "200", "300", "400", "500", "600", "700", "800", "900"):
            return cls(s)
        raise ValueError(f"Invalid FontWeight string: {s}")
    

class FontFamily(str, Enum):
    SERIF = "serif"
    SANS_SERIF = "sans-serif"
    CURSIVE = "cursive"
    FANTASY = "fantasy"
    MONOSPACE = "monospace"

    @classmethod
    def from_str(cls, s: str) -> "FontFamily":
        s = s.lower()
        if s in ("serif", "sans-serif", "cursive", "fantasy", "monospace"):
            return cls(s)
        raise ValueError(f"Invalid FontFamily string: {s}")
    

class SerifFont(str, Enum):
    TIMES_NEW_ROMAN = "Times New Roman"
    TIMES = "Times"
    DEJAVU_SERIF = "DejaVu Serif"
    BITSTREAM_VERA_SERIF = "Bitstream Vera Serif"
    COMPUTER_MODERN_ROMAN = "Computer Modern Roman"
    NEW_CENTURY_SCHOOLBOOK = "New Century Schoolbook"
    CENTURY_SCHOOLBOOK_L = "Century Schoolbook L"
    UTOPIA = "Utopia"
    ITC_BOOKMAN = "ITC Bookman"
    BOOKMAN = "Bookman"
    NIMBUS_ROMAN_NO9_L = "Nimbus Roman No9 L"
    PALATINO = "Palatino"
    CHARTER = "Charter"

    @classmethod
    def from_str(cls, s: str) -> "SerifFont":
        s = s.lower()
        mapping = {
            "times new roman": cls.TIMES_NEW_ROMAN,
            "times": cls.TIMES,
            "dejavu serif": cls.DEJAVU_SERIF,
            "bitstream vera serif": cls.BITSTREAM_VERA_SERIF,
            "computer modern roman": cls.COMPUTER_MODERN_ROMAN,
            "new century schoolbook": cls.NEW_CENTURY_SCHOOLBOOK,
            "century schoolbook l": cls.CENTURY_SCHOOLBOOK_L,
            "utopia": cls.UTOPIA,
            "itc bookman": cls.ITC_BOOKMAN,
            "bookman": cls.BOOKMAN,
            "nimbus roman no9 l": cls.NIMBUS_ROMAN_NO9_L,
            "palatino": cls.PALATINO,
            "charter": cls.CHARTER
        }
        if s in mapping:
            return mapping[s]
        raise ValueError(f"Invalid SerifFont string: {s}")
    

class SansSerifFont(str, Enum):
    ARIAL = "Arial"
    HELVETICA = "Helvetica"
    DEJAVU_SANS = "DejaVu Sans"
    BITSTREAM_VERA_SANS = "Bitstream Vera Sans"
    COMPUTER_MODERN_SANS_SERIF = "Computer Modern Sans Serif"
    LUCIDA_GRANDE = "Lucida Grande"
    VERDANA = "Verdana"
    GENEVA = "Geneva"
    LUCID = "Lucid"
    AVANT_GARDE = "Avant Garde"

    @classmethod
    def from_str(cls, s: str) -> "SansSerifFont":
        s = s.lower()
        mapping = {
            "arial": cls.ARIAL,
            "helvetica": cls.HELVETICA,
            "dejavu sans": cls.DEJAVU_SANS,
            "bitstream vera sans": cls.BITSTREAM_VERA_SANS,
            "computer modern sans serif": cls.COMPUTER_MODERN_SANS_SERIF,
            "lucida grande": cls.LUCIDA_GRANDE,
            "verdana": cls.VERDANA,
            "geneva": cls.GENEVA,
            "lucid": cls.LUCID,
            "avant garde": cls.AVANT_GARDE
        }
        if s in mapping:
            return mapping[s]
        raise ValueError(f"Invalid SansSerifFont string: {s}")
    

class CursiveFont(str, Enum):
    APPLE_CHANCERY = "Apple Chancery"
    TEXTILE = "Textile"
    ZAPF_CHANCERY = "Zapf Chancery"
    SAND = "Sand"
    SCRIPT_MT = "Script MT"
    FELIPA = "Felipa"
    COMIC_NEUE = "Comic Neue"
    COMIC_SANS_MS = "Comic Sans MS"

    @classmethod
    def from_str(cls, s: str) -> "CursiveFont":
        s = s.lower()
        mapping = {
            "apple chancery": cls.APPLE_CHANCERY,
            "textile": cls.TEXTILE,
            "zapf chancery": cls.ZAPF_CHANCERY,
            "sand": cls.SAND,
            "script mt": cls.SCRIPT_MT,
            "felipa": cls.FELIPA,
            "comic neue": cls.COMIC_NEUE,
            "comic sans ms": cls.COMIC_SANS_MS
        }
        if s in mapping:
            return mapping[s]
        raise ValueError(f"Invalid CursiveFont string: {s}")
    

class FantasyFont(str, Enum):
    XKCD_SCRIPT = "xkcd script"
    CHICAGO = "Chicago"
    CHARCOAL = "Charcoal"
    IMPACT = "Impact"
    WESTERN = "Western"

    @classmethod
    def from_str(cls, s: str) -> "FantasyFont":
        s = s.lower()
        mapping = {
            "xkcd script": cls.XKCD_SCRIPT,
            "chicago": cls.CHICAGO,
            "charcoal": cls.CHARCOAL,
            "impact": cls.IMPACT,
            "western": cls.WESTERN
        }
        if s in mapping:
            return mapping[s]
        raise ValueError(f"Invalid FantasyFont string: {s}")
    

class MonospaceFont(str, Enum):
    DEJAVU_SANS_MONO = "DejaVu Sans Mono"
    BITSTREAM_VERA_SANS_MONO = "Bitstream Vera Sans Mono"
    COMPUTER_MODERN_TYPEWRITER = "Computer Modern Typewriter"
    ANDALE_MONO = "Andale Mono"
    NIMBUS_MONO_L = "Nimbus Mono L"
    COURIER_NEW = "Courier New"
    COURIER = "Courier"
    FIXED = "Fixed"
    TERMINAL = "Terminal"

    @classmethod
    def from_str(cls, s: str) -> "MonospaceFont":
        s = s.lower()
        mapping = {
            "dejavu sans mono": cls.DEJAVU_SANS_MONO,
            "bitstream vera sans mono": cls.BITSTREAM_VERA_SANS_MONO,
            "computer modern typewriter": cls.COMPUTER_MODERN_TYPEWRITER,
            "andale mono": cls.ANDALE_MONO,
            "nimbus mono l": cls.NIMBUS_MONO_L,
            "courier new": cls.COURIER_NEW,
            "courier": cls.COURIER,
            "fixed": cls.FIXED,
            "terminal": cls.TERMINAL
        }
        if s in mapping:
            return mapping[s]
        raise ValueError(f"Invalid MonospaceFont string: {s}")


class JoinStyle(str, Enum):
    MITER = "miter"
    ROUND = "round"
    BEVEL = "bevel"

    @classmethod
    def from_str(cls, s: str) -> "JoinStyle":
        s = s.lower()
        if s in ("miter", "round", "bevel"):
            return cls(s)
        raise ValueError(f"Invalid JoinStyle string: {s}")


class CapStyle(str, Enum):
    BUTT = "butt"
    ROUND = "round"
    PROJECTING = "projecting"

    @classmethod
    def from_str(cls, s: str) -> "CapStyle":
        s = s.lower()
        if s in ("butt", "round", "projecting"):
            return cls(s)
        raise ValueError(f"Invalid CapStyle string: {s}")


class MarkerFillStyle(str, Enum):
    FULL = "full"
    LEFT = "left"
    RIGHT = "right"
    BOTTOM = "bottom"
    TOP = "top"
    NONE = "none"

    @classmethod
    def from_str(cls, s: str) -> "MarkerFillStyle":
        s = s.lower()
        if s in ("full", "left", "right", "bottom", "top", "none"):
            return cls(s)
        raise ValueError(f"Invalid MarkerFillStyle string: {s}")


class TickDirection(str, Enum):
    IN = "in"
    OUT = "out"
    INOUT = "inout"

    @classmethod
    def from_str(cls, s: str) -> "TickDirection":
        s = s.lower()
        if s in ("in", "out", "inout"):
            return cls(s)
        raise ValueError(f"Invalid TickDirection string: {s}")


class CoordinateSystem(str, Enum):
    CARTESIAN_2D = "cartesian_2d"
    CARTESIAN_3D = "cartesian_3d"
    POLAR = "polar"

    @classmethod
    def from_str(cls, s: str) -> "CoordinateSystem":
        s = s.lower()
        if s in ("cartesian_2d", "cartesian_3d", "polar"):
            return cls(s)
        raise ValueError(f"Invalid CoordinateSystem string: {s}")


class ArtistType(str, Enum):
    """
    An enumeration for the different types of plots available.
    Inherits from str to be easily serializable.
    """

    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    IMAGE = "image"
    MESH = "mesh"
    CONTOUR = "contour"
    HISTOGRAM = "histogram"
    STAIR = "stair"
    SURFACE = "surface"
    POLAR_LINE = "polar_line"
    BOXPLOT = "boxplot"
