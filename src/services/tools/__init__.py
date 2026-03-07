# This file makes the 'tools' directory a Python package.
from typing import Optional
from unittest.mock import Mock

from .base_tool import BaseTool


class MockTool(BaseTool):
    """A mock tool for testing and placeholder purposes."""

    def __init__(self, name: str, icon_path: str, model, canvas_widget, event_aggregator):
        super().__init__(model, canvas_widget, event_aggregator)
        self._name = name
        self._icon_path = icon_path

    @property
    def name(self) -> str:
        return self._name

    @property
    def icon_path(self) -> str:
        return self._icon_path

    def on_activated(self) -> None:
        pass

    def on_deactivated(self) -> None:
        pass

    def mouse_press_event(
        self, node_id: Optional[str], fig_coords: tuple[float, float], button: int
    ) -> None:
        pass

    def mouse_move_event(self, fig_coords: tuple[float, float]) -> None:
        pass

    def mouse_release_event(self, fig_coords: tuple[float, float]) -> None:
        pass

    def key_press_event(self, event) -> None:
        pass

    def paint_event(self, painter) -> None:
        pass
