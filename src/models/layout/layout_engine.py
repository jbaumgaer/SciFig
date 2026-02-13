import logging
from abc import ABC, abstractmethod
from typing import Optional, Protocol # Added Protocol
from src.models.layout.layout_config import Gutters, LayoutConfig, Margins
from src.models.nodes import PlotNode
from src.shared.types import PlotID, Rect
from src.models.layout.layout_protocols import LayoutEngineProtocol # Added this import


class LayoutEngine(ABC, LayoutEngineProtocol): # Inherit from the protocol
    """
    Abstract base class for all layout engines.
    Defines the interface for calculating plot geometries based on a layout configuration.
    TODO: This is redundant with LayoutEngineProtocol. Decide on one approach, and then put it into the interfaces folder
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def calculate_geometries(
        self, plots: list[PlotNode], layout_config: LayoutConfig
    ) -> tuple[dict[PlotID, Rect], Optional[Margins], Optional[Gutters]]:
        """
        Calculates and returns the target (left, bottom, width, height) geometry for each PlotNode.
        This method is stateless; all necessary parameters are passed via layout_config.
        Returns Optional[Margins] and Optional[Gutters] because these might not be relevant for all engines (e.g., FreeLayoutEngine).

        Args:
            plots: A list of PlotNode objects to arrange.
            layout_config: The configuration object specific to this layout engine.

        Returns:
            A tuple containing:
                - A dictionary mapping each PlotNode to its calculated geometry.
                - An Optional[Margins] object, representing effective margins after layout (None if not applicable).
                - An Optional[Gutters] object, representing effective gutters after layout (None if not applicable).
        """
        pass
