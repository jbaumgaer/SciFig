from typing import Protocol, Any, Optional
from src.shared.types import PlotID, Rect
from src.models.layout.layout_config import Margins, Gutters
from src.models.nodes.plot_node import PlotNode # Import specific type if it's the one used

class LayoutEngineProtocol(Protocol):
    def calculate_geometries(
        self,
        plots: list[PlotNode],
        layout_config: Any
    ) -> tuple[dict[PlotID, Rect], Optional[Margins], Optional[Gutters]]:
        ...

class FreeFormLayoutCapabilities(Protocol):
    def perform_align(self, nodes: list[PlotNode], alignment_type: str) -> list[PlotNode]:
        ...
    def perform_distribute(self, nodes: list[PlotNode], distribution_type: str) -> list[PlotNode]:
        ...
