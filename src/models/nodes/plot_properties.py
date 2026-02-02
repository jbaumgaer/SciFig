from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PlotMapping:
    x: Optional[str]
    y: List[str]


@dataclass
class AxesLimits:
    xlim: tuple[Optional[float], Optional[float]]
    ylim: tuple[Optional[float], Optional[float]]


@dataclass
class PlotProperties:
    title: str
    xlabel: str
    ylabel: str
    plot_mapping: PlotMapping
    axes_limits: AxesLimits
