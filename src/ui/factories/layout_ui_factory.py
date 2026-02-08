import logging
from functools import partial
from typing import Any, Callable

from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon, QIntValidator, QValidator
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.services.config_service import ConfigService
from src.shared.constants import IconPath, LayoutMode

from src.services.layout_manager import LayoutManager
from src.controllers.layout_controller import LayoutController


class LayoutUIFactory:
    """
    A factory class responsible for building UI elements (QActions, QMenus)
    related to layout management, based on the current layout mode.
    """

    def __init__(self, config_service: ConfigService, layout_manager: LayoutManager):
        self._config_service = config_service
        self._layout_manager = layout_manager # Store LayoutManager instance
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("LayoutUIFactory initialized.")

    def _create_icon_button(self, icon_key: str, tooltip: str, command: Callable, parent: QWidget, object_name: str | None = None) -> QPushButton:
        """
        Helper to create an icon-only QPushButton with a tooltip and connected command.
        """
        button = QPushButton(QIcon(IconPath.get_path(icon_key)), "", parent)
        button.setToolTip(tooltip)
        if object_name:
            button.setObjectName(object_name)
        button.clicked.connect(command)
        return button

    def _create_parameter_line_edit(
        self,
        param_name: str,
        initial_value: Any,
        validator: QValidator | None,
        container: QWidget,
        layout_controller: LayoutController,
        placeholder_text: str | None = None,
        is_list_param: bool = False # Flag to indicate if the parameter is a list (e.g., hspace, wspace)
    ) -> QLineEdit:
        """
        Helper to create a QLineEdit for editing a layout parameter.
        Connects editingFinished signal to _handle_line_edit_change.
        """
        line_edit = QLineEdit(container)
        line_edit.setObjectName(f"{param_name}_edit")
        if initial_value is not None:
            if is_list_param and isinstance(initial_value, list):
                line_edit.setText(", ".join(map(str, initial_value)))
            else:
                line_edit.setText(str(initial_value))
        if validator:
            line_edit.setValidator(validator)
        if placeholder_text:
            line_edit.setPlaceholderText(placeholder_text)
        
        # Connect editingFinished to the handler, passing the line_edit instance
        line_edit.editingFinished.connect(partial(self._handle_line_edit_change, layout_controller, param_name, line_edit))
        return line_edit

    def build_layout_controls(self, layout_controller: LayoutController, parent: QObject) -> QWidget:
        """
        Builds and returns a QWidget containing controls relevant to the currently UI-selected layout mode.
        """
        ui_mode = self._layout_manager.ui_selected_layout_mode
        self.logger.debug(f"Building layout controls for UI selected mode: {ui_mode.value}")
        if ui_mode == LayoutMode.FREE_FORM:
            return self._build_free_form_controls(layout_controller, parent)
        elif ui_mode == LayoutMode.GRID:
            return self._build_grid_layout_controls(layout_controller, parent)
        else:
            self.logger.warning(f"Unknown UI selected layout mode '{ui_mode}'. Returning empty widget.")
            return QWidget(parent) # Return an empty widget for unknown mode

    def _build_free_form_controls(self, layout_controller: LayoutController, parent: QObject) -> QWidget:
        """
        Builds UI controls for Free-Form layout mode (e.g., alignment, distribution).
        Returns a QWidget containing these controls.
        """
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Align Group
        align_group_box = QWidget(container)
        align_layout = QHBoxLayout(align_group_box)
        align_layout.setContentsMargins(0,0,0,0)

        # Align Left
        align_layout.addWidget(self._create_icon_button("properties.alignment.align_horizontal_left", "Align Left", lambda: layout_controller.align_selected_plots("left"), container, "btn_align_left"))

        # Align Horizontal Center
        align_layout.addWidget(self._create_icon_button("properties.alignment.align_horizontal_center", "Align Horizontal Center", lambda: layout_controller.align_selected_plots("h_center"), container, "btn_align_h_center"))

        # Align Right
        align_layout.addWidget(self._create_icon_button("properties.alignment.align_horizontal_right", "Align Right", lambda: layout_controller.align_selected_plots("right"), container, "btn_align_right"))

        align_layout.addStretch() # Spacer

        # Align Top
        align_layout.addWidget(self._create_icon_button("properties.alignment.align_vertical_top", "Align Top", lambda: layout_controller.align_selected_plots("top"), container, "btn_align_top"))

        # Align Vertical Center
        align_layout.addWidget(self._create_icon_button("properties.alignment.align_vertical_center", "Align Vertical Center", lambda: layout_controller.align_selected_plots("v_center"), container, "btn_align_v_center"))

        # Align Bottom
        align_layout.addWidget(self._create_icon_button("properties.alignment.align_vertical_bottom", "Align Bottom", lambda: layout_controller.align_selected_plots("bottom"), container, "btn_align_bottom"))

        layout.addWidget(QLabel("Alignment:")) # Label for clarity
        layout.addWidget(align_group_box)

        # Distribute Group
        distribute_group_box = QWidget(container)
        distribute_layout = QHBoxLayout(distribute_group_box)
        distribute_layout.setContentsMargins(0,0,0,0)

        # Distribute Horizontally
        distribute_layout.addWidget(self._create_icon_button("properties.distribute.horizontal_distribute", "Distribute Horizontally", lambda: layout_controller.distribute_selected_plots("horizontal"), container, "btn_distribute_h"))

        # Distribute Vertically
        distribute_layout.addWidget(self._create_icon_button("properties.distribute.vertical_distribute", "Distribute Vertically", lambda: layout_controller.distribute_selected_plots("vertical"), container, "btn_distribute_v"))

        layout.addWidget(QLabel("Distribution:")) # Label for clarity
        layout.addWidget(distribute_group_box)

        layout.addStretch() # Push everything to the top

        return container

    def _build_grid_layout_controls(self, layout_controller: LayoutController, parent: QObject) -> QWidget:
        """
        Builds UI controls for Grid layout mode (e.g., set grid size, adjust ratios).
        Uses QLineEdit for rows and columns, QDoubleSpinBoxes for granular margins,
        and QLineEdits for list-based hspace and wspace.
        Initializes values from the current LayoutManager's last grid config.
        Returns a QWidget containing these controls.
        """
        container = QWidget(parent)

        overall_container_layout = QVBoxLayout(container)
        overall_container_layout.setContentsMargins(0, 0, 0, 0)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)

        current_grid_config = self._layout_manager._last_grid_config

        # Rows
        line_rows = self._create_parameter_line_edit("rows", current_grid_config.rows if current_grid_config else None, QIntValidator(1, 99), container, layout_controller)
        form_layout.addRow("Rows:", line_rows)

        # Columns
        line_cols = self._create_parameter_line_edit("cols", current_grid_config.cols if current_grid_config else None, QIntValidator(1, 99), container, layout_controller)
        form_layout.addRow("Cols:", line_cols)

        # Granular Margins
        line_margin_top = self._create_parameter_line_edit("margin_top", current_grid_config.margins.top if current_grid_config else None, None, container, layout_controller)
        form_layout.addRow("Margin Top:", line_margin_top)
        
        line_margin_bottom = self._create_parameter_line_edit("margin_bottom", current_grid_config.margins.bottom if current_grid_config else None, None, container, layout_controller)
        form_layout.addRow("Margin Bottom:", line_margin_bottom)
        
        line_margin_left = self._create_parameter_line_edit("margin_left", current_grid_config.margins.left if current_grid_config else None, None, container, layout_controller)
        form_layout.addRow("Margin Left:", line_margin_left)
        
        line_margin_right = self._create_parameter_line_edit("margin_right", current_grid_config.margins.right if current_grid_config else None, None, container, layout_controller)
        form_layout.addRow("Margin Right:", line_margin_right)

        # Gutters (list-based input)
        line_hspace = self._create_parameter_line_edit("hspace", current_grid_config.gutters.hspace if current_grid_config else None, None, container, layout_controller, placeholder_text="e.g., 0.1, 0.2", is_list_param=True)
        form_layout.addRow("H-Space (csv):", line_hspace)

        line_wspace = self._create_parameter_line_edit("wspace", current_grid_config.gutters.wspace if current_grid_config else None, None, container, layout_controller, placeholder_text="e.g., 0.1, 0.2", is_list_param=True)
        form_layout.addRow("W-Space (csv):", line_wspace)


        overall_container_layout.addLayout(form_layout)
        
        # Infer Grid Button
        btn_infer_grid = QPushButton("Infer Grid", container)
        btn_infer_grid.setIcon(QIcon(IconPath.get_path("properties.infer_grid")))
        btn_infer_grid.setToolTip("Infer grid parameters (rows, cols, margins, gutters) from current free-form plot positions.")
        btn_infer_grid.clicked.connect(self._layout_manager.infer_grid_parameters)
        overall_container_layout.addWidget(btn_infer_grid)

        # Optimize Layout Button (formerly Snap to Grid)
        btn_optimize_layout = QPushButton("Optimize Layout", container)
        btn_optimize_layout.setIcon(QIcon(IconPath.get_path("properties.optimize_layout")))
        btn_optimize_layout.setToolTip("Optimize layout using current grid parameters and Matplotlib's constrained layout.")
        btn_optimize_layout.clicked.connect(self._layout_manager.optimize_layout_action)
        overall_container_layout.addWidget(btn_optimize_layout)
        
        overall_container_layout.addStretch()

        return container

    def _handle_line_edit_change(self, layout_controller: LayoutController, param_name: str, line_edit: QLineEdit):
        raw_value = line_edit.text()
        value_to_pass = raw_value # Default to passing raw string

        validator = line_edit.validator()
        if validator:
            state, _, _ = validator.validate(raw_value, 0)
            self.logger.debug(f"LayoutUIFactory: Validator state for {param_name} ('{raw_value}'): {state} (0=Invalid, 1=Intermediate, 2=Acceptable)")
            if state == QValidator.Acceptable:
                # If a validator is present and accepts the input, try converting to float if applicable
                try:
                    value_to_pass = float(raw_value)
                except ValueError:
                    self.logger.debug(f"LayoutUIFactory: Could not convert '{raw_value}' to float for {param_name}, passing as string.")
            else:
                self.logger.warning(f"LayoutUIFactory: Input for {param_name} ('{raw_value}') is not acceptable (state: {state}). Not processing.")
                # Restore the original text if validation fails
                current_grid_config = self._layout_manager._last_grid_config
                if current_grid_config is not None:
                    if param_name.startswith("margin"):
                        if param_name == "margin_top": line_edit.setText(str(current_grid_config.margins.top))
                        elif param_name == "margin_bottom": line_edit.setText(str(current_grid_config.margins.bottom))
                        elif param_name == "margin_left": line_edit.setText(str(current_grid_config.margins.left))
                        elif param_name == "margin_right": line_edit.setText(str(current_grid_config.margins.right))
                    elif param_name == "rows":
                        line_edit.setText(str(current_grid_config.rows))
                    elif param_name == "cols":
                        line_edit.setText(str(current_grid_config.cols))
                    elif param_name == "hspace":
                        line_edit.setText(", ".join(map(str, current_grid_config.gutters.hspace)))
                    elif param_name == "wspace":
                        line_edit.setText(", ".join(map(str, current_grid_config.gutters.wspace)))
                else:
                    line_edit.setText("") # Clear the field if no current grid config to restore from
                return # Do not process invalid input if a validator is present and rejects it.
        else:
            # If no validator, attempt conversion to float, otherwise pass as string
            try:
                value_to_pass = float(raw_value)
            except ValueError:
                self.logger.debug(f"LayoutUIFactory: No validator for {param_name} and could not convert '{raw_value}' to float, passing as string.")

        self.logger.debug(f"LayoutUIFactory: Processing change for {param_name}. Value: {value_to_pass}")
        layout_controller.on_grid_layout_param_changed(param_name, value_to_pass)

