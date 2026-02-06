import logging
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
    QSpinBox,
    QLabel,
)

from src.config_service import ConfigService
from src.controllers.main_controller import MainController
from src.layout_engine import LayoutMode
from src.views.layout_ui_factory import LayoutUIFactory


@pytest.fixture
def mock_config_service():
    """Fixture for a mock ConfigService."""
    config_service = MagicMock(spec=ConfigService)
    # Mock specific icon paths to return dummy SVG paths
    config_service.get.side_effect = lambda key, default=None: {
        "paths.icon_base_dir": "src/assets/icons", # Base directory
        "paths.properties.alignment.align_horizontal_left": "properties/alignment/align_horizontal_left_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_horizontal_center": "properties/alignment/align_horizontal_center_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_horizontal_right": "properties/alignment/align_horizontal_right_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_vertical_top": "properties/alignment/align_vertical_top_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_vertical_center": "properties/alignment/align_vertical_center_24dp_E3E3E3.svg",
        "paths.properties.alignment.align_vertical_bottom": "properties/alignment/align_vertical_bottom_24dp_E3E3E3.svg",
        "paths.properties.distribute.horizontal_distribute": "properties/distribute/horizontal_distribute_24dp_E3E3E3.svg",
        "paths.properties.distribute.vertical_distribute": "properties/distribute/vertical_distribute_24dp_E3E3E3.svg",
        "paths.properties.snap_to_grid": "plots/add_chart_24dp_E3E3E3.svg",
        "layout.default_grid_rows": 2,
        "layout.default_grid_cols": 2,
        "layout.grid_margin": 0.05,
        "layout.grid_gutter": 0.05,
    }.get(key, default)
    return config_service

@pytest.fixture
def mock_main_controller():
    """
    Fixture for a mock MainController.
    """
    controller = MagicMock(spec=MainController)
    controller.align_selected_plots = MagicMock()
    controller.distribute_selected_plots = MagicMock()
    controller.snap_free_plots_to_grid_action = MagicMock()
    controller.apply_grid_layout_from_ui = MagicMock()
    return controller


@pytest.fixture
def layout_ui_factory(mock_config_service):
    """
    Fixture for a LayoutUIFactory instance.
    """
    # Temporarily set the _config_service on the class for testing get_path
    original_config_service = LayoutUIFactory._config_service
    LayoutUIFactory._config_service = mock_config_service
    
    factory = LayoutUIFactory(mock_config_service)
    yield factory
    
    # Restore original _config_service after test
    LayoutUIFactory._config_service = original_config_service


class TestLayoutUIFactory:
    """
    Tests for the LayoutUIFactory class.
    """

    def test_build_layout_controls_free_form_mode_uses_icons(self, layout_ui_factory, mock_main_controller):
        """
        Test that _build_free_form_controls creates buttons with QIcons.
        """
        parent_widget = QWidget()
        free_form_controls = layout_ui_factory._build_free_form_controls(mock_main_controller, parent_widget)
        
        # Check for presence of QPushButtons with icons
        buttons = free_form_controls.findChildren(QPushButton)
        assert len(buttons) > 0 # At least one button should be present

        for button in buttons:
            assert isinstance(button.icon(), QIcon)
            assert not button.icon().isNull() # Check that the icon is not null

    def test_snap_to_grid_button_uses_icon(self, layout_ui_factory, mock_main_controller):
        """
        Test that the "Snap Selected to Grid" button in free-form controls uses a QIcon.
        """
        parent_widget = QWidget()
        free_form_controls = layout_ui_factory._build_free_form_controls(mock_main_controller, parent_widget)
        
        snap_button: QPushButton = None
        for button in free_form_controls.findChildren(QPushButton):
            if button.text() == "Snap Selected to Grid":
                snap_button = button
                break
        
        assert snap_button is not None
        assert isinstance(snap_button.icon(), QIcon)
        assert not snap_button.icon().isNull()

    def test_build_layout_controls_free_form_mode(self, layout_ui_factory, mock_main_controller):
        """
        Test that build_layout_controls builds free form controls when the layout mode is 'free_form'.
        """
        parent_widget = QWidget()
        controls = layout_ui_factory.build_layout_controls(LayoutMode.FREE_FORM, mock_main_controller, parent_widget)
        assert isinstance(controls, QWidget)
        # Further assertions to check for specific free-form related widgets
        # (e.g., check for alignment/distribution buttons)
        buttons = controls.findChildren(QPushButton)
        assert any("Align" in btn.toolTip() for btn in buttons)
        assert any("Distribute" in btn.toolTip() for btn in buttons)

    def test_build_layout_controls_grid_mode(self, layout_ui_factory, mock_main_controller):
        """
        Test that build_layout_controls builds grid layout controls when the layout mode is 'grid'.
        """
        parent_widget = QWidget()
        controls = layout_ui_factory.build_layout_controls(LayoutMode.GRID, mock_main_controller, parent_widget)
        assert isinstance(controls, QWidget)
        # Further assertions to check for specific grid-layout related widgets
        # (e.g., check for QSpinBox for rows/cols)
        spin_boxes = controls.findChildren(QSpinBox)
        assert len(spin_boxes) > 0
        assert any("Rows:" in label.text() for label in controls.findChildren(QLabel))
        assert any("Cols:" in label.text() for label in controls.findChildren(QLabel))


    def test_build_layout_controls_unknown_mode(self, layout_ui_factory, mock_main_controller):
        """
        Test that build_layout_controls handles an unknown layout mode gracefully, returning an empty QWidget.
        """
        parent_widget = QWidget()
        controls = layout_ui_factory.build_layout_controls(layout_mode="unknown_mode", main_controller=mock_main_controller, parent=parent_widget)
        assert isinstance(controls, QWidget)
        assert not controls.children() # Check if it's an empty widget


    def test_build_free_form_controls(self, layout_ui_factory, mock_main_controller):
        """
        Test that _build_free_form_controls creates the expected widgets for free-form layout.
        """
        parent_widget = QWidget()
        controls = layout_ui_factory._build_free_form_controls(mock_main_controller, parent_widget)
        assert isinstance(controls, QWidget)
        buttons = controls.findChildren(QPushButton)
        assert len(buttons) == 9 # 6 alignment + 2 distribution + 1 snap-to-grid button
        assert any(btn.toolTip() == "Align Left" for btn in buttons)
        assert any(btn.toolTip() == "Distribute Horizontally" for btn in buttons)
        assert any(btn.text() == "Snap Selected to Grid" for btn in buttons)
        mock_main_controller.align_selected_plots.assert_not_called()
        mock_main_controller.distribute_selected_plots.assert_not_called()
        mock_main_controller.snap_free_plots_to_grid_action.assert_not_called()


    def test_build_grid_layout_controls(self, layout_ui_factory, mock_main_controller):
        """
        Test that _build_grid_layout_controls creates the expected widgets for grid layout.
        """
        parent_widget = QWidget()
        controls = layout_ui_factory._build_grid_layout_controls(mock_main_controller, parent_widget)
        assert isinstance(controls, QWidget)
        spin_boxes = controls.findChildren(QSpinBox)
        assert len(spin_boxes) == 4 # Rows, Cols, Margin, Gutter
        # The apply button is removed, so we don't assert its presence here
        mock_main_controller.apply_grid_layout_from_ui.assert_not_called()

    @pytest.mark.parametrize("value_type", [QSpinBox, QDoubleSpinBox])
    def test_grid_controls_debounced_connections(self, layout_ui_factory, mock_main_controller, value_type, qtbot):
        """
        Test that QSpinBox/QDoubleSpinBox in grid controls have debounced connections
        to main_controller.update_grid_parameters.
        """
        parent_widget = QWidget()
        controls = layout_ui_factory._build_grid_layout_controls(mock_main_controller, parent_widget)
        
        # Find all relevant spin boxes
        rows_spinbox = controls.findChild(QSpinBox, "grid_rows_spinbox")
        cols_spinbox = controls.findChild(QSpinBox, "grid_cols_spinbox")
        margin_spinbox = controls.findChild(QDoubleSpinBox, "grid_margin_spinbox")
        gutter_spinbox = controls.findChild(QDoubleSpinBox, "grid_gutter_spinbox")

        assert rows_spinbox is not None
        assert cols_spinbox is not None
        assert margin_spinbox is not None
        assert gutter_spinbox is not None

        mock_main_controller.update_grid_parameters.reset_mock()

        # Simulate value change and check if debounced call happens
        rows_spinbox.setValue(3)
        cols_spinbox.setValue(4)
        margin_spinbox.setValue(0.15)
        gutter_spinbox.setValue(0.08)

        # The actual values in the spinboxes are read when update_grid_parameters is called.
        # So we need to ensure the values are what we expect.
        # We need to wait for the debouncer to trigger the call
        # A simple wait should suffice as debouncer delay is small
        qtbot.wait(100) # Wait for debouncer (default delay is 50ms)

        mock_main_controller.update_grid_parameters.assert_called_once_with(
            rows=3, cols=4, margin=0.15, gutter=0.08
        )
    
    def test_build_grid_layout_controls_no_apply_button(self, layout_ui_factory, mock_main_controller):
        """
        Test that the "Apply Grid Layout" button is no longer present in
        _build_grid_layout_controls since live updates are implemented.
        """
        parent_widget = QWidget()
        controls = layout_ui_factory._build_grid_layout_controls(mock_main_controller, parent_widget)
        apply_button = controls.findChild(QPushButton, "apply_grid_layout_button") # Assuming an objectName
        assert apply_button is None
        # Also assert that no QPushButton with the text "Apply Grid Layout" exists
        for button in controls.findChildren(QPushButton):
            assert button.text() != "Apply Grid Layout"