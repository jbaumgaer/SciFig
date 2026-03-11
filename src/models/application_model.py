import logging
from pathlib import Path
from typing import Any, Optional

from src.interfaces.project_io import ProjectLifecycle
from src.models.layout.layout_config import GridConfig
from src.models.nodes.grid_node import GridNode
from src.models.nodes.group_node import GroupNode
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode, node_factory
from src.services.event_aggregator import EventAggregator
from src.shared.constants import LayoutMode
from src.shared.events import Events


class ApplicationModel(ProjectLifecycle):
    """
    The central model for the entire application. It is the single source of truth,
    holding the state of the scene graph and implementing the ProjectLifecycle protocol.
    """

    def __init__(
        self,
        event_aggregator: EventAggregator,
        figure_size: tuple[float, float],
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._event_aggregator = event_aggregator
        self.scene_root = GroupNode(name="root")
        self.selection: list[SceneNode] = []
        self.selected_path: str = ""  # The path to a sub-component within the selection
        self._file_path: Optional[Path] = None
        self._is_dirty: bool = False
        self.layout_mode: LayoutMode = LayoutMode.FREE_FORM
        self._figure_size = figure_size

    @property
    def figure_size(self) -> tuple[float, float]:
        """Returns the total figure dimensions in centimeters (width, height)."""
        return self._figure_size

    @figure_size.setter
    def figure_size(self, size: tuple[float, float]):
        """Sets the figure size and publishes FIGURE_SIZE_CHANGED."""
        if self._figure_size != size:
            self._figure_size = size
            self._event_aggregator.publish(Events.FIGURE_SIZE_CHANGED, figure_size=size)
            self.logger.info(f"Figure size changed to: {size} cm")

    def set_dirty(self, is_dirty: bool):
        """Public method to set the dirty status of the model."""
        if self._is_dirty != is_dirty:
            self._is_dirty = is_dirty

    def reset_state(self):
        """Resets the model to a clean, default state and publishes events."""
        self.scene_root = GroupNode(name="root")
        self.set_selection([])
        self.file_path = None
        self.layout_mode = LayoutMode.FREE_FORM
        self.set_dirty(False)  # Explicitly set to not dirty after a full reset
        self._event_aggregator.publish(Events.PROJECT_WAS_RESET)

    def set_selection(self, nodes: list[SceneNode]):
        """Sets the selection and publishes SELECTION_CHANGED event."""
        if self.selection != nodes:
            self.selection = nodes
            self.selected_path = (
                ""  # Reset sub-selection when the main selection changes
            )
            self._event_aggregator.publish(
                Events.SELECTION_CHANGED, selected_node_ids=[n.id for n in nodes]
            )

    def set_selected_path(self, path: str):
        """Sets the selected sub-component path and publishes SUB_COMPONENT_SELECTED."""
        if self.selected_path != path:
            self.selected_path = path
            # Notify that a sub-component of the current selection (usually the first node) is focused
            node_id = self.selection[0].id if self.selection else None
            self._event_aggregator.publish(
                Events.SUB_COMPONENT_SELECTED, node_id=node_id, path=path
            )

    def set_scene_root(self, new_root: SceneNode):
        """Sets a new root for the scene graph."""
        self.scene_root = new_root
        self.set_selection([])

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    @property
    def file_path(self) -> Optional[Path]:
        return self._file_path

    @file_path.setter
    def file_path(self, path: Optional[Path]) -> None:
        if self._file_path != path:
            self._file_path = path

    def get_active_grid(self) -> Optional["GridNode"]:
        """
        Returns the primary GridNode managing the layout. 
        In Grid 2.0, this is typically the first GridNode child of the root.
        """
        for node in self.scene_root.all_descendants(of_type=GridNode):
            return node
        return None

    def add_node(self, node: SceneNode, parent: Optional[SceneNode] = None):
        """Adds a node to the scene graph."""
        if parent is None:
            parent = self.scene_root
        parent.add_child(node)
        # Dirty state is managed by the command adding the node.

    def extract_plot_states(self) -> list[dict]:
        """Extracts data and properties from all existing plot nodes."""
        existing_plot_states = []
        for node in self.scene_root.all_descendants():
            if isinstance(node, PlotNode) and node.data is not None:
                state = {
                    "data": node.data,
                    "plot_properties_dict": node.plot_properties.to_dict(),
                    "id": node.id,
                }
                existing_plot_states.append(state)
        self.logger.debug(
            f"Extracted {len(existing_plot_states)} existing plot states."
        )
        return existing_plot_states

    def get_node_at(self, position: tuple[float, float]) -> Optional[SceneNode]:
        """Finds the topmost node at the given figure coordinates."""
        return self.scene_root.hit_test(position)

    def as_dict(self) -> dict[str, Any]:
        """Serializes the application model to a dictionary."""
        return {
            "version": "1.0",
            "scene_root": self.scene_root.to_dict(),
            "layout_mode": self.layout_mode.value,
        }

    def load_from_state(self, data: dict[str, Any], temp_dir: Path):
        """Loads the application model from a dictionary."""
        self.reset_state()  # This will publish PROJECT_WAS_RESET, SELECTION_CHANGED, LAYOUT_CONFIG_CHANGED
        self.scene_root = node_factory(data["scene_root"], temp_dir=temp_dir)

        mode_str = data.get("layout_mode", "FREE_FORM")
        self.layout_mode = LayoutMode(mode_str)

        # After loading, the project is considered unmodified until a change is made
        self.set_dirty(False)
