from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QDockWidget

from src.commands import CommandManager
from src.models import ApplicationModel
from src.views.canvas_widget import CanvasWidget
from src.views.main_window import MainWindow
from src.views.properties_view import PropertiesView


class MainWindowBuilder:
    def __init__(self, model: ApplicationModel, command_manager: CommandManager):
        self.model = model
        self.command_manager = command_manager
        self.main_window = MainWindow()
        self.main_window.command_manager = command_manager

    def build_canvas(self):
        canvas = CanvasWidget(figure=self.model.figure, parent=self.main_window)
        self.main_window.setCentralWidget(canvas)
        self.main_window.canvas_widget = canvas
        return self

    def build_properties_dock(self):
        properties_view = PropertiesView(
            model=self.model, command_manager=self.command_manager
        )
        dock = QDockWidget("Properties", self.main_window)
        dock.setObjectName("Properties")
        dock.setWidget(properties_view)
        self.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self.main_window.properties_dock = dock
        self.main_window.properties_view = properties_view
        return self

    def build_menu(self):
        # This is the logic from the old _create_menu_bar method
        menu_bar = self.main_window.menuBar()
        self.main_window.menu_bar = menu_bar

        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File")
        self.main_window.file_menu = file_menu
        self.main_window.new_layout_action = file_menu.addAction("&New Layout...")

        # --- Edit Menu ---
        edit_menu = menu_bar.addMenu("&Edit")
        self.main_window.edit_menu = edit_menu

        undo_action = edit_menu.addAction("&Undo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.command_manager.undo)
        self.main_window.undo_action = undo_action

        redo_action = edit_menu.addAction("&Redo")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.command_manager.redo)
        self.main_window.redo_action = redo_action
        return self

    def get_window(self) -> MainWindow:
        """Returns the final, constructed window."""
        return self.main_window
