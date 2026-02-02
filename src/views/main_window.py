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
        self.new_file_action = None
        self.new_file_from_template_action = None
        self.open_figure_action = None
        self.open_recent_figures_menu = None
        self.close_action = None
        self.save_project_action = None
        self.save_copy_action = None
        self.export_figure_menu = None
        self.export_vector_menu = None
        self.export_raster_menu = None
        self.export_svg_action = None
        self.export_pdf_action = None
        self.export_eps_action = None
        self.export_png_action = None
        self.export_tiff_action = None
        self.export_python_action = None
        self.exit_action = None
        self.edit_menu = None
        self.undo_action = None
        self.redo_action = None
        self.cut_action = None
        self.copy_action = None
        self.paste_action = None
        self.colors_action = None
        self.settings_action = None

    def show_properties_panel(self):
        """Makes the properties dock widget visible and raises it to the top."""
        if self.properties_dock:  # Added check for None
            self.properties_dock.show()
            self.properties_dock.raise_()
