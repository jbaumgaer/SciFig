import pytest
from unittest.mock import MagicMock, ANY
from pathlib import Path
from PySide6.QtWidgets import QMenuBar, QToolBar, QWidget
from qframelesswindow import StandardTitleBar

from src.ui.windows.main_window import MainWindow
from src.ui.widgets.ribbon_bar import RibbonBar
from src.ui.panels.side_panel import SidePanel
from src.ui.builders.menu_bar_builder import MainMenuActions
from src.ui.builders.ribbon_bar_builder import RibbonActions
from src.ui.builders.tool_bar_builder import ToolBarActions
from src.shared.events import Events


@pytest.fixture
def main_window(qtbot, mock_event_aggregator):
    """Provides a fresh MainWindow instance with mocked dependencies."""
    
    # Mock all required components
    mock_menu_bar = QMenuBar()
    mock_menu_actions = MagicMock(spec=MainMenuActions)
    # Ensure tab actions exist for ribbon switching
    mock_menu_actions.insert_tab_action = MagicMock()
    mock_menu_actions.design_tab_action = MagicMock()
    mock_menu_actions.layout_tab_action = MagicMock()
    
    # Use real RibbonBar (but mock its actions)
    mock_ribbon = RibbonBar() 
    # Add dummy tabs so currentIndex isn't -1
    mock_ribbon.add_ribbon_tab("Insert")
    mock_ribbon.add_ribbon_tab("Design")
    mock_ribbon.add_ribbon_tab("Layout")
    
    mock_ribbon_actions = MagicMock(spec=RibbonActions)
    
    mock_toolbar = QToolBar()
    mock_toolbar_actions = MagicMock(spec=ToolBarActions)
    
    # Use a real QWidget to satisfy QDockWidget.setWidget type requirements
    mock_side_panel = QWidget()
    
    window = MainWindow(
        menu_bar=mock_menu_bar,
        main_menu_actions=mock_menu_actions,
        ribbon_bar=mock_ribbon,
        ribbon_actions=mock_ribbon_actions,
        tool_bar=mock_toolbar,
        tool_bar_actions=mock_toolbar_actions,
        side_panel=mock_side_panel,
        event_aggregator=mock_event_aggregator
    )
    
    qtbot.addWidget(window)
    return window


class TestMainWindow:
    """Unit tests for MainWindow."""

    def test_initialization(self, main_window):
        """Verifies that the window initializes with correct basic state."""
        assert main_window.windowTitle() == "SciFig"
        assert isinstance(main_window.titleBar, StandardTitleBar)
        assert main_window.side_panel_view is not None
        assert main_window.side_panel_dock is not None

    def test_event_subscriptions(self, mock_event_aggregator):
        """Verifies that MainWindow subscribes to expected UI service events."""
        # Reset mock to capture only subscriptions in __init__
        mock_event_aggregator.subscribe.reset_mock()
        
        # We need a new window to check __init__ subscriptions
        mock_menu_bar = QMenuBar()
        mock_menu_actions = MagicMock(spec=MainMenuActions)
        mock_menu_actions.insert_tab_action = MagicMock()
        mock_menu_actions.design_tab_action = MagicMock()
        mock_menu_actions.layout_tab_action = MagicMock()
        
        # Use real RibbonBar and QWidget to satisfy type requirements
        MainWindow(
            mock_menu_bar, mock_menu_actions, RibbonBar(), MagicMock(),
            QToolBar(), MagicMock(), QWidget(), mock_event_aggregator
        )
        
        expected_events = [
            Events.SHOW_ADD_PLOT_DIALOG_REQUESTED,
            Events.PROMPT_FOR_OPEN_PATH_REQUESTED,
            Events.PROMPT_FOR_SAVE_AS_PATH_REQUESTED,
            Events.PROMPT_FOR_TEMPLATE_SELECTION_REQUESTED,
            Events.PROMPT_FOR_OPEN_PATH_FOR_NODE_DATA_REQUESTED,
            Events.WINDOW_TITLE_DATA_READY
        ]
        
        for event in expected_events:
            mock_event_aggregator.subscribe.assert_any_call(event, ANY)

    def test_set_canvas_widget(self, main_window):
        """Verifies that the canvas widget is correctly added to the layout."""
        mock_canvas = QWidget()
        main_window.set_canvas_widget(mock_canvas)
        
        assert main_window.canvas_widget is mock_canvas
        # Check if it was added to the layout
        # (Simplified check: verify the internal pointer)
        assert mock_canvas.parent() is not None

    def test_window_title_update(self, main_window):
        """Verifies that the window title updates correctly."""
        main_window._on_window_title_data_ready("New Title[*]", True)
        
        assert main_window.windowTitle() == "New Title[*]"
        assert main_window.isWindowModified() is True

    def test_ribbon_switching_logic(self, main_window):
        """Verifies that menu actions correctly trigger ribbon tab switching."""
        # Insert Tab (0)
        main_window.main_menu_actions.insert_tab_action.triggered.emit()
        assert main_window.ribbon_bar.currentIndex() == 0
        
        # Design Tab (1)
        main_window.main_menu_actions.design_tab_action.triggered.emit()
        assert main_window.ribbon_bar.currentIndex() == 1
        
        # Layout Tab (2)
        main_window.main_menu_actions.layout_tab_action.triggered.emit()
        assert main_window.ribbon_bar.currentIndex() == 2
