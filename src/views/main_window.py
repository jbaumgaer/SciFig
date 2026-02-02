from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QWidget,
)

from src.commands import CommandManager

from .properties_view import PropertiesView


class MainWindow(QMainWindow):
    """
    The main application window (View). It acts as the primary container for
    the application's UI components, including the canvas and properties panel.
    """

    def __init__(self):  # Removed model and command_manager from signature
        """TODO: Change the fact that everything can be initialized with None.
        Assume that these must be set, just not in the initializer."""
        super().__init__()
        self.setWindowTitle("SciFig - Data Analysis GUI")
        self.setGeometry(50, 50, 800, 600)

        self.command_manager: CommandManager | None = None  # Will be set by builder

        self.canvas_widget: QWidget | None = None  # Will be set by builder
        self.properties_view: PropertiesView | None = None  # Will be set by builder
        self.properties_dock: QDockWidget | None = None  # Will be set by builder

        # Menu components will be set by the builder
        self.menu_bar = None
        self.file_menu = None
        self.new_layout_action = None
        self.edit_menu = None
        self.undo_action = None
        self.redo_action = None

    def show_properties_panel(self):
        """Makes the properties dock widget visible and raises it to the top."""
        if self.properties_dock:  # Added check for None
            self.properties_dock.show()
            self.properties_dock.raise_()
