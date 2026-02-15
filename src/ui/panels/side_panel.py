import logging
from typing import Optional

from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QTabWidget
)

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.ui.panels.layers_tab import LayersTab
from src.ui.panels.layout_tab import LayoutTab
from src.ui.panels.properties_tab import PropertiesTab


class SidePanel(QTabWidget):
    """
    A non-modal, tabbed panel that displays and allows editing of properties
    for the currently selected object(s) in the scene.
    """

    def __init__(
        self,
        model: ApplicationModel,
    ):
        super().__init__()
        # TODO: Check if I even pass a parent
        self.model = model
        self._tabs: dict[str, QWidget] = {}

        self.logger = logging.getLogger(self.__class__.__name__)

        # Connect model signals to the new _on_selection_changed method
        self.model.selectionChanged.connect(self._on_selection_changed)
        self._on_selection_changed() # Initial call to set up tab state
        self.logger.info("SidePanel initialized.")

    def add_tab(self, tab_key: str, tab_widget: QWidget, tab_name: str):
        """
        Adds a tab to the SidePanel, storing it in a dictionary.
        This generic method replaces add_properties_tab, add_layout_tab, add_layers_tab.
        """
        if tab_key in self._tabs:
            self.logger.warning(f"SidePanel: Tab with key '{tab_key}' already exists.")
            return
        self._tabs[tab_key] = tab_widget
        self.addTab(tab_widget, tab_name)
        self.logger.debug(f"SidePanel: Added tab '{tab_name}' with key '{tab_key}'.")

    @property
    def properties_tab(self) -> Optional[PropertiesTab]:
        return self._tabs.get("properties")
    
    @property
    def layout_tab(self) -> Optional[LayoutTab]:
        return self._tabs.get("layout")
    
    @property
    def layers_tab(self) -> Optional[LayersTab]:
        return self._tabs.get("layers")

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
        index = self.indexOf(
            getattr(self, f"{tab_name.lower().replace(' ', '_')}_tab")
        )
        if index != -1:
            self.setCurrentIndex(index)
            self.logger.debug(f"SidePanel: Switched to tab: {tab_name}")
        else:
            self.logger.warning(f"SidePanel: Tab '{tab_name}' not found.")
