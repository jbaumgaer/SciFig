import logging
from typing import Optional

from PySide6.QtWidgets import (
    QGroupBox,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.controllers.layout_controller import LayoutController
from src.models.layout.layout_config import GridConfig
from src.services.event_aggregator import EventAggregator
from src.shared.constants import LayoutMode
from src.shared.events import Events
from src.ui.factories.layout_ui_factory import LayoutUIFactory


class LayoutTab(QWidget):
    def __init__(
        self,
        event_aggregator: EventAggregator,
        layout_controller: LayoutController,
        layout_ui_factory: LayoutUIFactory,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._event_aggregator = event_aggregator
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
        initial_ui_layout_mode = self.layout_controller.get_ui_selected_layout_mode()
        self._layout_mode_toggle_button.setChecked(
            initial_ui_layout_mode == LayoutMode.GRID
        )
        self._update_toggle_button_text(initial_ui_layout_mode)

        # Connect to layout_controller
        self._layout_mode_toggle_button.toggled.connect(
            self.layout_controller.toggle_layout_mode
        )  # TODO: Make this an event
        self._toggle_layout.addWidget(self._layout_mode_toggle_button)

        self._main_layout.addWidget(self._toggle_group)

        # --- Dynamic Layout Controls Container ---
        self._dynamic_layout_controls_stack = QStackedWidget(self)
        self._main_layout.addWidget(self._dynamic_layout_controls_stack)

        self._main_layout.addStretch()

        self._subscribe_to_events()

        self.logger.debug("LayoutTab initializing complete.")

        self._update_content(initial_ui_layout_mode)

    def _subscribe_to_events(self):
        self._event_aggregator.subscribe(
            Events.UI_LAYOUT_MODE_CHANGED, self._update_content
        )
        self._event_aggregator.subscribe(
            Events.UI_LAYOUT_MODE_CHANGED, self._update_toggle_button_text
        )
        self._event_aggregator.subscribe(
            Events.GRID_CONFIG_PARAMETERS_CHANGED, self._handle_grid_parameters_inferred
        )
        self._event_aggregator.subscribe(
            Events.NODE_LAYOUT_RECONCILED, self._handle_layout_config_changed
        )
        self._event_aggregator.subscribe(
            Events.ACTIVE_LAYOUT_MODE_CHANGED, self._handle_active_layout_mode_changed
        )

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
            ui_layout_mode = self.layout_controller.get_ui_selected_layout_mode()

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

    def _handle_grid_parameters_inferred(self, grid_config: GridConfig):
        """Handler for when grid parameters are inferred, to update UI."""
        self.logger.debug(
            f"LayoutTab: Grid parameters inferred. Updating UI with {grid_config}."
        )
        # Decoupling fix: Automatically switch the UI view to GRID mode so fields are visible,
        # but don't toggle the application's actual active layout mode yet.
        self.layout_controller.set_layout_mode(LayoutMode.GRID)
        self._update_content(LayoutMode.GRID)
        # Note: This updates the UI toggle button state as well via subscription

    def _handle_layout_config_changed(self, config: GridConfig):
        """Handler for when the application's active layout config changes."""
        self.logger.debug(
            f"LayoutTab: Active layout config changed to {config.mode}. Updating content."
        )
        # Rebuild content for the active mode, which will then reflect the new config
        self._update_content(config.mode)

    def _handle_active_layout_mode_changed(self, mode: LayoutMode):
        """Handler for when the application's active layout mode changes."""
        self.logger.debug(
            f"LayoutTab: Active layout mode changed to {mode}. Ensuring UI reflects this."
        )
        # Ensure the content shown matches the active mode
        self._update_content(mode)
