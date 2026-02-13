import logging
from pathlib import Path
from typing import Optional

import matplotlib.figure
from PySide6.QtCore import QObject, Signal

from src.interfaces.project_io import ProjectLifecycle
from src.models.layout.layout_config import FreeConfig, LayoutConfig
from src.models.nodes.group_node import GroupNode
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode, node_factory


class ApplicationModel(QObject, ProjectLifecycle):
    """
    The central model for the entire application. It is the single source of truth,
    holding the state of the scene graph and implementing the ProjectLifecycle protocol.
    """

    projectReset = Signal() #TODO: Maybe call this modelReset to be more general
    modelChanged = Signal()
    selectionChanged = Signal()
    layoutConfigChanged = Signal()

    def __init__(self, figure: matplotlib.figure.Figure):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.figure = figure
        self.scene_root = GroupNode(name="root")
        self.selection: list[SceneNode] = []
        self._file_path: Optional[Path] = None
        self._is_modified: bool = False
        self._current_layout_config: LayoutConfig = FreeConfig()

    def _set_modified(self, modified: bool = True):
        """Private helper to set the modified status and emit a signal."""
        if self._is_modified != modified:
            self._is_modified = modified
            # A general model change signal is sufficient, as any UI
            # concerned with the modified status (like a window title)
            # will be listening to it.
            self.modelChanged.emit()

    def reset_state(self):
        """Resets the model to a clean, default state.
        TODO: This is maybe redundant with set_scene_root, which also clears the selection. Decide on one approach and remove the other.
        Also. I manually change the selection without using set_selection, which is a bit hacky. Maybe I should make set_selection private and only
        use it within the model to ensure the signal is always emitted when the selection changes."""
        self.scene_root = GroupNode(name="root")
        self.selection = []
        self.file_path = None
        self.current_layout_config = FreeConfig()
        # Set modified to False *after* all state-clearing actions
        self._is_modified = False 
        self.projectReset.emit()
        self.modelChanged.emit()
        self.selectionChanged.emit()

    def set_selection(self, nodes: list[SceneNode]):
        """Sets the selection and emits the selectionChanged signal."""
        self.selection = nodes
        self.selectionChanged.emit()

    def set_scene_root(self, new_root: SceneNode):
        """Sets a new root for the scene graph."""
        self.scene_root = new_root
        self.set_selection([])
        self.logger.debug(f"Scene root set to: {new_root.name} (ID: {new_root.id}). Selection cleared.")
        # self.projectReset.emit() TODO: Decide if this should be emitted here or if it's only relevant for the reset_state method. Maybe we can have a more general signal like sceneGraphChanged that is emitted whenever the structure of the scene graph changes significantly, and then projectReset can be a specific case of that. For now, I'll just emit modelChanged, which is already being listened to by all UI components that care about changes in the model.
        self._set_modified()
        # self.modelChanged.emit()

    @property
    def is_modified(self) -> bool:
        return self._is_modified

    @property
    def file_path(self) -> Optional[Path]:
        return self._file_path

    @file_path.setter
    def file_path(self, path: Optional[Path]) -> None:
        if self._file_path != path:
            self._file_path = path
            self._set_modified() # Changing the path is a modification

    @property
    def current_layout_config(self) -> LayoutConfig:
        return self._current_layout_config

    @current_layout_config.setter
    def current_layout_config(self, config: LayoutConfig):
        if self._current_layout_config != config:
            self._current_layout_config = config
            self.logger.info(f"Layout config changed to mode: {config.mode.value}")
            self.layoutConfigChanged.emit()
            self._set_modified()

    def add_node(self, node: SceneNode, parent: SceneNode | None = None):
        """Adds a node to the scene graph."""
        if parent is None:
            parent = self.scene_root
        parent.add_child(node)
        self._set_modified()

    def extract_plot_states(self) -> list[dict]:
        """Extracts data and properties from all existing plot nodes."""
        existing_plot_states = []
        for node in self.scene_root.all_descendants():
            if isinstance(node, PlotNode) and node.data is not None:
                state = {
                    "data": node.data,
                    "plot_properties_dict": node.plot_properties.to_dict(
                        exclude_geometry=True
                    ),
                    "id": node.id,}
                existing_plot_states.append(state)
        self.logger.debug(f"Extracted {len(existing_plot_states)} existing plot states.")
        return existing_plot_states

    def get_node_at(self, position: tuple[float, float]) -> SceneNode | None:
        """Finds the topmost node at the given figure coordinates."""
        return self.scene_root.hit_test(position)

    def as_dict(self) -> dict[str, any]:
        """Serializes the application model to a dictionary."""
        return {
            "version": "1.0",
            "scene_root": self.scene_root.to_dict(),
            "layout_config": self.current_layout_config.to_dict(),
        }

    def load_from_state(self, data: dict[str, any], temp_dir: Path):
        """Loads the application model from a dictionary."""
        self.reset_state()
        self.scene_root = node_factory(data["scene_root"], temp_dir=temp_dir)

        layout_config_data = data.get("layout_config")
        if layout_config_data:
            self.current_layout_config = LayoutConfig.from_dict(layout_config_data)
        else:
            self.current_layout_config = FreeConfig()

        # After loading, the project is considered unmodified until a change is made
        self._is_modified = False
        self.modelChanged.emit()
