import logging 
from pathlib import Path

import matplotlib.figure
from PySide6.QtCore import QObject, Signal

from .nodes import GroupNode, SceneNode
from .nodes.scene_node import node_factory
from src.config_service import ConfigService


class ApplicationModel(QObject):
    """
    The central model for the entire application. It is the single source of truth,
    holding the state of the scene graph.
    """

    modelChanged = Signal()
    selectionChanged = Signal()
    autoLayoutChanged = Signal(bool) # Added signal

    def __init__(self, figure: matplotlib.figure.Figure, config_service: ConfigService): # Modified signature
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__) # Added logger
        self.figure = figure
        self._config_service = config_service # Stored config service
        self.scene_root = GroupNode(name="root")
        self.selection: list[SceneNode] = []

        # Auto-layout properties
        self._auto_layout_enabled: bool = self._config_service.get("figure.auto_layout_enabled_default", False) # Initialized from config
        self._figure_subplot_params: dict | None = None # Stores explicit layout when auto-layout is off

    @property
    def auto_layout_enabled(self) -> bool:
        return self._auto_layout_enabled

    def set_auto_layout_enabled(self, enabled: bool):
        """
        Sets whether automatic layout adjustment is enabled for the figure.
        If disabling auto-layout, captures the current layout parameters.
        If enabling auto-layout, clears captured parameters.
        """
        if self._auto_layout_enabled == enabled:
            return # No change

        self.logger.info(f"Setting auto-layout enabled: {enabled}. Previous: {self._auto_layout_enabled}")

        if not enabled and self._auto_layout_enabled:
            # Transitioning from enabled to disabled, capture current layout
            self.figure.tight_layout() # Apply one last auto-layout
            
            # Capture subplot parameters (left, right, bottom, top, wspace, hspace)
            # Iterate through axes to get their positions
            subplot_params = self.figure.subplotpars
            self._figure_subplot_params = {
                "left": subplot_params.left,
                "right": subplot_params.right,
                "bottom": subplot_params.bottom,
                "top": subplot_params.top,
                "wspace": subplot_params.wspace,
                "hspace": subplot_params.hspace,
            }
            self.logger.debug(f"Captured subplot parameters: {self._figure_subplot_params}")
        elif enabled and not self._auto_layout_enabled:
            # Transitioning from disabled to enabled, clear captured layout
            self._figure_subplot_params = None
            self.logger.debug("Cleared captured subplot parameters.")

        self._auto_layout_enabled = enabled
        self.autoLayoutChanged.emit(enabled) # Emit signal

    @property
    def figure_subplot_params(self) -> dict | None:
        return self._figure_subplot_params

    def add_node(self, node: SceneNode, parent: SceneNode | None = None):
        """Adds a node to the scene graph."""
        if parent is None:
            parent = self.scene_root
        parent.add_child(node)
        self.modelChanged.emit()

    def clear_scene(self):
        """Removes all nodes from the scene."""
        self.scene_root.children.clear()
        self.set_selection([])
        self.modelChanged.emit()

    def set_selection(self, nodes: list[SceneNode]):
        """Sets the selection and emits the selectionChanged signal."""
        self.selection = nodes
        self.selectionChanged.emit()

    def set_scene_root(self, new_root: SceneNode):
        """Sets a new root for the scene graph."""
        self.scene_root = new_root
        self.set_selection([]) # Clear selection when root changes
        self.modelChanged.emit()

    def get_node_at(self, position: tuple[float, float]) -> SceneNode | None:
        """Finds the topmost node at the given figure coordinates."""
        return self.scene_root.hit_test(position)

    def to_dict(self) -> dict:
        """Serializes the application model to a dictionary."""
        return {
            "version": "1.0",
            "scene_root": self.scene_root.to_dict(),
        }

    def load_from_dict(self, data: dict, temp_dir: Path):
        """Loads the application model from a dictionary."""
        # Version check can be added here in the future
        self.clear_scene()
        self.scene_root = node_factory(data["scene_root"], temp_dir=temp_dir)
        self.modelChanged.emit()
