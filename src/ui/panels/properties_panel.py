import logging

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLineEdit,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.shared.types import Layout
from src.controllers.node_controller import NodeController
from src.controllers.layout_controller import LayoutController
from src.shared.constants import LayoutMode
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.properties_ui_factory import PropertiesUIFactory


class PropertiesPanel(QWidget):
    """
    A non-modal panel that displays and allows editing of properties
    for the currently selected object(s) in the scene.
    """

    def __init__(
        self,
        model: ApplicationModel,
        node_controller: NodeController,
        layout_controller: LayoutController,
        properties_ui_factory: PropertiesUIFactory,
        layout_ui_factory: LayoutUIFactory,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setFixedWidth(250)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.model = model
        self.node_controller = node_controller
        self.layout_controller = layout_controller
        self.properties_ui_factory = properties_ui_factory
        self._layout_ui_factory = layout_ui_factory
        # self._layout_manager and self._main_controller are removed as per refactoring

        # Main layout for the entire PropertiesView
        self._overall_layout = QVBoxLayout(self)
        self._overall_layout.setContentsMargins(5, 5, 5, 5) #TODO: These are magic numbers and should go into config

        # Layout Mode Toggle Button (persistent at the top)
        self.layout_mode_toggle_button = QToolButton(self)
        self.layout_mode_toggle_button.setCheckable(True)
        self.layout_mode_toggle_button.setStyleSheet("QToolButton:checked { background-color: lightgray; }")
         #TODO: These are magic numbers and should go into config

        # Set initial state and text
        initial_layout_mode = self.layout_controller._layout_manager.layout_mode # This is a bit of a code smell
        self.layout_mode_toggle_button.setChecked(initial_layout_mode == LayoutMode.GRID)
        self._update_layout_mode_toggle_button_ui(initial_layout_mode)

        # Connect to layout_controller
        self.layout_mode_toggle_button.toggled.connect(self.layout_controller.toggle_layout_mode)

        # Connect to update UI based on layout manager changes
        self.layout_controller._layout_manager.layoutModeChanged.connect(self._update_layout_mode_toggle_button_ui)

        self._overall_layout.addWidget(self.layout_mode_toggle_button)
        self._overall_layout.addSpacing(10)  #TODO: These are magic numbers and should go into config

        # Container for the dynamic content
        self._dynamic_content_widget = QWidget(self)
        self._main_layout = QVBoxLayout(self._dynamic_content_widget) # This will be the layout for dynamic content
        self._main_layout.setContentsMargins(0,0,0,0) #TODO: These are magic numbers and should go into config

        self._overall_layout.addWidget(self._dynamic_content_widget)
        self._overall_layout.addStretch() # Take up remaining space

        self._limit_edits: dict[str, QLineEdit] = {}
        self._current_node: PlotNode | None = None
        self._x_combo: QComboBox | None = None
        self._y_combo: QComboBox | None = None

        self.logger = logging.getLogger(self.__class__.__name__)

        self.model.selectionChanged.connect(self._update_content)
        self.layout_controller._layout_manager.layoutModeChanged.connect(self._update_content) # New connection
        self._update_content() # Initial call at the end of __init__

    def _clear_layout(self, layout: Layout):
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
        # Clear references to combo boxes after they are potentially deleted by deleteLater
        self._x_combo = None
        self._y_combo = None

    def _update_content(self):
        """
        Updates the content of the properties panel based on current selection
        and layout mode.
        """
        self.logger.debug("Updating properties panel content.")
        self._current_node = None
        self._clear_layout(self._main_layout)
        selection = self.model.selection

        # Condition 1: Single PlotNode with data selected
        if len(selection) == 1 and isinstance(selection[0], PlotNode) and selection[0].data is not None:
            node = selection[0]
            self._current_node = node
            form_layout = QFormLayout()

            self._x_combo = QComboBox()
            self._y_combo = QComboBox()

            self.properties_ui_factory.build_widgets(
                node,
                form_layout,
                self,
                self._limit_edits,
                self._x_combo,
                self._y_combo,
            )
            self._main_layout.addLayout(form_layout)
            self._main_layout.addStretch()
            self.logger.debug(f"Displayed properties for selected PlotNode: {node.name}")
        # Condition 2: Otherwise (Default/Layout Controls)
        else:
            self.logger.debug("Displaying layout controls.")
            layout_controls_widget = self._layout_ui_factory.build_layout_controls(
                self.layout_controller._layout_manager.layout_mode, self.layout_controller, self
            )
            self._main_layout.addWidget(layout_controls_widget)
            self._main_layout.addStretch()
            self.logger.debug("Displayed layout controls.")

    def _update_layout_mode_toggle_button_ui(self, layout_mode: LayoutMode):
        """
        Updates the text and checked state of the layout mode toggle button.
        """
        if layout_mode == LayoutMode.GRID:
            self.layout_mode_toggle_button.setText("Layout Mode: Grid")
            self.layout_mode_toggle_button.setChecked(True)
        else:
            self.layout_mode_toggle_button.setText("Layout Mode: Free Form")
            self.layout_mode_toggle_button.setChecked(False)



