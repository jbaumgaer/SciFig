from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QIcon, QIntValidator
from PySide6.QtWidgets import (
    QLineEdit,  # Updated from QSpinBox
    QPushButton,
    QWidget,
)

from src.controllers.layout_controller import (
    LayoutController,
)  # Changed from MainController
from src.models.layout.layout_config import (
    GridConfig,
    Gutters,
    Margins,
)  # Import new config classes
from src.models.layout.layout_engine import LayoutMode
from src.services.config_service import ConfigService
from src.services.layout_manager import LayoutManager
from src.ui.factories.layout_ui_factory import LayoutUIFactory


@pytest.fixture
def mock_config_service():
    """Fixture for a mock ConfigService."""
    config_service = MagicMock(spec=ConfigService)
    # Mock specific icon paths to return dummy SVG paths
    config_service.get.side_effect = lambda key, default=None: {
        "paths.icon_base_dir": "src/assets/icons",  # Base directory
        "paths.properties.alignment.align_horizontal_left": "properties/alignment/align_horizontal_left_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_horizontal_center": "properties/alignment/align_horizontal_center_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_horizontal_right": "properties/alignment/align_horizontal_right_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_vertical_top": "properties/alignment/align_vertical_top_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_vertical_center": "properties/alignment/align_vertical_center_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_vertical_bottom": "properties/alignment/align_vertical_bottom_24dp_E3E3E3.svg",
        "paths.properties.distribute.horizontal_distribute": "properties/distribute/horizontal_distribute_24dp_E3E3E3.svg",
        "paths.properties.distribute.vertical_distribute": "properties/distribute/vertical_distribute_24dp_E3E3E3.svg",
        "paths.properties.infer_grid": "properties/infer_grid_24dp_E3E3E3.svg",  # New icon key
        "paths.properties.optimize_layout": "properties/optimize_layout_24dp_E3E3E3.svg",  # New icon key
        "layout.default_grid_rows": 2,  # Example values for minimal config
        "layout.default_grid_cols": 2,
        "layout.grid_margin_top": 0.05,
        "layout.grid_margin_bottom": 0.05,
        "layout.grid_margin_left": 0.05,
        "layout.grid_margin_right": 0.05,
        "layout.grid_hspace": [0.02],
        "layout.grid_wspace": [0.02],
    }.get(key, default)
    return config


@pytest.fixture
def mock_layout_controller():
    """
    Fixture for a mock LayoutController.
    """
    controller = MagicMock(spec=LayoutController)
    controller.align_selected_plots = MagicMock()
    controller.distribute_selected_plots = MagicMock()
    controller.on_grid_layout_param_changed = MagicMock()
    return controller


@pytest.fixture
def mock_layout_manager():
    """
    Fixture for a mock LayoutManager.
    """
    manager = MagicMock(spec=LayoutManager)
    manager._last_grid_config = None  # Initially None for testing
    manager.layout_mode = LayoutMode.FREE_FORM  # Default mode
    manager.infer_grid_parameters = MagicMock()
    manager.optimize_layout_action = MagicMock()
    # Provide a minimal grid config for when it's requested
    manager._create_minimal_grid_config.return_value = GridConfig(
        rows=1,
        cols=1,
        row_ratios=[1.0],
        col_ratios=[1.0],
        margins=Margins(top=0.05, bottom=0.05, left=0.05, right=0.05),
        gutters=Gutters(hspace=[0.02], wspace=[0.02]),
    )
    return manager


@pytest.fixture
def layout_ui_factory(mock_config_service, mock_layout_manager):
    """
    Fixture for a LayoutUIFactory instance.
    """
    # Patch IconPath.set_config_service to prevent actual class attribute modification
    with patch("src.shared.constants.IconPath.set_config_service"):
        factory = LayoutUIFactory(mock_config_service, mock_layout_manager)
        yield factory


class TestLayoutUIFactory:
    """
    Tests for the LayoutUIFactory class, updated for refactored GridConfig handling.
    """

    def test_build_layout_controls_free_form_mode(
        self, layout_ui_factory, mock_layout_controller, mock_layout_manager
    ):
        """
        Test that build_layout_controls builds free form controls with icon buttons
        when ui_selected_layout_mode is FREE_FORM.
        """
        mock_layout_manager.ui_selected_layout_mode = (
            LayoutMode.FREE_FORM
        )  # Set UI selected mode
        parent_widget = QWidget()
        controls = layout_ui_factory.build_layout_controls(
            mock_layout_controller, parent_widget
        )
        assert isinstance(controls, QWidget)

        buttons = controls.findChildren(QPushButton)
        assert len(buttons) == 8  # 6 alignment + 2 distribution buttons

        for btn in buttons:
            assert isinstance(btn.icon(), QIcon)
            assert not btn.icon().isNull()
            # Ensure text is empty, as they are icon-only buttons
            assert btn.text() == ""
            # Ensure connections are made
            if "Align" in btn.toolTip():
                btn.clicked.emit()
                mock_layout_controller.align_selected_plots.assert_called()
                mock_layout_controller.align_selected_plots.reset_mock()
            elif "Distribute" in btn.toolTip():
                btn.clicked.emit()
                mock_layout_controller.distribute_selected_plots.assert_called()
                mock_layout_controller.distribute_selected_plots.reset_mock()

    def test_build_layout_controls_grid_mode(
        self, layout_ui_factory, mock_layout_controller, mock_layout_manager
    ):
        """
        Test that build_layout_controls builds grid layout controls when ui_selected_layout_mode is GRID.
        """
        mock_layout_manager.ui_selected_layout_mode = (
            LayoutMode.GRID
        )  # Set UI selected mode
        mock_layout_manager._last_grid_config = GridConfig(
            rows=1, cols=1, margins=Margins(0, 0, 0, 0), gutters=Gutters([], [])
        )  # Provide a minimal config
        parent_widget = QWidget()
        controls = layout_ui_factory.build_layout_controls(
            mock_layout_controller, parent_widget
        )
        assert isinstance(controls, QWidget)

        # Check for grid-specific QLineEdits
        rows_edit = controls.findChild(QLineEdit, "rows_edit")
        assert rows_edit is not None
        cols_edit = controls.findChild(QLineEdit, "cols_edit")
        assert cols_edit is not None

        # Check for grid-specific buttons
        infer_btn = controls.findChild(QPushButton, "btn_infer_grid")
        assert infer_btn is not None
        optimize_btn = controls.findChild(QPushButton, "btn_optimize_layout")
        assert optimize_btn is not None

    def test_build_grid_layout_controls_no_active_config(
        self, layout_ui_factory, mock_layout_controller, mock_layout_manager
    ):
        """
        Test that _build_grid_layout_controls initializes QLineEdits with empty values
        when _last_grid_config in LayoutManager is None.
        """
        mock_layout_manager._last_grid_config = None  # Explicitly set to None
        parent_widget = QWidget()
        controls = layout_ui_factory._build_grid_layout_controls(
            mock_layout_controller, parent_widget
        )
        assert isinstance(controls, QWidget)

        # Check QLineEdits are empty
        rows_edit = controls.findChild(QLineEdit, "rows_edit")
        assert rows_edit is not None and rows_edit.text() == ""
        cols_edit = controls.findChild(QLineEdit, "cols_edit")
        assert cols_edit is not None and cols_edit.text() == ""
        margin_top_edit = controls.findChild(QLineEdit, "margin_top_edit")
        assert margin_top_edit is not None and margin_top_edit.text() == ""
        hspace_edit = controls.findChild(QLineEdit, "hspace_edit")
        assert hspace_edit is not None and hspace_edit.text() == ""

        # Check buttons are present and correctly connected
        infer_btn = controls.findChild(QPushButton, "btn_infer_grid")
        assert infer_btn is not None
        assert infer_btn.text() == "Infer Grid"
        infer_btn.clicked.emit()
        mock_layout_manager.infer_grid_parameters.assert_called_once()

    def test_build_grid_layout_controls_with_active_config(
        self, layout_ui_factory, mock_layout_controller, mock_layout_manager
    ):
        """
        Test that _build_grid_layout_controls initializes QLineEdits with values
        from a valid _last_grid_config in LayoutManager.
        """
        active_grid_config = GridConfig(
            rows=3,
            cols=4,
            row_ratios=[1.0] * 3,
            col_ratios=[1.0] * 4,
            margins=Margins(top=0.1, bottom=0.2, left=0.3, right=0.4),
            gutters=Gutters(hspace=[0.05], wspace=[0.15]),
        )
        mock_layout_manager._last_grid_config = (
            active_grid_config  # Set an active config
        )
        parent_widget = QWidget()
        controls = layout_ui_factory._build_grid_layout_controls(
            mock_layout_controller, parent_widget
        )

        # Check QLineEdits are populated
        rows_edit = controls.findChild(QLineEdit, "rows_edit")
        assert rows_edit is not None and rows_edit.text() == "3"
        cols_edit = controls.findChild(QLineEdit, "cols_edit")
        assert cols_edit is not None and cols_edit.text() == "4"
        margin_top_edit = controls.findChild(QLineEdit, "margin_top_edit")
        assert margin_top_edit is not None and margin_top_edit.text() == "0.1"
        hspace_edit = controls.findChild(QLineEdit, "hspace_edit")
        assert hspace_edit is not None and hspace_edit.text() == "0.05"

    def test_handle_line_edit_change_valid_input(
        self, layout_ui_factory, mock_layout_controller, mock_layout_manager, qtbot
    ):
        """
        Test _handle_line_edit_change processes valid input and calls controller.
        """
        # Set up a valid _last_grid_config
        mock_layout_manager._last_grid_config = GridConfig(
            rows=2,
            cols=2,
            row_ratios=[1.0, 1.0],
            col_ratios=[1.0, 1.0],
            margins=Margins(top=0.1, bottom=0.1, left=0.1, right=0.1),
            gutters=Gutters(hspace=[0.05], wspace=[0.05]),
        )

        parent_widget = QWidget()
        rows_edit = layout_ui_factory._create_parameter_line_edit(
            "rows", 2, QIntValidator(1, 99), parent_widget, mock_layout_controller
        )

        # Simulate user input
        rows_edit.setText("3")

        # Manually call the connected slot
        layout_ui_factory._handle_line_edit_change(
            mock_layout_controller, "rows", rows_edit
        )

        mock_layout_controller.on_grid_layout_param_changed.assert_called_once_with(
            "rows", 3
        )

    def test_handle_line_edit_change_invalid_input_restores_value(
        self, layout_ui_factory, mock_layout_controller, mock_layout_manager, qtbot
    ):
        """
        Test _handle_line_edit_change restores the previous valid value on invalid input.
        """
        # Set up a valid _last_grid_config
        mock_layout_manager._last_grid_config = GridConfig(
            rows=2,
            cols=2,
            row_ratios=[1.0, 1.0],
            col_ratios=[1.0, 1.0],
            margins=Margins(top=0.1, bottom=0.1, left=0.1, right=0.1),
            gutters=Gutters(hspace=[0.05], wspace=[0.05]),
        )

        parent_widget = QWidget()
        rows_edit = layout_ui_factory._create_parameter_line_edit(
            "rows", 2, QIntValidator(1, 99), parent_widget, mock_layout_controller
        )

        # Simulate invalid user input
        rows_edit.setText("abc")

        # Manually call the connected slot
        layout_ui_factory._handle_line_edit_change(
            mock_layout_controller, "rows", rows_edit
        )

        # Should restore to original value from _last_grid_config
        assert rows_edit.text() == "2"
        mock_layout_controller.on_grid_layout_param_changed.assert_not_called()

    def test_handle_line_edit_change_invalid_input_no_config_clears(
        self, layout_ui_factory, mock_layout_controller, mock_layout_manager, qtbot
    ):
        """
        Test _handle_line_edit_change clears the QLineEdit on invalid input
        if _last_grid_config is None.
        """
        mock_layout_manager._last_grid_config = None  # No active grid config

        parent_widget = QWidget()
        rows_edit = layout_ui_factory._create_parameter_line_edit(
            "rows", None, QIntValidator(1, 99), parent_widget, mock_layout_controller
        )

        # Simulate invalid user input
        rows_edit.setText("abc")

        # Manually call the connected slot
        layout_ui_factory._handle_line_edit_change(
            mock_layout_controller, "rows", rows_edit
        )

        # Should clear the text as no config to restore from
        assert rows_edit.text() == ""
        mock_layout_controller.on_grid_layout_param_changed.assert_not_called()
