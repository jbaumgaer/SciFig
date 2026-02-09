import logging
from pathlib import Path

import matplotlib.figure
from PySide6.QtCore import QObject, Signal

from src.services.config_service import ConfigService
from src.models.layout.layout_config import FreeConfig, LayoutConfig
from src.models.nodes.group_node import GroupNode
from src.models.nodes.scene_node import SceneNode, node_factory


class ApplicationModel(QObject):
    """
    The central model for the entire application. It is the single source of truth,
    holding the state of the scene graph.
    """

    modelChanged = Signal()
    selectionChanged = Signal()
    layoutConfigChanged = Signal() # Replaced autoLayoutChanged

    def __init__(self, figure: matplotlib.figure.Figure, config_service: ConfigService):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.figure = figure
        self._config_service = config_service
        self.scene_root = GroupNode(name="root")
        self.selection: list[SceneNode] = []

        # Layout configuration property
        # Initialize from config or default to FreeConfig
        self._current_layout_config: LayoutConfig = FreeConfig() # Default to FreeConfig

    @property
    def current_layout_config(self) -> LayoutConfig:
        return self._current_layout_config

    @current_layout_config.setter
    def current_layout_config(self, config: LayoutConfig):
        if self._current_layout_config != config:
            self._current_layout_config = config
            self.logger.info(f"Layout config changed to mode: {config.mode.value}")
            self.layoutConfigChanged.emit()
            self.modelChanged.emit() # Also trigger a general model change for redraw

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
            "layout_config": self.current_layout_config.to_dict() # Serialize layout config
        }

    def load_from_dict(self, data: dict, temp_dir: Path):
        """Loads the application model from a dictionary."""
        # Version check can be added here in the future
        #TODO: This method emits two modelChanged signals, one from clear_scene and one at the end. Consider optimizing to emit only once.
        self.clear_scene()
        self.scene_root = node_factory(data["scene_root"], temp_dir=temp_dir)

        # Deserialize layout config
        layout_config_data = data.get("layout_config")
        if layout_config_data:
            self.current_layout_config = LayoutConfig.from_dict(layout_config_data) # Use LayoutConfig.from_dict
        else:
            self.current_layout_config = FreeConfig() # Default if not found

        self.modelChanged.emit()
