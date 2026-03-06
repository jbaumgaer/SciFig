import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QTabWidget, QScrollArea

from src.ui.builders.ribbon_bar_builder import RibbonBarBuilder, RibbonActions
from src.ui.widgets.ribbon_bar import RibbonBar


@pytest.fixture
def mock_icon_path():
    """Mock IconPath to avoid file system access and return dummy strings."""
    with patch("src.ui.builders.ribbon_bar_builder.IconPath") as mock:
        mock.get_path.side_effect = lambda key: f"path/to/{key}.svg"
        yield mock


@pytest.fixture
def ribbon_builder(mock_event_aggregator, mock_icon_path):
    """Provides a RibbonBarBuilder instance."""
    return RibbonBarBuilder(mock_event_aggregator)


class TestRibbonBarBuilder:
    """
    Unit tests for RibbonBarBuilder.
    Verifies the construction of the ribbon UI and the population of the actions container.
    """

    def test_build_returns_ribbon_and_actions(self, ribbon_builder, qtbot):
        """Verifies that build() returns the expected types and populated containers."""
        ribbon, actions = ribbon_builder.build()
        
        assert isinstance(ribbon, RibbonBar)
        assert isinstance(actions, RibbonActions)
        
        # Verify all dataclass fields are populated with QAction objects
        for field_name in RibbonActions.__annotations__.keys():
            val = getattr(actions, field_name)
            assert isinstance(val, QAction), f"Field {field_name} is not a QAction"
            assert val.text() != "" # Ensure it has text

    def test_build_creates_expected_tabs(self, ribbon_builder, qtbot):
        """Verifies that the three main tabs are created."""
        ribbon, _ = ribbon_builder.build()
        
        # RibbonBar inherits from QTabWidget
        tab_widget = ribbon
        tab_texts = [tab_widget.tabText(i) for i in range(tab_widget.count())]
        
        assert "Insert" in tab_texts
        assert "Design" in tab_texts
        assert "Layout" in tab_texts

    def test_action_creation_with_icons(self, ribbon_builder, mock_icon_path, qtbot):
        """Verifies that actions are created with text and associated icons."""
        _, actions = ribbon_builder.build()
        
        # Check a few specific actions
        assert actions.insert_line_action.text() == "Line"
        assert actions.design_nature_action.text() == "Nature"
        assert actions.layout_margins_action.text() == "Margins"
        
        # Verify mock_icon_path was called for key actions
        mock_icon_path.get_path.assert_any_call("ribbon.insert.plots.line")
        mock_icon_path.get_path.assert_any_call("ribbon.design.nature")

    def test_insert_tab_groups_structure(self, ribbon_builder, qtbot):
        """Verifies the grouping of actions within the 'Insert' tab."""
        ribbon, _ = ribbon_builder.build()
        
        # Get the scroll area for the first tab
        scroll_area = ribbon.widget(0)
        assert isinstance(scroll_area, QScrollArea)
        
        # Get the page widget inside the scroll area
        page_widget = scroll_area.widget()
        assert page_widget is not None
        
        layout = page_widget.layout()
        assert layout is not None
        
        # The layout contains RibbonGroup widgets and their separator lines
        # Total items should be 2 * number of groups (group + separator)
        # Should have at least Plots, Shapes, Text, Arrows, Symbols (5 groups -> 10 items)
        assert layout.count() >= 10

    def test_layout_tab_arrange_actions(self, ribbon_builder, qtbot):
        """Verifies specific actions in the Layout -> Arrange group."""
        _, actions = ribbon_builder.build()
        
        assert actions.layout_align_left_action.text() == "Align Left"
        assert actions.layout_distribute_h_action.text() == "Dist. H"
        assert actions.layout_grid_toggle_action.text() == "Grid"
