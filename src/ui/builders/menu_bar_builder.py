from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar

from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


@dataclass
class MainMenuActions:
    # File Menu Actions
    file_menu: QMenu
    new_file_action: QAction
    new_file_from_template_action: QAction
    open_project_action: QAction
    open_recent_projects_menu: QMenu
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
    settings_action: QAction
    insert_tab_action: QAction
    design_tab_action: QAction
    layout_tab_action: QAction


class MenuBarBuilder:
    """
    Constructs the QMenuBar and connects its actions to publish events
    via the EventAggregator.
    """

    def __init__(self, event_aggregator: EventAggregator):
        self._event_aggregator = event_aggregator
        # TODO: A provider for the recent files list is still needed. This should
        # be implemented via an event loop (REQUEST_RECENT_PROJECTS_LIST -> RECENT_PROJECTS_LIST_UPDATED)
        # self._recent_files_provider = recent_files_provider

    def _update_recent_projects_menu(self, menu: QMenu):
        """
        Clears and repopulates the recent projects menu.
        TODO: This needs to be driven by an event, not a direct provider call.
        """
        menu.clear()
        # recent_files = self._recent_files_provider.get_recent_files()
        recent_files = []  # Placeholder

        if not recent_files:
            action = QAction("No Recent Projects", menu)
            action.setEnabled(False)
            menu.addAction(action)
            return

        for file_path_str in recent_files:
            action = QAction(file_path_str, menu)
            # Use a lambda to capture the file_path for the event payload
            action.triggered.connect(
                lambda checked=False, file_path=Path(
                    file_path_str
                ): self._event_aggregator.publish(
                    Events.OPEN_RECENT_PROJECT_REQUESTED, file_path=file_path
                )
            )
            menu.addAction(action)

    def _build_file_menu(self, menu_bar: QMenuBar):
        file_menu = menu_bar.addMenu("&File")

        new_file_action = file_menu.addAction("&New File...")
        new_file_action.setShortcut(QKeySequence.StandardKey.New)
        new_file_action.triggered.connect(
            lambda: self._event_aggregator.publish(Events.NEW_PROJECT_REQUESTED)
        )

        new_file_from_template_action = file_menu.addAction(
            "New File from &Template..."
        )
        new_file_from_template_action.setShortcut(QKeySequence("Shift+Ctrl+N"))
        new_file_from_template_action.triggered.connect(
            lambda: self._event_aggregator.publish(
                Events.NEW_PROJECT_FROM_TEMPLATE_REQUESTED
            )
        )

        file_menu.addSeparator()

        open_project_action = file_menu.addAction("&Open Project...")
        open_project_action.setShortcut(QKeySequence.StandardKey.Open)
        open_project_action.triggered.connect(
            lambda: self._event_aggregator.publish(Events.OPEN_PROJECT_REQUESTED)
        )

        open_recent_projects_menu = file_menu.addMenu("Open &Recent Projects")
        # TODO: Re-enable this when the recent files event loop is implemented
        # open_recent_projects_menu.aboutToShow.connect(
        #     lambda: self._update_recent_projects_menu(open_recent_projects_menu)
        # )
        open_recent_projects_menu.menuAction().setShortcut(QKeySequence("Ctrl+Shift+O"))

        file_menu.addSeparator()

        save_project_action = file_menu.addAction("&Save Project")
        save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        save_project_action.triggered.connect(
            lambda: self._event_aggregator.publish(Events.SAVE_PROJECT_REQUESTED)
        )

        save_copy_action = file_menu.addAction("Save a &Copy...")
        save_copy_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_copy_action.triggered.connect(
            lambda: self._event_aggregator.publish(Events.SAVE_PROJECT_AS_REQUESTED)
        )

        file_menu.addSeparator()
        close_action = file_menu.addAction("&Close")
        close_action.setShortcut(QKeySequence("Ctrl+W"))
        file_menu.addSeparator()

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
            new_file_action,
            new_file_from_template_action,
            open_project_action,
            open_recent_projects_menu,
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

    def _build_edit_menu(self, menu_bar: QMenuBar):
        edit_menu = menu_bar.addMenu("&Edit")

        undo_action = edit_menu.addAction("&Undo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(
            lambda: self._event_aggregator.publish(Events.UNDO_REQUESTED)
        )

        redo_action = edit_menu.addAction("&Redo")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(
            lambda: self._event_aggregator.publish(Events.REDO_REQUESTED)
        )

        edit_menu.addSeparator()
        cut_action = edit_menu.addAction("Cu&t")
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        copy_action = edit_menu.addAction("&Copy")
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        paste_action = edit_menu.addAction("&Paste")
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        edit_menu.addSeparator()
        settings_action = edit_menu.addAction("&Settings...")
        settings_action.setShortcut(QKeySequence("Ctrl+,"))

        return (
            edit_menu,
            undo_action,
            redo_action,
            cut_action,
            copy_action,
            paste_action,
            settings_action,
        )

    def build(self) -> tuple[QMenuBar, MainMenuActions]:
        menu_bar = QMenuBar()
        (
            file_menu,
            new_file_action,
            new_file_from_template_action,
            open_project_action,
            open_recent_projects_menu,
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
            settings_action,
        ) = self._build_edit_menu(menu_bar)

        # Build Ribbon Tab Selectors as Menu Items
        insert_tab_action = menu_bar.addAction("Insert")
        design_tab_action = menu_bar.addAction("Design")
        layout_tab_action = menu_bar.addAction("Layout")

        actions = MainMenuActions(
            file_menu=file_menu,
            new_file_action=new_file_action,
            new_file_from_template_action=new_file_from_template_action,
            open_project_action=open_project_action,
            open_recent_projects_menu=open_recent_projects_menu,
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
            settings_action=settings_action,
            insert_tab_action=insert_tab_action,
            design_tab_action=design_tab_action,
            layout_tab_action=layout_tab_action,
        )
        return menu_bar, actions
