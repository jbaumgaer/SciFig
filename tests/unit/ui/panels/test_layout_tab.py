import logging

import pytest
from PySide6.QtCore import Signal, Qt # Import Qt for LeftButton
from PySide6.QtWidgets import QStackedWidget, QToolButton, QVBoxLayout, QWidget

from src.shared.constants import LayoutMode
from src.ui.panels.layout_tab import LayoutTab


class TestLayoutTab:
    """Test suite for the LayoutTab widget."""

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mock_application_model, mock_layout_controller, mock_layout_ui_factory, caplog):
        """
        Setup the test environment for each test case.
        This runs automatically for each test method in this class.
        """
        self.mock_model = mock_application_model
        self.mock_layout_controller = mock_layout_controller
        self.mock_layout_ui_factory = mock_layout_ui_factory

        # --- Fix 1: Configure logging for caplog ---
        logging.getLogger(LayoutTab.__module__).setLevel(logging.DEBUG)
        caplog.set_level(logging.DEBUG) # Also set caplog's own level to capture debug messages

        # --- Arrange ---
        # Default mock configuration for most tests
        self.mock_layout_controller.get_ui_selected_layout_mode.return_value = LayoutMode.FREE_FORM

        # Mock the factory to return distinct, identifiable QWidget instances
        self.free_form_controls = QWidget()
        self.free_form_controls.setObjectName("FreeFormControls")
        self.grid_controls = QWidget()
        self.grid_controls.setObjectName("GridControls")

        # Set the initial return value for the factory's build method
        self.mock_layout_ui_factory.build_layout_controls.return_value = self.free_form_controls

        # Create the widget that will be tested
        self.layout_tab = LayoutTab(
            model=self.mock_model,
            layout_controller=self.mock_layout_controller,
            layout_ui_factory=self.mock_layout_ui_factory
        )
        qtbot.addWidget(self.layout_tab)

    def test_layout_tab_initialization_in_free_form_mode(self, caplog):
        """Test the initial state of the LayoutTab when starting in FREE_FORM mode."""
        # --- Assert ---
        assert isinstance(self.layout_tab.layout(), QVBoxLayout)
        assert any("LayoutTab initialized." in r.message for r in caplog.records)

        # Find UI elements without accessing private attributes
        toggle_button = self.layout_tab.findChild(QToolButton)
        stack = self.layout_tab.findChild(QStackedWidget)

        # Verify toggle button is set up correctly for the initial FREE_FORM mode
        assert toggle_button is not None
        assert not toggle_button.isChecked()
        assert "Switch to Grid Layout Controls" in toggle_button.text()

        # Verify the factory was called to build the initial controls
        self.mock_layout_ui_factory.build_layout_controls.assert_called_once_with(
            self.mock_layout_controller,
            stack  # Check that the parent is the stacked widget
        )

        # Verify the initial widget is correctly added and displayed
        assert stack.count() == 1
        assert stack.currentWidget() == self.free_form_controls

    def test_toggle_button_switches_to_grid_mode(self, qtbot):
        """Test that clicking the toggle button calls the controller to switch to GRID mode."""
        # --- Arrange ---
        toggle_button = self.layout_tab.findChild(QToolButton)

        # --- Act ---
        # Use qtbot to simulate a real user click
        qtbot.mouseClick(toggle_button, Qt.LeftButton)

        # --- Assert ---
        # Verify the controller's method was called with the correct state (checked = True)
        self.mock_layout_controller.toggle_layout_mode.assert_called_once_with(True)

    def test_toggle_button_switches_to_free_form_mode(self, qtbot):
        """Test that un-checking the toggle button calls the controller to switch to FREE_FORM mode."""
        # --- Arrange ---
        toggle_button = self.layout_tab.findChild(QToolButton)
        toggle_button.setChecked(True)  # Start in GRID mode
        self.mock_layout_controller.reset_mock()  # Reset mock after setup arrangement

        # --- Act ---
        qtbot.mouseClick(toggle_button, Qt.LeftButton)  # This will un-check the button

        # --- Assert ---
        self.mock_layout_controller.toggle_layout_mode.assert_called_once_with(False)

    def test_update_content_on_ui_layout_mode_changed_to_grid(self, caplog):
        """Test that the UI content is rebuilt when the layout mode changes to GRID via signal."""
        # --- Arrange ---
        caplog.set_level(logging.DEBUG)
        stack = self.layout_tab.findChild(QStackedWidget)
        self.mock_layout_ui_factory.reset_mock()
        self.mock_layout_ui_factory.build_layout_controls.return_value = self.grid_controls

        # --- Act ---
        # Emit the signal from the mocked layout manager
        self.mock_layout_controller._layout_manager.uiLayoutModeChanged.emit(LayoutMode.GRID)

        # --- Assert ---
        assert any("Updating content for UI layout mode: grid" in r.message for r in caplog.records)

        # Verify that the factory was called to build the new controls
        self.mock_layout_ui_factory.build_layout_controls.assert_called_once()

        # Verify that the stack was cleared and the new widget is the only one present
        assert stack.count() == 1
        assert stack.currentWidget() == self.grid_controls
        assert stack.currentWidget().objectName() == "GridControls"

    def test_update_toggle_button_text_on_mode_change(self, qtbot): # Add qtbot for wait_for_signals
        """Test that the toggle button's text updates correctly when the layout mode changes."""
        # --- Arrange ---
        toggle_button = self.layout_tab.findChild(QToolButton)

        # --- Act & Assert for GRID ---
        self.mock_layout_controller._layout_manager.uiLayoutModeChanged.emit(LayoutMode.GRID)
        qtbot.wait_signals([self.mock_layout_controller._layout_manager.uiLayoutModeChanged])
        assert "Switch to Free-Form Layout Controls" in toggle_button.text() # Now offers to switch TO free-form

        # --- Act & Assert for FREE_FORM ---
        self.mock_layout_controller._layout_manager.uiLayoutModeChanged.emit(LayoutMode.FREE_FORM)
        qtbot.wait_signals([self.mock_layout_controller._layout_manager.uiLayoutModeChanged])
        assert "Switch to Grid Layout Controls" in toggle_button.text() # Now offers to switch TO grid

    def test_update_content_on_grid_config_parameters_changed(self, qtbot): # Add qtbot for wait_for_signals
        """Test that grid controls are rebuilt when grid config parameters change."""
        # --- Arrange ---
        # Ensure we are in GRID mode to start
        self.layout_tab._update_content(LayoutMode.GRID)
        self.mock_layout_ui_factory.reset_mock()

        # --- Act ---
        self.mock_layout_controller._layout_manager.gridConfigParametersChanged.emit()
        # --- Fix 4: Wait for signal to be processed ---
        qtbot.wait_signals([self.mock_layout_controller._layout_manager.gridConfigParametersChanged])

        # --- Assert ---
        # Verify the factory was called again to rebuild the controls,
        # indicating the UI has refreshed.
        self.mock_layout_ui_factory.build_layout_controls.assert_called_once_with(
            self.mock_layout_controller,
            self.layout_tab.findChild(QStackedWidget)
        )

    def test_clear_stacked_widget_removes_all_widgets(self):
        """Test the private helper method _clear_stacked_widget to ensure no memory leaks."""
        # --- Arrange ---
        stack = self.layout_tab.findChild(QStackedWidget)
        # Manually add some dummy widgets to the stack
        stack.addWidget(QWidget())
        stack.addWidget(QWidget())
        assert stack.count() == 3  # The initial one plus the two dummies

        # --- Act ---
        # Call the private method we want to test
        self.layout_tab._clear_stacked_widget(stack)

        # --- Assert ---
        assert stack.count() == 0
