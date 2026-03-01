from typing import Optional, Protocol

from src.models.layout.layout_config import Gutters, Margins
from src.models.nodes.plot_node import (
    PlotNode,  # Import specific type if it's the one used
)
from src.shared.types import PlotID, Rect

# TODO: This should go into the interfaces folder because the freeformlyoutcapabilities will later become important for any group of free form objects


class LayoutEngineProtocol(Protocol):
    def calculate_geometries(
        self, plots: list[PlotNode], layout_config: any
    ) -> tuple[dict[PlotID, Rect], Optional[Margins], Optional[Gutters]]: ...


class FreeFormLayoutCapabilities(Protocol):
    def perform_align(
        self, nodes: list[PlotNode], alignment_type: str
    ) -> list[PlotNode]: ...
    def perform_distribute(
        self, nodes: list[PlotNode], distribution_type: str
    ) -> list[PlotNode]: ...
