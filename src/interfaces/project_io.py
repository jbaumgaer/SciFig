from pathlib import Path
from typing import Optional

from src.models.nodes.scene_node import SceneNode


# ---------------------------------------------------------------------------
# 1. Interface for the Model (Implemented by ApplicationModel)
#    Using a plain class to define the interface and avoid metaclass conflicts.
# ---------------------------------------------------------------------------
class ProjectLifecycle:
    """
    Defines the contract for a model managing the project's lifecycle state.
    """

    @property
    def is_dirty(self) -> bool:
        raise NotImplementedError

    def set_dirty(self, is_dirty: bool) -> None:
        raise NotImplementedError

    @property
    def file_path(self) -> Optional[Path]:
        raise NotImplementedError

    @file_path.setter
    def file_path(self, path: Optional[Path]) -> None:
        raise NotImplementedError

    def set_scene_root(self, root_node: SceneNode) -> None:
        raise NotImplementedError

    def extract_plot_states(self) -> list[dict[str, any]]:
        raise NotImplementedError

    def as_dict(self) -> dict[str, any]:
        raise NotImplementedError

    def load_from_state(self, state: dict[str, any], temp_dir: Path) -> None:
        raise NotImplementedError

    def reset_state(self) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 2. Interface for the Controller (Implemented by ProjectController)
# ---------------------------------------------------------------------------
class ProjectActions:
    """
    Defines the user-facing actions related to project I/O.
    """

    def handle_new_project(self) -> None:
        raise NotImplementedError

    def handle_new_from_template(self) -> None:  # No longer takes a template_name
        raise NotImplementedError

    def handle_open_project(self) -> None:
        raise NotImplementedError

    def handle_save_project(self) -> None:
        raise NotImplementedError

    def handle_save_as_project(self) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 3. Interface for the View (Implemented by MainWindow)
# ---------------------------------------------------------------------------
class ProjectIOView:
    """
    Defines the UI services a view must provide for project I/O operations.
    """

    def ask_for_open_path(self) -> Optional[Path]:
        raise NotImplementedError

    def ask_for_save_path(self) -> Optional[Path]:
        raise NotImplementedError

    def ask_for_template_path(self, template_dir: Path) -> Optional[Path]:
        raise NotImplementedError
