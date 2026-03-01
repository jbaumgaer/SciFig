from pathlib import Path
from typing import Protocol


class RecentFilesProvider(Protocol):
    """
    Defines the contract for an object that can provide a list of
    recent files and open one of them. This is used to decouple the
    MenuBarBuilder from the concrete ProjectController.
    """

    def get_recent_files(self) -> list[str]:
        """Returns a list of recent file paths as strings."""
        ...

    def open_project(self, file_path: Path) -> None:
        """Triggers the action to open a project from a given path."""
        ...
