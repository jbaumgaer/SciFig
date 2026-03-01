
import pytest
from PySide6.QtWidgets import QApplication, QTabWidget
from pytest_mock import mocker

from src.controllers.layout_controller import LayoutController
from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.services.config_service import ConfigService
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.plot_properties_ui_factory import PlotPropertiesUIFactory
from src.ui.panels.layers_tab import LayersTab
from src.ui.panels.layout_tab import LayoutTab
from src.ui.panels.properties_tab import PropertiesTab
from src.ui.panels.side_panel import SidePanel


@pytest.fixture
def mock_app(qtbot):
    """Fixture to ensure QApplication exists."""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app
    # No need to quit app here if it's reused by qtbot

@pytest.fixture
def mock_dependencies(mocker, mock_app):
    """Mocks common dependencies for SidePanel."""
    model = mocker.Mock(spec=ApplicationModel)
    model.selectionChanged = mocker.Mock()
    model.selection = [] # Default empty selection

    node_controller = mocker.Mock(spec=NodeController)
    layout_controller = mocker.Mock(spec=LayoutController)
    plot_properties_ui_factory = mocker.Mock(spec=PlotPropertiesUIFactory)
    layout_ui_factory = mocker.Mock(spec=LayoutUIFactory)
    project_controller = mocker.Mock(spec=ProjectController)
    config_service = mocker.Mock(spec=ConfigService)

    # Mock tab instantiations to ensure SidePanel doesn't create real widgets prematurely
    mocker.patch('src.ui.panels.properties_tab.PropertiesTab', autospec=True)
    mocker.patch('src.ui.panels.layout_tab.LayoutTab', autospec=True)
    mocker.patch('src.ui.panels.layers_tab.LayersTab', autospec=True)

    # Return mocked instances that SidePanel expects to construct
    mock_properties_tab_instance = mocker.Mock(spec=PropertiesTab)
    mock_layout_tab_instance = mocker.Mock(spec=LayoutTab)
    mock_layers_tab_instance = mocker.Mock(spec=LayersTab)

    mock_properties_tab_instance.return_value = mock_properties_tab_instance
    mock_layout_tab_instance.return_value = mock_layout_tab_instance
    mock_layers_tab_instance.return_value = mock_layers_tab_instance

    return model, node_controller, layout_controller, plot_properties_ui_factory, \
        layout_ui_factory, project_controller, config_service, \
        mock_properties_tab_instance, mock_layout_tab_instance, mock_layers_tab_instance

@pytest.fixture
def side_panel(qtbot, mock_dependencies):
    """Fixture to create a SidePanel instance."""
    model, node_controller, layout_controller, plot_properties_ui_factory, \
    layout_ui_factory, project_controller, config_service, \
    mock_properties_tab_instance, mock_layout_tab_instance, mock_layers_tab_instance = mock_dependencies

    # Create the panel with actual tab instances instead of mocks
    panel = SidePanel(
        model=model,
        node_controller=node_controller,
        layout_controller=layout_controller,
        plot_properties_ui_factory=plot_properties_ui_factory,
        layout_ui_factory=layout_ui_factory,
        project_controller=project_controller,
        config_service=config_service
    )

    # Manually assign mocked tab instances to the panel for verification,
    # as the SidePanel __init__ will have called the patched constructors.
    panel.properties_tab = mock_properties_tab_instance
    panel.layout_tab = mock_layout_tab_instance
    panel.layers_tab = mock_layers_tab_instance

    qtbot.addWidget(panel)
    return panel, model, node_controller, layout_controller, plot_properties_ui_factory, \
           layout_ui_factory, project_controller, config_service

class TestSidePanel:

    def test_initialization_of_tabs_and_qtabwidget(self, side_panel, mock_dependencies, mocker):
        """
        Verify that SidePanel initializes as a QTabWidget and correctly creates
        and adds its constituent tabs (PropertiesTab, LayoutTab, LayersTab).
        """
        panel, model, nc, lc, ppuf, luf, pc, cs = side_panel
        mp_tab_instance, ml_tab_instance, ml_tab_instance = mock_dependencies[7:] # Unpack the mocked tab instances

        assert isinstance(panel, QTabWidget)
        assert panel.count() == 3

        # Verify correct types of tabs are added by checking the return values of the mocked constructors
        mp_tab_instance.assert_called_once_with(
            model=model, node_controller=nc, plot_properties_ui_factory=ppuf,
            project_controller=pc, config_service=cs, parent=panel
        )
        ml_tab_instance.assert_called_once_with(
            model=model, layout_controller=lc, layout_ui_factory=luf, parent=panel
        )
        ml_tab_instance.assert_called_once_with(
            model=model, node_controller=nc, config_service=cs, parent=panel
        )

        assert panel.tabText(panel.indexOf(panel.properties_tab)) == "Properties"
        assert panel.tabText(panel.indexOf(panel.layout_tab)) == "Layout"
        assert panel.tabText(panel.indexOf(panel.layers_tab)) == "Layers"

        # Verify initial tab is PropertiesTab (default by SidePanel implementation)
        assert panel.currentWidget() == panel.properties_tab

    def test_tab_switching_by_name(self, side_panel, qtbot):
        """
        Verify that the show_tab_by_name method correctly switches the active tab.
        """
        panel, _, _, _, _, _, _, _ = side_panel

        panel.show_tab_by_name("Layout")
        assert panel.currentWidget() == panel.layout_tab

        panel.show_tab_by_name("Layers")
        assert panel.currentWidget() == panel.layers_tab

        panel.show_tab_by_name("Properties")
        assert panel.currentWidget() == panel.properties_tab

        # Test with invalid tab name, ensuring it logs a warning and current tab doesn't change
        with mocker.patch.object(panel.logger, 'warning') as mock_warning:
            panel.show_tab_by_name("NonExistentTab")
            mock_warning.assert_called_once_with("SidePanel: Tab 'NonExistentTab' not found.")
        assert panel.currentWidget() == panel.properties_tab # Should not change

    def test_on_selection_changed_switches_to_properties_tab_for_plotnode(self, side_panel, mocker):
        """
        Verify that when a single PlotNode is selected, the SidePanel automatically
        switches to the 'Properties' tab.
        """
        panel, model, _, _, _, _, _, _ = side_panel

        # Start on a different tab to ensure a switch occurs
        panel.setCurrentWidget(panel.layers_tab)

        mock_plot_node = mocker.Mock(spec=PlotNode)
        model.selection = [mock_plot_node]

        # Call the private method directly as we're testing its logic upon signal emission
        panel._on_selection_changed()

        assert panel.currentWidget() == panel.properties_tab
        # model.selectionChanged.assert_called_once() # This will be called from outside the panel

    def test_on_selection_changed_does_not_switch_for_non_plotnode(self, side_panel, mocker):
        """
        Verify that when a single non-PlotNode (e.g., SceneNode) is selected,
        the SidePanel does NOT automatically switch to the 'Properties' tab.
        """
        panel, model, _, _, _, _, _, _ = side_panel
        panel.setCurrentWidget(panel.layers_tab) # Start on a different tab

        mock_scene_node = mocker.Mock(spec=SceneNode)
        model.selection = [mock_scene_node]

        panel._on_selection_changed()

        assert panel.currentWidget() == panel.layers_tab # Should remain on Layers tab

    def test_on_selection_changed_does_not_switch_for_multiple_selection(self, side_panel, mocker):
        """
        Verify that when multiple nodes are selected (even if they include PlotNodes),
        the SidePanel does NOT automatically switch to the 'Properties' tab.
        """
        panel, model, _, _, _, _, _, _ = side_panel
        panel.setCurrentWidget(panel.layers_tab) # Start on a different tab

        mock_plot_node1 = mocker.Mock(spec=PlotNode)
        mock_plot_node2 = mocker.Mock(spec=PlotNode)
        model.selection = [mock_plot_node1, mock_plot_node2]

        panel._on_selection_changed()

        assert panel.currentWidget() == panel.layers_tab # Should remain on Layers tab
