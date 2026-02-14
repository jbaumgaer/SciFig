import logging
from typing import Optional

from PySide6.QtWidgets import (
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QTabWidget
)

from src.controllers.layout_controller import LayoutController
from src.controllers.node_controller import NodeController
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
# from src.shared.types import Layout # Removed - not needed for QTabWidget
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.plot_properties_ui_factory import (
    PlotPropertiesUIFactory,
)
from src.ui.panels.layers_tab import LayersTab
from src.ui.panels.layout_tab import LayoutTab

# New Tab Imports
from src.ui.panels.properties_tab import PropertiesTab
from src.controllers.project_controller import ProjectController


class SidePanel(QTabWidget):
    """
    A non-modal, tabbed panel that displays and allows editing of properties
    for the currently selected object(s) in the scene.
    """

    def __init__(
        self,
        model: ApplicationModel,
        node_controller: NodeController,
        layout_controller: LayoutController,
        plot_properties_ui_factory: PlotPropertiesUIFactory,
        layout_ui_factory: LayoutUIFactory,
        project_controller: ProjectController,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        # TODO: Check if I even pass a parent
        # self.setFixedWidth(250) # Removed - Managed by QDockWidget
        # self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred) # Removed - Managed by QDockWidget
        self.model = model
        self.node_controller = node_controller
        self.layout_controller = layout_controller
        self.plot_properties_ui_factory = plot_properties_ui_factory
        self._layout_ui_factory = layout_ui_factory
        self._project_controller = project_controller

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("SidePanel initialized.")

        # self._overall_layout = QVBoxLayout(self) # Removed - QTabWidget manages its own layout
        # self._overall_layout.setContentsMargins(5, 5, 5, 5)

        # Create QTabWidget (SidePanel is now the QTabWidget itself)
        # self.tab_widget = QTabWidget(self) # Removed
        # self._overall_layout.addWidget(self.tab_widget) # Removed

        # Instantiate tabs
        self.properties_tab = PropertiesTab(
            model=self.model,
            node_controller=self.node_controller,
            plot_properties_ui_factory=self.plot_properties_ui_factory,
            project_controller=self._project_controller,
            parent=self,
        )
        self.layout_tab = LayoutTab(
            model=self.model,
            layout_controller=self.layout_controller,
            layout_ui_factory=self._layout_ui_factory,
            parent=self,
        )
        self.layers_tab = LayersTab(
            model=self.model,
            node_controller=self.node_controller,
            parent=self,
        )

        # Add tabs to the QTabWidget (SidePanel itself)
        self.addTab(self.properties_tab, "Properties")
        self.addTab(self.layout_tab, "Layout")
        self.addTab(self.layers_tab, "Layers")

        # self._overall_layout.addStretch() # Removed

        # Connect model signals to the new _on_selection_changed method
        self.model.selectionChanged.connect(self._on_selection_changed)
        self._on_selection_changed() # Initial call to set up tab state

    # _clear_layout is no longer strictly needed in SidePanel, but kept for consistency if tabs need it internally
    def _clear_layout(self, layout: Optional[QVBoxLayout]): # Changed type hint to Optional[QVBoxLayout]
        """Recursively clears all widgets and sub-layouts."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clear_layout(sub_layout)


    def _on_selection_changed(self):
        """
        Handles changes in application model selection, potentially switching tabs.
        """
        self.logger.debug(
            "SidePanel: Selection changed. Checking for PlotNode selection."
        )
        selection = self.model.selection
        if len(selection) == 1 and isinstance(selection[0], PlotNode):
            self.logger.debug(
                "SidePanel: Single PlotNode selected. Switching to Properties tab."
            )
            self.setCurrentWidget(self.properties_tab) # Changed
        # Future: Handle other node types or no selection gracefully

    def show_tab_by_name(self, tab_name: str):
        """
        Programmatically switches to the specified tab by name.
        """
        # Removed self.tab_widget.indexOf and self.tab_widget.setCurrentIndex
        index = self.indexOf(
            getattr(self, f"{tab_name.lower().replace(' ', '_')}_tab")
        )
        if index != -1:
            self.setCurrentIndex(index)
            self.logger.debug(f"SidePanel: Switched to tab: {tab_name}")
        else:
            self.logger.warning(f"SidePanel: Tab '{tab_name}' not found.")
