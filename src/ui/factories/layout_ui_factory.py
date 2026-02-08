import logging

from PySide6.QtCore import QObject
from PySide6.QtGui import QDoubleValidator, QIcon, QIntValidator, QValidator
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
from src.models.layout.layout_config import GridConfig
from src.shared.types import Margins, Gutters


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

    def build_layout_controls(self, layout_mode: LayoutMode, layout_controller: LayoutController, parent: QObject) -> QWidget:
        """
        Builds and returns a QWidget containing controls relevant to the given layout mode.
        """
        self.logger.debug(f"Building layout controls for mode: {layout_mode.value}")
        if layout_mode == LayoutMode.FREE_FORM:
            return self._build_free_form_controls(layout_controller, parent)
        elif layout_mode == LayoutMode.GRID:
            return self._build_grid_layout_controls(layout_controller, parent)
        else:
            self.logger.warning(f"Unknown layout mode '{layout_mode}'. Returning empty widget.")
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
        btn_align_left = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_horizontal_left")), "", container)
        btn_align_left.setToolTip("Align Left")
        btn_align_left.clicked.connect(lambda: layout_controller.align_selected_plots("left"))
        align_layout.addWidget(btn_align_left)

        # Align Horizontal Center
        btn_align_h_center = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_horizontal_center")), "", container)
        btn_align_h_center.setToolTip("Align Horizontal Center")
        btn_align_h_center.clicked.connect(lambda: layout_controller.align_selected_plots("h_center"))
        align_layout.addWidget(btn_align_h_center)

        # Align Right
        btn_align_right = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_horizontal_right")), "", container)
        btn_align_right.setToolTip("Align Right")
        btn_align_right.clicked.connect(lambda: layout_controller.align_selected_plots("right"))
        align_layout.addWidget(btn_align_right)

        align_layout.addStretch() # Spacer

        # Align Top
        btn_align_top = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_vertical_top")), "", container)
        btn_align_top.setToolTip("Align Top")
        btn_align_top.clicked.connect(lambda: layout_controller.align_selected_plots("top"))
        align_layout.addWidget(btn_align_top)

        # Align Vertical Center
        btn_align_v_center = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_vertical_center")), "", container)
        btn_align_v_center.setToolTip("Align Vertical Center")
        btn_align_v_center.clicked.connect(lambda: layout_controller.align_selected_plots("v_center"))
        align_layout.addWidget(btn_align_v_center)

        # Align Bottom
        btn_align_bottom = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_vertical_bottom")), "", container)
        btn_align_bottom.setToolTip("Align Bottom")
        btn_align_bottom.clicked.connect(lambda: layout_controller.align_selected_plots("bottom"))
        align_layout.addWidget(btn_align_bottom)

        layout.addWidget(QLabel("Alignment:")) # Label for clarity
        layout.addWidget(align_group_box)

        # Distribute Group
        distribute_group_box = QWidget(container)
        distribute_layout = QHBoxLayout(distribute_group_box)
        distribute_layout.setContentsMargins(0,0,0,0)

        # Distribute Horizontally
        btn_distribute_h = QPushButton(QIcon(IconPath.get_path("properties.distribute.horizontal_distribute")), "", container)
        btn_distribute_h.setToolTip("Distribute Horizontally")
        btn_distribute_h.clicked.connect(lambda: layout_controller.distribute_selected_plots("horizontal"))
        distribute_layout.addWidget(btn_distribute_h)

        # Distribute Vertically
        btn_distribute_v = QPushButton(QIcon(IconPath.get_path("properties.distribute.vertical_distribute")), "", container)
        btn_distribute_v.setToolTip("Distribute Vertically")
        btn_distribute_v.clicked.connect(lambda: layout_controller.distribute_selected_plots("vertical"))
        distribute_layout.addWidget(btn_distribute_v)

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
        default_grid_config_instance = self._layout_manager._create_default_grid_config()

        # Helper function to check if a config is 'default' for display purposes
        def is_default_grid_config(config: GridConfig) -> bool:
            # Compare all relevant fields to determine if it's still the default/placeholder
            return (config.rows == default_grid_config_instance.rows and
                    config.cols == default_grid_config_instance.cols and
                    config.margins == default_grid_config_instance.margins and
                    config.gutters == default_grid_config_instance.gutters)

        is_grid_inferred = not is_default_grid_config(current_grid_config)

        # Rows (QLineEdit)
        line_rows = QLineEdit(container)
        line_rows.setValidator(QIntValidator(1, 99))
        line_rows.setText(str(current_grid_config.rows) if is_grid_inferred else "")
        current_line_rows = line_rows # Capture the QLineEdit object
        line_rows.editingFinished.connect(lambda: self._handle_line_edit_change(layout_controller, "rows", current_line_rows))
        form_layout.addRow("Rows:", line_rows)

        # Columns (QLineEdit)
        line_cols = QLineEdit(container)
        line_cols.setValidator(QIntValidator(1, 99))
        line_cols.setText(str(current_grid_config.cols) if is_grid_inferred else "")
        current_line_cols = line_cols # Capture the QLineEdit object
        line_cols.editingFinished.connect(lambda: self._handle_line_edit_change(layout_controller, "cols", current_line_cols))
        form_layout.addRow("Cols:", line_cols)

        # Granular Margins (QLineEdit)
        # Top Margin
        line_margin_top = QLineEdit(container)
        # line_margin_top.setValidator(QDoubleValidator(0.0, 0.5, 3)) # Allow 3 decimal places - Temporarily commented out to enable editingFinished signal.
        line_margin_top.setText(str(current_grid_config.margins.top) if is_grid_inferred else "")
        current_line_margin_top = line_margin_top # Capture the QLineEdit object
        line_margin_top.editingFinished.connect(lambda: self._handle_line_edit_change(layout_controller, "margin_top", current_line_margin_top)) # TODO: Manual parsing/validation required for editingFinished
        form_layout.addRow("Margin Top:", line_margin_top)

        # Bottom Margin
        line_margin_bottom = QLineEdit(container)
        # line_margin_bottom.setValidator(QDoubleValidator(0.0, 0.5, 3)) # Temporarily commented out to enable editingFinished signal.
        line_margin_bottom.setText(str(current_grid_config.margins.bottom) if is_grid_inferred else "")
        current_line_margin_bottom = line_margin_bottom # Capture the QLineEdit object
        line_margin_bottom.editingFinished.connect(lambda: self._handle_line_edit_change(layout_controller, "margin_bottom", current_line_margin_bottom)) # TODO: Manual parsing/validation required for editingFinished
        form_layout.addRow("Margin Bottom:", line_margin_bottom)

        # Left Margin
        line_margin_left = QLineEdit(container)
        # line_margin_left.setValidator(QDoubleValidator(0.0, 0.5, 3)) # Temporarily commented out to enable editingFinished signal.
        line_margin_left.setText(str(current_grid_config.margins.left) if is_grid_inferred else "")
        current_line_margin_left = line_margin_left # Capture the QLineEdit object
        line_margin_left.editingFinished.connect(lambda: self._handle_line_edit_change(layout_controller, "margin_left", current_line_margin_left)) # TODO: Manual parsing/validation required for editingFinished
        form_layout.addRow("Margin Left:", line_margin_left)

        # Right Margin
        line_margin_right = QLineEdit(container)
        # line_margin_right.setValidator(QDoubleValidator(0.0, 0.5, 3)) # Temporarily commented out to enable editingFinished signal.
        line_margin_right.setText(str(current_grid_config.margins.right) if is_grid_inferred else "")
        current_line_margin_right = line_margin_right # Capture the QLineEdit object
        line_margin_right.editingFinished.connect(lambda: self._handle_line_edit_change(layout_controller, "margin_right", current_line_margin_right)) # TODO: Manual parsing/validation required for editingFinished
        form_layout.addRow("Margin Right:", line_margin_right)

        # Gutters (QLineEdit for list-based input)
        # Horizontal Space (hspace)
        line_hspace = QLineEdit(container)
        # Display current hspace list as comma-separated string
        line_hspace.setText(", ".join(map(str, current_grid_config.gutters.hspace)) if is_grid_inferred else "")
        line_hspace.setPlaceholderText("e.g., 0.1, 0.2")
        current_line_hspace = line_hspace # Capture the QLineEdit object
        line_hspace.editingFinished.connect(lambda: self._handle_line_edit_change(layout_controller, "hspace", current_line_hspace)) # TODO: Manual parsing/validation required for editingFinished
        form_layout.addRow("H-Space (csv):", line_hspace)

        # Vertical Space (wspace)
        line_wspace = QLineEdit(container)
        # Display current wspace list as comma-separated string
        line_wspace.setText(", ".join(map(str, current_grid_config.gutters.wspace)) if is_grid_inferred else "")
        line_wspace.setPlaceholderText("e.g., 0.1, 0.2")
        current_line_wspace = line_wspace # Capture the QLineEdit object
        line_wspace.editingFinished.connect(lambda: self._handle_line_edit_change(layout_controller, "wspace", current_line_wspace)) # TODO: Manual parsing/validation required for editingFinished
        form_layout.addRow("W-Space (csv):", line_wspace)


        overall_container_layout.addLayout(form_layout)
        
        # Infer Grid Button
        btn_infer_grid = QPushButton(QIcon(IconPath.get_path("properties.infer_grid")), "Infer Grid", container)
        btn_infer_grid.setToolTip("Infer grid parameters (rows, cols, margins, gutters) from current free-form plot positions.")
        btn_infer_grid.clicked.connect(self._layout_manager.infer_grid_parameters)
        overall_container_layout.addWidget(btn_infer_grid)

        # Optimize Layout Button (formerly Snap to Grid)
        btn_optimize_layout = QPushButton(QIcon(IconPath.get_path("properties.optimize_layout")), "Optimize Layout", container)
        btn_optimize_layout.setToolTip("Optimize layout using current grid parameters and Matplotlib's constrained layout.")
        btn_optimize_layout.clicked.connect(self._layout_manager.optimize_layout_action)
        overall_container_layout.addWidget(btn_optimize_layout)
        
        overall_container_layout.addStretch()

        return container

    def _handle_line_edit_change(self, layout_controller: LayoutController, param_name: str, line_edit: QLineEdit):
        # TODO: Manual parsing/validation required for editingFinished.
        # QDoubleValidator appears to suppress editingFinished, so we are disabling it for now.
        # This function will now receive values for margin fields without prior QDoubleValidator validation.
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
                return # Do not process invalid input if a validator is present and rejects it.
        else:
            # If no validator, attempt conversion to float, otherwise pass as string
            try:
                value_to_pass = float(raw_value)
            except ValueError:
                self.logger.debug(f"LayoutUIFactory: No validator for {param_name} and could not convert '{raw_value}' to float, passing as string.")

        self.logger.debug(f"LayoutUIFactory: Processing change for {param_name}. Value: {value_to_pass}")
        layout_controller.on_grid_layout_param_changed(param_name, value_to_pass)

