from dataclasses import dataclass

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar, QMainWindow

from src.commands import CommandManager


@dataclass
class MainMenuActions:
    menu_bar: QMenuBar
    # File Menu Actions
    file_menu: QMenu
    new_layout_action: QAction
    new_file_action: QAction
    new_file_from_template_action: QAction
    open_figure_action: QAction
    open_recent_figures_menu: QMenu
    close_action: QAction
    save_project_action: QAction
    save_copy_action: QAction
    export_figure_menu: QMenu
    export_vector_menu: QMenu
    export_raster_menu: QMenu
    export_svg_action: QAction
    export_pdf_action: QAction
    export_eps_action: QAction
    export_png_action: QAction
    export_tiff_action: QAction
    export_python_action: QAction
    exit_action: QAction
    # Edit Menu Actions
    edit_menu: QMenu
    undo_action: QAction
    redo_action: QAction
    cut_action: QAction
    copy_action: QAction
    paste_action: QAction
    colors_action: QAction
    settings_action: QAction


class MenuBarBuilder:
    def __init__(self, parent_window: QMainWindow, command_manager: CommandManager):
        self._parent_window = parent_window
        self._command_manager = command_manager

    def _build_file_menu(self, menu_bar: QMenuBar) -> tuple[
        QMenu, QAction, QAction, QAction, QAction, QMenu, QAction, QAction, QAction, QMenu, QMenu, QMenu, QAction, QAction, QAction, QAction, QAction, QAction, QAction
    ]:
        file_menu = menu_bar.addMenu("&File")

        new_layout_action = file_menu.addAction("&New Layout...")
        new_file_action = file_menu.addAction("&New File...")
        new_file_action.setShortcut(QKeySequence.StandardKey.New)
        new_file_from_template_action = file_menu.addAction("New File from &Template...")
        new_file_from_template_action.setShortcut(QKeySequence("Shift+Ctrl+N"))

        file_menu.addSeparator()

        open_figure_action = file_menu.addAction("&Open Figure...")
        open_figure_action.setShortcut(QKeySequence.StandardKey.Open)

        open_recent_figures_menu = file_menu.addMenu("&Open Recent Figures")
        open_recent_figures_menu.menuAction().setShortcut(QKeySequence("Ctrl+Shift+O"))

        close_action = file_menu.addAction("&Close")
        close_action.setShortcut(QKeySequence("Ctrl+W"))

        file_menu.addSeparator()

        save_project_action = file_menu.addAction("&Save Project")
        save_project_action.setShortcut(QKeySequence.StandardKey.Save)

        save_copy_action = file_menu.addAction("Save a &Copy...")
        save_copy_action.setShortcut(QKeySequence.StandardKey.SaveAs)

        export_figure_menu = file_menu.addMenu("&Export Figure")
        export_figure_menu.menuAction().setShortcut(QKeySequence("Ctrl+E"))

        vector_export_menu = export_figure_menu.addMenu("&Vector")
        export_svg_action = vector_export_menu.addAction("SVG...")
        export_pdf_action = vector_export_menu.addAction("PDF...")
        export_eps_action = vector_export_menu.addAction("EPS...")

        raster_export_menu = export_figure_menu.addMenu("&Raster")
        export_png_action = raster_export_menu.addAction("PNG...")
        export_tiff_action = raster_export_menu.addAction("TIFF...")

        export_python_action = export_figure_menu.addAction("Python...")

        file_menu.addSeparator()

        exit_action = file_menu.addAction("&Exit")
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)

        return (
            file_menu,
            new_layout_action,
            new_file_action,
            new_file_from_template_action,
            open_figure_action,
            open_recent_figures_menu,
            close_action,
            save_project_action,
            save_copy_action,
            export_figure_menu,
            vector_export_menu,
            raster_export_menu,
            export_svg_action,
            export_pdf_action,
            export_eps_action,
            export_png_action,
            export_tiff_action,
            export_python_action,
            exit_action,
        )

    def _build_edit_menu(self, menu_bar: QMenuBar) -> tuple[
        QMenu, QAction, QAction, QAction, QAction, QAction, QAction, QAction
    ]:
        edit_menu = menu_bar.addMenu("&Edit")

        undo_action = edit_menu.addAction("&Undo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._command_manager.undo)

        redo_action = edit_menu.addAction("&Redo")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self._command_manager.redo)

        edit_menu.addSeparator()

        cut_action = edit_menu.addAction("Cu&t")
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)

        copy_action = edit_menu.addAction("&Copy")
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)

        paste_action = edit_menu.addAction("&Paste")
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)

        edit_menu.addSeparator()

        colors_action = edit_menu.addAction("&Colors...")
        colors_action.setShortcut(QKeySequence("Ctrl+Shift+C"))

        settings_action = edit_menu.addAction("&Settings...")
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        
        return (
            edit_menu,
            undo_action,
            redo_action,
            cut_action,
            copy_action,
            paste_action,
            colors_action,
            settings_action,
        )

    def build(self) -> MainMenuActions:
        menu_bar = self._parent_window.menuBar()

        (
            file_menu,
            new_layout_action,
            new_file_action,
            new_file_from_template_action,
            open_figure_action,
            open_recent_figures_menu,
            close_action,
            save_project_action,
            save_copy_action,
            export_figure_menu,
            vector_export_menu,
            raster_export_menu,
            export_svg_action,
            export_pdf_action,
            export_eps_action,
            export_png_action,
            export_tiff_action,
            export_python_action,
            exit_action,
        ) = self._build_file_menu(menu_bar)

        (
            edit_menu,
            undo_action,
            redo_action,
            cut_action,
            copy_action,
            paste_action,
            colors_action,
            settings_action,
        ) = self._build_edit_menu(menu_bar)

        return MainMenuActions(
            menu_bar=menu_bar,
            file_menu=file_menu,
            new_layout_action=new_layout_action,
            new_file_action=new_file_action,
            new_file_from_template_action=new_file_from_template_action,
            open_figure_action=open_figure_action,
            open_recent_figures_menu=open_recent_figures_menu,
            close_action=close_action,
            save_project_action=save_project_action,
            save_copy_action=save_copy_action,
            export_figure_menu=export_figure_menu,
            export_vector_menu=vector_export_menu,
            export_raster_menu=raster_export_menu,
            export_svg_action=export_svg_action,
            export_pdf_action=export_pdf_action,
            export_eps_action=export_eps_action,
            export_png_action=export_png_action,
            export_tiff_action=export_tiff_action,
            export_python_action=export_python_action,
            exit_action=exit_action,
            edit_menu=edit_menu,
            undo_action=undo_action,
            redo_action=redo_action,
            cut_action=cut_action,
            copy_action=copy_action,
            paste_action=paste_action,
            colors_action=colors_action,
            settings_action=settings_action,
        )
