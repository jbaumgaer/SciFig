import logging
from typing import Optional

from PySide6.QtWidgets import (
    QGroupBox,  # New Import
    QStackedWidget,  # New Import for dynamic content
    QToolButton,  # New Import
    QVBoxLayout,
    QWidget,
)

from src.controllers.layout_controller import LayoutController
from src.models.application_model import ApplicationModel
from src.shared.constants import LayoutMode  # New Import
from src.ui.factories.layout_ui_factory import LayoutUIFactory


class LayoutTab(QWidget):
    def __init__(
        self,
        model: ApplicationModel,
        layout_controller: LayoutController,
        layout_ui_factory: LayoutUIFactory,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.model = model
        self.layout_controller = layout_controller
        self.layout_ui_factory = layout_ui_factory
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("LayoutTab initialized.")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Layout UI Type Toggle Section ---
        self._toggle_group = QGroupBox("Layout Controls Type", self)
        self._toggle_layout = QVBoxLayout(
            self._toggle_group
        )  # Use QVBoxLayout for GroupBox content

        self._layout_mode_toggle_button = QToolButton(self)
        self._layout_mode_toggle_button.setCheckable(True)
        self._layout_mode_toggle_button.setStyleSheet(
            "QToolButton:checked { background-color: lightgray; }"
        )  # TODO: magic number

        # Set initial state and text
        initial_ui_layout_mode = (
            self.layout_controller._layout_manager.ui_selected_layout_mode
        )
        self._layout_mode_toggle_button.setChecked(
            initial_ui_layout_mode == LayoutMode.GRID
        )
        self._update_toggle_button_text(initial_ui_layout_mode)

        # Connect to layout_controller
        self._layout_mode_toggle_button.toggled.connect(
            self.layout_controller.toggle_layout_mode
        )
        self._toggle_layout.addWidget(self._layout_mode_toggle_button)

        self._main_layout.addWidget(self._toggle_group)

        # --- Dynamic Layout Controls Container ---
        self._dynamic_layout_controls_stack = QStackedWidget(self)
        self._main_layout.addWidget(self._dynamic_layout_controls_stack)

        self._main_layout.addStretch()

        # Connect signals
        self.layout_controller._layout_manager.uiLayoutModeChanged.connect(
            self._update_content
        )
        self.layout_controller._layout_manager.uiLayoutModeChanged.connect(
            self._update_toggle_button_text
        )
        self.layout_controller._layout_manager.gridConfigParametersChanged.connect(
            self._update_content
        )
        self._update_content(
            initial_ui_layout_mode
        )  # Initial call to populate dynamic controls

    def _clear_stacked_widget(self, stacked_widget: QStackedWidget):
        """Clears all widgets from a QStackedWidget."""
        for i in reversed(range(stacked_widget.count())):
            widget_to_remove = stacked_widget.widget(i)
            stacked_widget.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

    def _update_content(self, ui_layout_mode: Optional[LayoutMode] = None):
        """
        Updates the dynamic layout controls based on the selected UI layout mode.
        """
        # If ui_layout_mode is not provided (e.g., when called by a signal that doesn't pass args),
        # use the currently active UI selected layout mode from the layout manager.
        if ui_layout_mode is None:
            ui_layout_mode = self.layout_controller._layout_manager.ui_selected_layout_mode
        
        self.logger.debug(
            f"LayoutTab: Updating content for UI layout mode: {ui_layout_mode.value}"
        )

        # Clear existing widgets from the QStackedWidget
        self._clear_stacked_widget(self._dynamic_layout_controls_stack)

        # Build and add new controls
        layout_controls_widget = self.layout_ui_factory.build_layout_controls(
            self.layout_controller,
            self._dynamic_layout_controls_stack,  # Parent is the stacked widget
        )
        self._dynamic_layout_controls_stack.addWidget(layout_controls_widget)
        # We only have one widget at a time, so set current index to 0
        self._dynamic_layout_controls_stack.setCurrentIndex(0)

    def _update_toggle_button_text(self, ui_layout_mode: LayoutMode):
        """
        Updates the text of the layout mode toggle button based on the current UI selected mode.
        """
        if ui_layout_mode == LayoutMode.GRID:
            self._layout_mode_toggle_button.setText(
                "Switch to Free-Form Layout Controls"
            )
        else:
            self._layout_mode_toggle_button.setText("Switch to Grid Layout Controls")
