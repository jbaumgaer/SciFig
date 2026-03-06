import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtGui import QIcon, QIntValidator, QValidator
from PySide6.QtWidgets import QWidget, QPushButton, QLineEdit

from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.shared.constants import LayoutMode, IconPath
from src.shared.events import Events
from src.models.layout.layout_config import GridConfig, Margins, Gutters

@pytest.fixture
def factory(mock_layout_manager, mock_event_aggregator, mock_config_service):
    """Provides a LayoutUIFactory instance and sets up IconPath."""
    # Setup mock_layout_manager for factory requirements
    mock_layout_manager.ui_selected_layout_mode = LayoutMode.FREE_FORM

    sample_config = GridConfig(
        rows=2, cols=2,
        row_ratios=[1.0, 1.0],
        col_ratios=[1.0, 1.0],
        margins=Margins(top=0.1, bottom=0.1, left=0.1, right=0.1),
        gutters=Gutters(hspace=[0.05], wspace=[0.05])
    )
    mock_layout_manager.get_last_grid_config.return_value = sample_config

    # Ensure IconPath is initialized for the tests
    IconPath.set_config_service(mock_config_service)

    return LayoutUIFactory(mock_layout_manager, mock_event_aggregator)



class TestLayoutUIFactory:
    """
    Unit tests for LayoutUIFactory.
    Verifies that UI components are correctly built and hooked into the EventAggregator.
    """

    def test_build_layout_controls_free_form(self, factory, mock_layout_manager, qtbot):
        """Verifies controls built for Free Form layout mode."""
        mock_layout_manager.ui_selected_layout_mode = LayoutMode.FREE_FORM
        
        parent = QWidget()
        container = factory.build_layout_controls(MagicMock(), parent)
        
        # Verify alignment buttons exist
        btn_left = container.findChild(QPushButton, "btn_align_left")
        assert btn_left is not None
        assert btn_left.toolTip() == "Align Left"
        
        # Trigger button and verify event publication
        btn_left.click()
        factory._event_aggregator.publish.assert_called_with(
            Events.ALIGN_PLOTS_REQUESTED, edge="left"
        )

    def test_build_layout_controls_grid(self, factory, mock_layout_manager, qtbot):
        """Verifies controls built for Grid layout mode."""
        mock_layout_manager.ui_selected_layout_mode = LayoutMode.GRID
        
        parent = QWidget()
        container = factory.build_layout_controls(MagicMock(), parent)
        
        # Verify grid-specific LineEdits exist
        rows_edit = container.findChild(QLineEdit, "rows_edit")
        assert rows_edit is not None
        assert rows_edit.text() == "2" # From sample_config fixture
        
        # Verify Infer Grid button
        buttons = container.findChildren(QPushButton)
        assert any(btn.text() == "Infer Grid" for btn in buttons)

    def test_handle_line_edit_change_valid_numeric(self, factory, mock_layout_manager):
        """Tests that valid numeric input publishes a parameter change request."""
        line_edit = QLineEdit()
        line_edit.setText("5")
        # Add a validator to simulate rows/cols behavior
        line_edit.setValidator(QIntValidator(1, 99))
        
        factory._handle_line_edit_change("rows", line_edit)
        
        factory._event_aggregator.publish.assert_called_with(
            Events.CHANGE_GRID_PARAMETER_REQUESTED,
            param_name="rows",
            value=5.0 # float(5)
        )

    def test_handle_line_edit_change_invalid_restores_old_value(self, factory, mock_layout_manager):
        """Tests that invalid input triggers a restore from the last config."""
        line_edit = QLineEdit()
        line_edit.setText("abc")
        line_edit.setValidator(QIntValidator(1, 99))
        
        factory._handle_line_edit_change("rows", line_edit)
        
        # Should NOT publish
        factory._event_aggregator.publish.assert_not_called()
        # Should restore text to "2" (from mock_layout_manager sample_config)
        assert line_edit.text() == "2"

    def test_handle_line_edit_change_list_param(self, factory, mock_layout_manager):
        """Tests handling of CSV-style list parameters (hspace/wspace)."""
        line_edit = QLineEdit()
        line_edit.setText("0.1, 0.2")
        # No validator for these usually in the code
        
        factory._handle_line_edit_change("hspace", line_edit)
        
        # Current implementation passes the raw string for further processing
        factory._event_aggregator.publish.assert_called_with(
            Events.CHANGE_GRID_PARAMETER_REQUESTED,
            param_name="hspace",
            value="0.1, 0.2"
        )

    def test_infer_grid_button_publishes_event(self, factory, mock_layout_manager, qtbot):
        """Verifies that the Infer Grid button publishes the correct request."""
        mock_layout_manager.ui_selected_layout_mode = LayoutMode.GRID
        parent = QWidget()
        container = factory._build_grid_layout_controls(parent)
        
        # Find the button by text
        buttons = container.findChildren(QPushButton)
        infer_btn = next(btn for btn in buttons if btn.text() == "Infer Grid")
        
        infer_btn.click()
        factory._event_aggregator.publish.assert_called_with(
            Events.INFER_GRID_PARAMETERS_REQUESTED
        )

    def test_optimize_layout_button_publishes_event(self, factory, mock_layout_manager, qtbot):
        """Verifies that the Optimize Layout button publishes the correct request."""
        mock_layout_manager.ui_selected_layout_mode = LayoutMode.GRID
        parent = QWidget()
        container = factory._build_grid_layout_controls(parent)
        
        buttons = container.findChildren(QPushButton)
        opt_btn = next(btn for btn in buttons if btn.text() == "Optimize Layout")
        
        opt_btn.click()
        factory._event_aggregator.publish.assert_called_with(
            Events.OPTIMIZE_LAYOUT_REQUESTED
        )
