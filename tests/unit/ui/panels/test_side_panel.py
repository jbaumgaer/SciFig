import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QPushButton

from src.ui.panels.side_panel import SidePanel
from src.shared.events import Events


@pytest.fixture
def side_panel(mock_event_aggregator, qtbot):
    """Provides a fresh SidePanel instance initialized with a mock event aggregator."""
    panel = SidePanel(mock_event_aggregator)
    qtbot.addWidget(panel)
    return panel


class TestSidePanel:
    """
    Unit tests for SidePanel.
    Verifies tab management and event-driven tab switching.
    """

    def test_initial_state(self, side_panel):
        """Verifies that the side panel starts empty and as a QTabWidget."""
        assert isinstance(side_panel, QTabWidget)
        assert side_panel.count() == 0
        assert side_panel._tabs == {}

    def test_add_tab_logic(self, side_panel):
        """Verifies that add_tab correctly adds widgets and tracks them in the internal dict."""
        mock_widget = QWidget()
        side_panel.add_tab("test_key", mock_widget, "Test Tab")
        
        assert side_panel.count() == 1
        assert side_panel.tabText(0) == "Test Tab"
        assert side_panel._tabs["test_key"] == mock_widget
        assert side_panel.widget(0) == mock_widget

    def test_duplicate_tab_key_logs_warning(self, side_panel, caplog):
        """Ensures that adding a tab with an existing key is ignored and logged."""
        side_panel.add_tab("key1", QWidget(), "Tab 1")
        
        # Try adding again with same key
        side_panel.add_tab("key1", QWidget(), "Tab 2")
        
        assert side_panel.count() == 1
        assert "already exists" in caplog.text

    def test_property_accessors(self, side_panel):
        """Verifies that the convenience properties return the correct tab instances."""
        prop_tab = QWidget()
        layout_tab = QWidget()
        layers_tab = QWidget()
        
        side_panel.add_tab("properties", prop_tab, "Properties")
        side_panel.add_tab("layout", layout_tab, "Layout")
        side_panel.add_tab("layers", layers_tab, "Layers")
        
        assert side_panel.properties_tab == prop_tab
        assert side_panel.layout_tab == layout_tab
        assert side_panel.layers_tab == layers_tab

    def test_on_switch_tab_event(self, side_panel, mock_event_aggregator):
        """Verifies that the panel switches tabs when the SWITCH_SIDEPANEL_TAB event is published."""
        tab1 = QWidget()
        tab2 = QWidget()
        side_panel.add_tab("tab1", tab1, "Tab 1")
        side_panel.add_tab("tab2", tab2, "Tab 2")
        
        # Start at tab1
        side_panel.setCurrentWidget(tab1)
        assert side_panel.currentWidget() == tab1
        
        # Simulate event publication
        # SidePanel subscribed to this event in __init__
        callback = mock_event_aggregator.subscribe.call_args_list[0][0][1]
        callback("tab2")
        
        assert side_panel.currentWidget() == tab2

    def test_on_switch_tab_invalid_key_logs_warning(self, side_panel, caplog):
        """Ensures that switching to a non-existent tab key is handled gracefully."""
        side_panel.add_tab("tab1", QWidget(), "Tab 1")
        
        side_panel._on_switch_tab("non_existent")
        
        assert "not found" in caplog.text
        # Current tab should not have changed (index 0)
        assert side_panel.currentIndex() == 0

    def test_show_tab_by_name(self, side_panel):
        """Verifies the programmatic switching by name logic."""
        prop_tab = QWidget()
        side_panel.add_tab("properties", prop_tab, "Properties")
        
        # We need to manually set up the property if we aren't using real tab classes
        # But SidePanel uses getattr(self, f"{tab_name...}_tab")
        # In reality, properties_tab is a property returning the dict value.
        
        # Switch to properties
        side_panel.show_tab_by_name("Properties")
        assert side_panel.currentWidget() == prop_tab

    def test_clear_layout_recursively_deletes_widgets(self, side_panel, qtbot):
        """Verifies that _clear_layout recursively cleans up widgets."""
        container = QWidget()
        layout = QVBoxLayout(container)
        child = QPushButton("Test")
        layout.addWidget(child)
        
        side_panel._clear_layout(layout)
        
        # Verify the widget is slated for deletion (or no longer in layout)
        assert layout.count() == 0
