from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QDockWidget, QMenuBar

from src.commands import CommandManager
from src.models import ApplicationModel
from src.models.nodes.plot_types import PlotType
from src.views.canvas_widget import CanvasWidget
from src.views.main_window import MainWindow
from src.views.properties_view import PropertiesView


class MainWindowBuilder:
    def __init__(self, model: ApplicationModel, command_manager: CommandManager, plot_types: list[PlotType]):
        self.model = model
        self.command_manager = command_manager
        self.plot_types = plot_types
        self.main_window = MainWindow()
        self.main_window.command_manager = command_manager

    def build_canvas(self):
        canvas = CanvasWidget(figure=self.model.figure, parent=self.main_window)
        self.main_window.setCentralWidget(canvas)
        self.main_window.canvas_widget = canvas
        return self

    def build_properties_dock(self):
        properties_view = PropertiesView(
            model=self.model,
            command_manager=self.command_manager,
            plot_types=self.plot_types,
        )
        dock = QDockWidget("Properties", self.main_window)
        dock.setObjectName("Properties")
        dock.setWidget(properties_view)
        self.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.main_window.properties_dock = dock
        self.main_window.properties_view = properties_view
        return self

    def build_menu(self):
        menu_bar = self.main_window.menuBar()
        self._build_file_menu(menu_bar=menu_bar)
        self._build_edit_menu(menu_bar=menu_bar)
        self.main_window.menu_bar = menu_bar
        return self
    
    def _build_file_menu(self, menu_bar: QMenuBar):
        file_menu = menu_bar.addMenu("&File")
        self.main_window.file_menu = file_menu
        self.main_window.new_layout_action = file_menu.addAction("&New Layout...")
        new_file_action = file_menu.addAction("&New File...")
        new_file_action.setShortcut(QKeySequence.StandardKey.New)
        self.main_window.new_file_action = new_file_action
        new_file_from_template_action = file_menu.addAction("New File from &Template...")
        new_file_from_template_action.setShortcut(QKeySequence("Shift+Ctrl+N"))
        self.main_window.new_file_from_template_action = new_file_from_template_action

        file_menu.addSeparator()

        open_figure_action = file_menu.addAction("&Open Figure...")
        open_figure_action.setShortcut(QKeySequence.StandardKey.Open)
        self.main_window.open_figure_action = open_figure_action

        open_recent_figures_menu = file_menu.addMenu("&Open Recent Figures")
        open_recent_figures_menu.menuAction().setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.main_window.open_recent_figures_menu = open_recent_figures_menu

        close_action = file_menu.addAction("&Close")
        close_action.setShortcut(QKeySequence("Ctrl+W"))
        self.main_window.close_action = close_action

        file_menu.addSeparator()

        save_project_action = file_menu.addAction("&Save Project")
        save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        self.main_window.save_project_action = save_project_action

        save_copy_action = file_menu.addAction("Save a &Copy...")
        save_copy_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.main_window.save_copy_action = save_copy_action

        export_figure_menu = file_menu.addMenu("&Export Figure")
        export_figure_menu.menuAction().setShortcut(QKeySequence("Ctrl+E"))
        self.main_window.export_figure_menu = export_figure_menu

        vector_export_menu = export_figure_menu.addMenu("&Vector")
        self.main_window.export_vector_menu = vector_export_menu
        export_svg_action = vector_export_menu.addAction("SVG...")
        export_pdf_action = vector_export_menu.addAction("PDF...")
        export_eps_action = vector_export_menu.addAction("EPS...")
        self.main_window.export_svg_action = export_svg_action
        self.main_window.export_pdf_action = export_pdf_action
        self.main_window.export_eps_action = export_eps_action

        raster_export_menu = export_figure_menu.addMenu("&Raster")
        self.main_window.export_raster_menu = raster_export_menu
        export_png_action = raster_export_menu.addAction("PNG...")
        export_tiff_action = raster_export_menu.addAction("TIFF...")
        self.main_window.export_png_action = export_png_action
        self.main_window.export_tiff_action = export_tiff_action

        export_python_action = export_figure_menu.addAction("Python...")
        self.main_window.export_python_action = export_python_action

        file_menu.addSeparator()

        exit_action = file_menu.addAction("&Exit")
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.main_window.exit_action = exit_action
        return self
    
    def _build_edit_menu(self, menu_bar: QMenuBar):
        
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

        edit_menu.addSeparator()

        cut_action = edit_menu.addAction("Cu&t")
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.main_window.cut_action = cut_action

        copy_action = edit_menu.addAction("&Copy")
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.main_window.copy_action = copy_action

        paste_action = edit_menu.addAction("&Paste")
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.main_window.paste_action = paste_action

        edit_menu.addSeparator()

        colors_action = edit_menu.addAction("&Colors...")
        colors_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.main_window.colors_action = colors_action

        settings_action = edit_menu.addAction("&Settings...")
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.main_window.settings_action = settings_action
        return self
        


    def get_window(self) -> MainWindow:
        """Returns the final, constructed window."""
        return self.main_window
