import logging

from PySide6.QtCore import QObject
from PySide6.QtGui import QDoubleValidator, QIcon, QIntValidator
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
from src.controllers.main_controller import MainController
from src.services.layout_manager import LayoutManager


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

    def build_layout_controls(self, layout_mode: LayoutMode, main_controller: MainController, parent: QObject) -> QWidget:
        """
        Builds and returns a QWidget containing controls relevant to the given layout mode.
        """
        self.logger.debug(f"Building layout controls for mode: {layout_mode.value}")
        if layout_mode == LayoutMode.FREE_FORM:
            return self._build_free_form_controls(main_controller, parent)
        elif layout_mode == LayoutMode.GRID:
            return self._build_grid_layout_controls(main_controller, parent)
        else:
            self.logger.warning(f"Unknown layout mode '{layout_mode}'. Returning empty widget.")
            return QWidget(parent) # Return an empty widget for unknown mode

    def _build_free_form_controls(self, main_controller: MainController, parent: QObject) -> QWidget:
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
        btn_align_left.clicked.connect(lambda: main_controller.align_selected_plots("left"))
        align_layout.addWidget(btn_align_left)

        # Align Horizontal Center
        btn_align_h_center = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_horizontal_center")), "", container)
        btn_align_h_center.setToolTip("Align Horizontal Center")
        btn_align_h_center.clicked.connect(lambda: main_controller.align_selected_plots("h_center"))
        align_layout.addWidget(btn_align_h_center)

        # Align Right
        btn_align_right = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_horizontal_right")), "", container)
        btn_align_right.setToolTip("Align Right")
        btn_align_right.clicked.connect(lambda: main_controller.align_selected_plots("right"))
        align_layout.addWidget(btn_align_right)

        align_layout.addStretch() # Spacer

        # Align Top
        btn_align_top = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_vertical_top")), "", container)
        btn_align_top.setToolTip("Align Top")
        btn_align_top.clicked.connect(lambda: main_controller.align_selected_plots("top"))
        align_layout.addWidget(btn_align_top)

        # Align Vertical Center
        btn_align_v_center = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_vertical_center")), "", container)
        btn_align_v_center.setToolTip("Align Vertical Center")
        btn_align_v_center.clicked.connect(lambda: main_controller.align_selected_plots("v_center"))
        align_layout.addWidget(btn_align_v_center)

        # Align Bottom
        btn_align_bottom = QPushButton(QIcon(IconPath.get_path("properties.alignment.align_vertical_bottom")), "", container)
        btn_align_bottom.setToolTip("Align Bottom")
        btn_align_bottom.clicked.connect(lambda: main_controller.align_selected_plots("bottom"))
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
        btn_distribute_h.clicked.connect(lambda: main_controller.distribute_selected_plots("horizontal"))
        distribute_layout.addWidget(btn_distribute_h)

        # Distribute Vertically
        btn_distribute_v = QPushButton(QIcon(IconPath.get_path("properties.distribute.vertical_distribute")), "", container)
        btn_distribute_v.setToolTip("Distribute Vertically")
        btn_distribute_v.clicked.connect(lambda: main_controller.distribute_selected_plots("vertical"))
        distribute_layout.addWidget(btn_distribute_v)

        layout.addWidget(QLabel("Distribution:")) # Label for clarity
        layout.addWidget(distribute_group_box)

        # Snap to Grid Button
        btn_snap_to_grid = QPushButton(QIcon(IconPath.get_path("properties.snap_to_grid")), "Snap Selected to Grid", container)
        btn_snap_to_grid.setToolTip("Snap Selected to Grid")
        btn_snap_to_grid.clicked.connect(main_controller.snap_free_plots_to_grid_action)
        layout.addWidget(btn_snap_to_grid)

        layout.addStretch() # Push everything to the top

        return container

    def _build_grid_layout_controls(self, main_controller: MainController, parent: QObject) -> QWidget:
        """
        Builds UI controls for Grid layout mode (e.g., set grid size, adjust ratios).
        Uses QLineEdit for input fields for rows, columns, margin, and gutter.
        Initializes values from the current LayoutManager's last grid config.
        Returns a QWidget containing these controls.
        """
        container = QWidget(parent)

        overall_container_layout = QVBoxLayout(container)
        overall_container_layout.setContentsMargins(0, 0, 0, 0)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)

        # Get current grid config from layout manager to initialize UI fields
        current_grid_config = self._layout_manager._last_grid_config

        # Rows (QLineEdit)
        line_rows = QLineEdit(container)
        line_rows.setValidator(QIntValidator(1, 99)) # Allow only integers between 1 and 99
        line_rows.setText(str(current_grid_config.rows))
        form_layout.addRow("Rows:", line_rows)

        # Columns (QLineEdit)
        line_cols = QLineEdit(container)
        line_cols.setValidator(QIntValidator(1, 99)) # Allow only integers between 1 and 99
        line_cols.setText(str(current_grid_config.cols))
        form_layout.addRow("Cols:", line_cols)

        # Margin (QLineEdit)
        line_margin = QLineEdit(container)
        # Allow floating point numbers (e.g., 0.0 to 0.5 with 2 decimal places)
        line_margin.setValidator(QDoubleValidator(0.0, 0.5, 2))
        line_margin.setText(str(current_grid_config.margin))
        form_layout.addRow("Margin:", line_margin)

        # Gutter (QLineEdit)
        line_gutter = QLineEdit(container)
        line_gutter.setValidator(QDoubleValidator(0.0, 0.5, 2))
        line_gutter.setText(str(current_grid_config.gutter))
        form_layout.addRow("Gutter:", line_gutter)

        # Connect editingFinished signals to the update method
        def _update_grid_parameters_on_edit_finish(): # Renamed function
            self.logger.debug("(_update_grid_parameters_on_edit_finish) called.")
            self.logger.debug(f"Current QLineEdit values: Rows='{line_rows.text()}', Cols='{line_cols.text()}', Margin='{line_margin.text()}', Gutter='{line_gutter.text()}'")

            # Get values and convert to appropriate types, handling potential conversion errors
            try:
                rows = int(line_rows.text()) if line_rows.text() else None
            except ValueError:
                rows = None
                self.logger.warning(f"Invalid input for rows: {line_rows.text()}")

            try:
                cols = int(line_cols.text()) if line_cols.text() else None
            except ValueError:
                cols = None
                self.logger.warning(f"Invalid input for cols: {line_cols.text()}")

            try:
                margin = float(line_margin.text()) if line_margin.text() else None
            except ValueError:
                margin = None
                self.logger.warning(f"Invalid input for margin: {line_margin.text()}")

            try:
                gutter = float(line_gutter.text()) if line_gutter.text() else None
            except ValueError:
                gutter = None
                self.logger.warning(f"Invalid input for gutter: {line_gutter.text()}")

            # Get the current grid config from the layout manager for comparison
            current_grid_config_for_comparison = self._layout_manager._last_grid_config

            # Only call if at least one value is valid and actually changed
            if (rows is not None and rows != current_grid_config_for_comparison.rows) or \
               (cols is not None and cols != current_grid_config_for_comparison.cols) or \
               (margin is not None and margin != current_grid_config_for_comparison.margin) or \
               (gutter is not None and gutter != current_grid_config_for_comparison.gutter):

                main_controller.update_grid_parameters(
                    rows=rows,
                    cols=cols,
                    margin=margin,
                    gutter=gutter,
                )
            else:
                self.logger.debug("No effective change in grid parameters detected or input is invalid.")

        line_rows.editingFinished.connect(_update_grid_parameters_on_edit_finish)
        line_cols.editingFinished.connect(_update_grid_parameters_on_edit_finish)
        line_margin.editingFinished.connect(_update_grid_parameters_on_edit_finish)
        line_gutter.editingFinished.connect(_update_grid_parameters_on_edit_finish)

        overall_container_layout.addLayout(form_layout)
        overall_container_layout.addStretch()

        return container
