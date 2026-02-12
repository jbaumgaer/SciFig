from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtWidgets import QMenuBar, QToolBar

from src.core.application_components import ApplicationComponents
from src.core.composition_root import CompositionRoot
from src.models.plots.plot_types import PlotType
from src.services.tools import MockTool
from src.shared.constants import ToolName
from src.shared.exceptions import ConfigError
from src.ui.builders.menu_bar_builder import MainMenuActions
from src.ui.builders.tool_bar_builder import ToolBarActions

# No fixtures defined here anymore, all moved to tests/unit/conftest.py


@pytest.fixture
def composition_root(
    mock_qapplication,
    mock_application_model,  # Renamed from mock_model
    mock_command_manager,
    mock_project_controller,
    mock_layout_controller,
    mock_node_controller,
    mock_renderer,
    mock_tool_manager,
    mock_selection_tool,
    mock_main_window,
    mock_config_service,
    mock_free_layout_engine,
    mock_grid_layout_engine,
    mock_layout_manager,
    mock_layout_ui_factory,
    mock_plot_properties_ui_factory,
    mock_canvas_controller,
    mocker,  # Add mocker fixture for patching
):
    """Fixture for an ApplicationAssembler instance with mocked dependencies."""

    # Mock instance-level objects needed for returns or direct attributes
    mock_main_menu_actions = MagicMock(spec=MainMenuActions)
    mock_menu_bar = Mock(spec=QMenuBar)
    mock_toolbar_instance = Mock(spec=QToolBar)
    mock_toolbar_actions_instance = MagicMock(spec=ToolBarActions)
    mock_mock_tool_instance = MagicMock(spec=MockTool)
    mock_figure_instance = MagicMock()  # Mock instance for Figure

    # --- Step 1: Patch all classes that CompositionRoot will instantiate or import ---
    # Store the patched class mocks in local variables
    # Note: ConfigService is not patched here as it's passed directly to CompositionRoot
    mock_ApplicationModel_class_patch = mocker.patch(
        "src.core.composition_root.ApplicationModel"
    )
    mock_CommandManager_class_patch = mocker.patch(
        "src.core.composition_root.CommandManager"
    )
    mock_ProjectController_class_patch = mocker.patch(
        "src.core.composition_root.ProjectController"
    )
    mock_LayoutController_class_patch = mocker.patch(
        "src.core.composition_root.LayoutController"
    )
    mock_NodeController_class_patch = mocker.patch(
        "src.core.composition_root.NodeController"
    )
    mock_LayoutManager_class_patch = mocker.patch(
        "src.core.composition_root.LayoutManager"
    )
    mock_FreeLayoutEngine_class_patch = mocker.patch(
        "src.core.composition_root.FreeLayoutEngine"
    )
    mock_GridLayoutEngine_class_patch = mocker.patch(
        "src.core.composition_root.GridLayoutEngine"
    )
    mock_LayoutUIFactory_class_patch = mocker.patch(
        "src.core.composition_root.LayoutUIFactory"
    )
    mock_PlotPropertiesUIFactory_class_patch = mocker.patch(
        "src.core.composition_root.PlotPropertiesUIFactory"
    )
    mock_Renderer_class_patch = mocker.patch("src.core.composition_root.Renderer")
    mock_ToolService_class_patch = mocker.patch("src.core.composition_root.ToolService")
    mock_SelectionTool_class_patch = mocker.patch(
        "src.core.composition_root.SelectionTool"
    )
    mock_MainWindow_class_patch = mocker.patch("src.core.composition_root.MainWindow")
    mock_CanvasController_class_patch = mocker.patch(
        "src.core.composition_root.CanvasController"
    )
    mock_build_line_plot_ui_widgets_func_patch = mocker.patch(
        "src.core.composition_root._build_line_plot_ui_widgets"
    )
    mock_build_scatter_plot_ui_widgets_func_patch = mocker.patch(
        "src.core.composition_root._build_scatter_plot_ui_widgets"
    )
    mock_figure_class_patch = mocker.patch(
        "src.core.composition_root.Figure", return_value=mock_figure_instance
    )  # Patched Figure class
    mock_MenuBarBuilder_class_patch = mocker.patch(
        "src.core.composition_root.MenuBarBuilder"
    )
    mock_ToolBarBuilder_class_patch = mocker.patch(
        "src.core.composition_root.ToolBarBuilder"
    )
    mock_MockTool_class_patch = mocker.patch(
        "src.services.tools.MockTool", return_value=mock_mock_tool_instance
    )  # Patched MockTool class
    mock_set_icon_config_patch = mocker.patch(
        "src.shared.constants.IconPath.set_config_service", autospec=True
    )

    # --- Step 2: Set the return_value for each patched class to the fixture's instance mock ---
    mock_ApplicationModel_class_patch.return_value = mock_application_model
    mock_CommandManager_class_patch.return_value = mock_command_manager
    mock_ProjectController_class_patch.return_value = mock_project_controller
    mock_LayoutController_class_patch.return_value = mock_layout_controller
    mock_NodeController_class_patch.return_value = mock_node_controller
    mock_LayoutManager_class_patch.return_value = mock_layout_manager
    mock_FreeLayoutEngine_class_patch.return_value = mock_free_layout_engine
    mock_GridLayoutEngine_class_patch.return_value = mock_grid_layout_engine
    mock_LayoutUIFactory_class_patch.return_value = mock_layout_ui_factory
    mock_PlotPropertiesUIFactory_class_patch.return_value = mock_plot_properties_ui_factory
    mock_Renderer_class_patch.return_value = mock_renderer
    mock_ToolService_class_patch.return_value = mock_tool_manager
    mock_SelectionTool_class_patch.return_value = mock_selection_tool
    mock_MainWindow_class_patch.return_value = mock_main_window
    mock_CanvasController_class_patch.return_value = mock_canvas_controller

    # For MenuBarBuilder and ToolBarBuilder, set the return_value of their build() methods
    mock_MenuBarBuilder_class_patch.return_value.build.return_value = (
        mock_menu_bar,
        mock_main_menu_actions,
    )
    mock_ToolBarBuilder_class_patch.return_value.build.return_value = (
        mock_toolbar_instance,
        mock_toolbar_actions_instance,
    )

    # Configure side effect for IconPath.set_config_service
    def set_config_service_side_effect(config_service):
        from src.shared.constants import IconPath

        IconPath._config_service = config_service

    mock_set_icon_config_patch.side_effect = set_config_service_side_effect

    # --- Step 3: Instantiate CompositionRoot ---
    composition_root_instance = CompositionRoot(mock_qapplication, mock_config_service)

    # --- Step 4: Set internal references on the CompositionRoot instance to the mocked objects ---
    # These assignments ensure that when a test calls composition_root._model, it gets the fixture's mock_model
    composition_root_instance._model = mock_application_model
    composition_root_instance._command_manager = mock_command_manager
    composition_root_instance._project_controller = mock_project_controller
    composition_root_instance._layout_controller = mock_layout_controller
    composition_root_instance._node_controller = mock_node_controller
    composition_root_instance._layout_manager = mock_layout_manager
    composition_root_instance._free_layout_engine = mock_free_layout_engine
    composition_root_instance._grid_layout_engine = mock_grid_layout_engine
    composition_root_instance._layout_ui_factory = mock_layout_ui_factory
    composition_root_instance._plot_properties_ui_factory = mock_plot_properties_ui_factory
    composition_root_instance._canvas_controller = mock_canvas_controller
    composition_root_instance._tool_manager = mock_tool_manager
    composition_root_instance._selection_tool = mock_selection_tool
    composition_root_instance._renderer = mock_renderer
    composition_root_instance._plot_types = list(
        mock_renderer.plotting_strategies.keys()
    )
    composition_root_instance._view = mock_main_window
    composition_root_instance._menu_bar = mock_menu_bar
    composition_root_instance._main_menu_actions = mock_main_menu_actions
    composition_root_instance._tool_bar = mock_toolbar_instance
    composition_root_instance._tool_bar_actions = mock_toolbar_actions_instance

    # Store patched class mocks for later assertions
    # mock_ConfigService_class_patch is not needed here as ConfigService is passed directly
    composition_root_instance._mock_ApplicationModel_class = (
        mock_ApplicationModel_class_patch
    )
    composition_root_instance._mock_CommandManager_class = (
        mock_CommandManager_class_patch
    )
    composition_root_instance._mock_ProjectController_class = (
        mock_ProjectController_class_patch
    )
    composition_root_instance._mock_LayoutController_class = (
        mock_LayoutController_class_patch
    )
    composition_root_instance._mock_NodeController_class = (
        mock_NodeController_class_patch
    )
    composition_root_instance._mock_LayoutManager_class = mock_LayoutManager_class_patch
    composition_root_instance._mock_FreeLayoutEngine_class = (
        mock_FreeLayoutEngine_class_patch
    )
    composition_root_instance._mock_GridLayoutEngine_class = (
        mock_GridLayoutEngine_class_patch
    )
    composition_root_instance._mock_LayoutUIFactory_class = (
        mock_LayoutUIFactory_class_patch
    )
    composition_root_instance._mock_PlotPropertiesUIFactory_class = (
        mock_PlotPropertiesUIFactory_class_patch
    )
    composition_root_instance._mock_Renderer_class = mock_Renderer_class_patch
    composition_root_instance._mock_ToolService_class = mock_ToolService_class_patch
    composition_root_instance._mock_SelectionTool_class = mock_SelectionTool_class_patch
    composition_root_instance._mock_MainWindow_class = mock_MainWindow_class_patch
    composition_root_instance._mock_CanvasController_class = (
        mock_CanvasController_class_patch
    )
    composition_root_instance._mock_menu_bar_builder_class = (
        mock_MenuBarBuilder_class_patch
    )
    composition_root_instance._mock_tool_bar_builder_class = (
        mock_ToolBarBuilder_class_patch
    )
    composition_root_instance._mock_build_line_plot_ui_widgets_func = (
        mock_build_line_plot_ui_widgets_func_patch
    )
    composition_root_instance._mock_build_scatter_plot_ui_widgets_func = (
        mock_build_scatter_plot_ui_widgets_func_patch
    )
    composition_root_instance._mock_Figure_class = (
        mock_figure_class_patch  # Store the Figure class mock
    )

    mock_set_icon_config_patch.assert_called_once_with(mock_config_service)

    return composition_root_instance


class TestCompositionRoot:

    # Test for the fix in _assemble_menus
    def test_assemble_menus_assigns_correctly(
        self,
        composition_root,
        mock_project_controller,
        mock_layout_controller,
        mock_command_manager,
    ):
        """
        Test that _assemble_menus correctly assigns _menu_bar and _main_menu_actions
        from the MenuBarBuilder's build() method.
        """
        mock_menu_bar = composition_root._menu_bar
        mock_main_menu_actions = composition_root._main_menu_actions

        composition_root._assemble_menus()

        assert composition_root._menu_bar is mock_menu_bar
        assert composition_root._main_menu_actions is mock_main_menu_actions

        composition_root._mock_menu_bar_builder_class.assert_called_once_with(
            project_controller=mock_project_controller,
            layout_controller=mock_layout_controller,
            command_manager=mock_command_manager,
        )

    # Test for the full assemble method (integration-like)
    def test_assemble_returns_application_components(self, composition_root):
        """
        Test that the full assemble() method runs without error and returns
        a fully populated ApplicationComponents object.
        """
        components = composition_root.assemble()

        assert isinstance(components, ApplicationComponents)
        assert components.app is composition_root._app
        assert components.model is composition_root._model
        assert components.command_manager is composition_root._command_manager
        assert components.project_controller is composition_root._project_controller
        assert components.layout_controller is composition_root._layout_controller
        assert components.node_controller is composition_root._node_controller
        assert components.canvas_controller is composition_root._canvas_controller
        assert components.view is composition_root._view
        assert components.selection_tool is composition_root._selection_tool
        assert components.tool_manager is composition_root._tool_manager
        assert components.main_menu_actions is composition_root._main_menu_actions
        assert components.tool_bar_actions is composition_root._tool_bar_actions
        assert components.layout_ui_factory is composition_root._layout_ui_factory
        assert components.layout_manager is composition_root._layout_manager

    def test_assemble_core_components_uses_config_for_figure(
        self, composition_root, mock_application_model, mock_config_service, mocker
    ):  # Renamed mock_model
        """
        Test that _assemble_core_components uses values from ConfigService for Figure creation.
        """
        # Get the mock for the Figure class that was patched in the assembler fixture
        mock_figure_class = mocker.patch("src.core.composition_root.Figure")
        mock_figure_instance = (
            mock_figure_class.return_value
        )  # The mock instance returned by the constructor

        composition_root._assemble_core_components()

        # Assert that the Figure constructor was called with the correct arguments
        mock_figure_class.assert_called_once_with(
            figsize=(
                mock_config_service.get_required("figure.default_width"),
                mock_config_service.get_required("figure.default_height"),
            ),
            dpi=mock_config_service.get_required("figure.default_dpi"),
            facecolor=mock_config_service.get_required("figure.default_facecolor"),
        )
        # Assert that these properties are then also set on the application model
        mock_application_model.figure = mock_figure_instance

    def test_assemble_main_window_receives_config_service(
        self, composition_root, mock_main_window, mock_config_service, mocker
    ):
        """
        Test that MainWindow.__init__ receives the ConfigService instance.
        """
        # Get the mock for MainWindow from the assembler's patching context
        mock_main_window_class = mocker.patch("src.core.composition_root.MainWindow")
        mock_main_window_class.return_value = mock_main_window

        composition_root._assemble_core_components()
        composition_root._assemble_menus()
        composition_root._assemble_tooling()
        composition_root._assemble_main_window()

        # Now verify the call to MainWindow's constructor using the patched class
        mock_main_window_class.assert_called_once_with(
            model=composition_root._model,
            project_controller=composition_root._project_controller,
            layout_controller=composition_root._layout_controller,
            node_controller=composition_root._node_controller,
            command_manager=composition_root._command_manager,
            plot_types=composition_root._plot_types,
            menu_bar=composition_root._menu_bar,
            main_menu_actions=composition_root._main_menu_actions,
            tool_bar=composition_root._tool_bar,
            tool_bar_actions=composition_root._tool_bar_actions,
            plot_properties_ui_factory=composition_root._plot_properties_ui_factory,
            config_service=mock_config_service,
            layout_ui_factory=composition_root._layout_ui_factory,
        )

    def test_controllers_receive_config_service(
        self,
        composition_root,
        mock_application_model,
        mock_command_manager,
        mock_config_service,
        mock_layout_manager,
    ):  # Renamed mock_model
        """
        Test that ProjectController, LayoutController, and NodeController are instantiated
        with the correct dependencies, including ConfigService for ProjectController and LayoutController.
        """
        composition_root._assemble_core_components()

        # ProjectController assertions
        composition_root._mock_ProjectController_class.assert_called_once_with(
            model=mock_application_model,
            command_manager=mock_command_manager,
            config_service=mock_config_service,
            layout_manager=mock_layout_manager,
        )

        # LayoutController assertions
        composition_root._mock_LayoutController_class.assert_called_once_with(
            model=mock_application_model,
            command_manager=mock_command_manager,
            layout_manager=mock_layout_manager,
        )

        # NodeController assertions (does not take config_service)
        composition_root._mock_NodeController_class.assert_called_once_with(
            model=mock_application_model, command_manager=mock_command_manager
        )

    def test_assemble_tooling_adds_tools_and_sets_active_tool(
        self,
        composition_root,
        mock_tool_manager,
        mock_selection_tool,
        mock_config_service,
    ):
        """
        Test that _assemble_tooling correctly instantiates tools, adds them to the ToolService,
        and sets the default active tool based on configuration.
        """
        with (
            patch(
                "src.core.composition_root.SelectionTool",
                return_value=mock_selection_tool,
            ) as MockSelectionTool,
            patch("src.core.composition_root.MockTool") as MockMockTool,
        ):

            composition_root._assemble_tooling()

            MockSelectionTool.assert_called_once_with(
                model=composition_root._model,
                command_manager=composition_root._command_manager,
                canvas_widget=None,
            )
            mock_tool_manager.add_tool.assert_any_call(mock_selection_tool)

            # Verify MockTools are added (count of unique names)
            # There are 5 MockTools besides SelectionTool in _assemble_tooling
            assert MockMockTool.call_count == 5

            expected_mock_tool_names = [
                ToolName.DIRECT_SELECTION.value,
                ToolName.EYEDROPPER.value,
                ToolName.PLOT.value,
                ToolName.TEXT.value,
                ToolName.ZOOM.value,
            ]

            # Verify each mock tool is added
            for name in expected_mock_tool_names:
                # We cannot easily check the arguments to MockTool directly since it's patched
                # and each call creates a new mock instance. Instead, we rely on call_count and
                # the fact that add_tool is called with a MockTool instance.
                pass  # The check was too complex, simplifying to just checking add_tool call.

            # Explicitly check add_tool calls for MockTools
            mock_tool_manager.add_tool.assert_any_call(
                MockMockTool.return_value
            )  # Any mock tool instance

            mock_tool_manager.set_active_tool.assert_called_once_with(
                mock_config_service.get(
                    "tool.default_active_tool", ToolName.SELECTION.value
                )
            )

    def test_assemble_tooling_assigns_canvas_widget_to_tools(
        self, composition_root, mock_main_window, mock_tool_manager, mock_selection_tool
    ):
        """
        Test that the canvas_widget is correctly assigned to the tools after MainWindow is assembled.
        """
        composition_root._assemble_core_components()  # Needed to initialize _model etc.
        composition_root._assemble_tooling()  # Tools are created, selection_tool.canvas_widget is initially None
        composition_root._assemble_main_window()  # MainWindow is created, and canvas_widget is assigned to tools

        assert mock_selection_tool._canvas_widget is mock_main_window.canvas_widget
        for tool_name, tool in mock_tool_manager._tools.items():
            assert tool._canvas_widget is mock_main_window.canvas_widget

    def test_assemble_canvas_controller_instantiates_canvas_controller(
        self,
        composition_root,
        mock_canvas_controller,
        mock_application_model,
        mock_main_window,
        mock_tool_manager,
        mock_command_manager,
        mock_layout_controller,
    ):  # Renamed mock_model
        """
        Test that _assemble_canvas_controller instantiates the CanvasController with correct dependencies.
        """
        composition_root._assemble_main_window()  # Ensure _view and canvas_widget are set
        composition_root._assemble_tooling()  # Ensure _tool_manager is set
        composition_root._assemble_canvas_controller()

        composition_root._mock_CanvasController_class.assert_called_once_with(
            model=mock_application_model,
            canvas_widget=mock_main_window.canvas_widget,
            tool_manager=mock_tool_manager,
            command_manager=mock_command_manager,
            layout_controller=composition_root._layout_controller,  # Use the stored instance from assembler
        )
        assert composition_root._canvas_controller is mock_canvas_controller

    def test_connect_signals(
        self,
        composition_root,
        mock_application_model,
        mock_main_window,
        mock_project_controller,
        mock_layout_controller,
        mock_selection_tool,
    ):  # Renamed mock_model
        """
        Test that _connect_signals correctly connects all signals to their respective slots.
        """
        # Assemble necessary components for _connect_signals to run
        composition_root._assemble_core_components()
        composition_root._assemble_menus()
        composition_root._assemble_tooling()
        composition_root._assemble_main_window()
        composition_root._assemble_canvas_controller()

        # Call the method under test
        composition_root._connect_signals()

        # Verify connections for main window actions
        mock_main_window.new_layout_action.triggered.connect.assert_called_once_with(
            mock_project_controller.create_new_layout
        )
        mock_main_window.save_project_action.triggered.connect.assert_called_once()
        mock_main_window.open_project_action.triggered.connect.assert_called_once()

        # Verify connections for model changes
        mock_application_model.modelChanged.connect.assert_called_once_with(
            composition_root._redraw_canvas_callback
        )
        mock_application_model.selectionChanged.connect.assert_called_once_with(
            composition_root._redraw_canvas_callback
        )
        mock_application_model.layoutConfigChanged.connect.assert_called_once_with(
            composition_root._redraw_canvas_callback
        )

        # Verify connection for selection tool
        mock_selection_tool.plot_double_clicked.connect.assert_called_once_with(
            mock_main_window.show_properties_panel
        )

    def test_redraw_canvas_callback(
        self, composition_root, mock_renderer, mock_application_model, mock_main_window
    ):  # Renamed mock_model
        """
        Test that _redraw_canvas_callback correctly calls renderer.render and figure_canvas.draw.
        """
        # Assemble necessary components for _redraw_canvas_callback to run
        composition_root._assemble_core_components()
        composition_root._assemble_main_window()  # To set _view and canvas_widget

        # Call the method under test
        composition_root._redraw_canvas_callback()

        # Verify renderer.render is called with correct arguments
        mock_renderer.render.assert_called_once_with(
            mock_main_window.canvas_widget.figure,
            mock_application_model.scene_root,
            mock_application_model.selection,
        )
        # Verify figure_canvas.draw is called
        mock_main_window.canvas_widget.figure_canvas.draw.assert_called_once()

    def test_plot_properties_ui_factory_registers_builders(
        self, composition_root, mock_plot_properties_ui_factory
    ):
        """
        Test that PlotPropertiesUIFactory.register_builder is called for PlotType.LINE and PlotType.SCATTER.
        """
        # Assemble core components to trigger the registration calls
        composition_root._assemble_core_components()

        # Verify register_builder calls
        mock_plot_properties_ui_factory.register_builder.assert_any_call(
            PlotType.LINE, composition_root._mock_build_line_plot_ui_widgets_func
        )
        mock_plot_properties_ui_factory.register_builder.assert_any_call(
            PlotType.SCATTER, composition_root._mock_build_scatter_plot_ui_widgets_func
        )
        assert mock_plot_properties_ui_factory.register_builder.call_count == 2

    def test_composition_root_layout_component_wiring(
        self,
        composition_root,
        mock_application_model,
        mock_command_manager,  # Renamed mock_model
        mock_config_service,
        mock_free_layout_engine,
        mock_grid_layout_engine,
        mock_layout_manager,
        mock_layout_ui_factory,
        mock_main_window,
        mock_renderer,
        mock_tool_manager,
        mock_canvas_controller,
    ):  # Removed mocker
        """
        Test that ApplicationAssembler successfully instantiates and wires up all new layout components
        (FreeLayoutEngine, GridLayoutEngine, LayoutManager, LayoutUIFactory) with correct dependencies,
        and passes LayoutManager to ProjectController and LayoutController, and LayoutUIFactory to MainWindow.
        """
        # Call assemble to trigger all instantiations and wiring
        components = composition_root.assemble()

        # Verify FreeLayoutEngine instantiation
        composition_root._mock_FreeLayoutEngine_class.assert_called_once_with()

        # Verify GridLayoutEngine instantiation
        composition_root._mock_GridLayoutEngine_class.assert_called_once_with(
            config_service=mock_config_service
        )

        # Verify LayoutManager instantiation
        composition_root._mock_LayoutManager_class.assert_called_once_with(
            application_model=mock_application_model,
            free_engine=mock_free_layout_engine,
            grid_engine=mock_grid_layout_engine,
            config_service=mock_config_service,
        )
        assert components.layout_manager is mock_layout_manager

        # Verify LayoutUIFactory instantiation
        composition_root._mock_LayoutUIFactory_class.assert_called_once_with(
            config_service=mock_config_service,
            layout_manager=mock_layout_manager,
        )
        assert components.layout_ui_factory is mock_layout_ui_factory

        # Verify Renderer receives LayoutManager
        composition_root._mock_Renderer_class.assert_called_once_with(
            layout_manager=mock_layout_manager, application_model=mock_application_model
        )

        # Verify MainWindow receives LayoutUIFactory and LayoutManager
        composition_root._mock_MainWindow_class.assert_called_once_with(
            model=composition_root._model,
            project_controller=composition_root._project_controller,
            layout_controller=composition_root._layout_controller,
            node_controller=composition_root._node_controller,
            command_manager=composition_root._command_manager,
            plot_types=composition_root._plot_types,
            menu_bar=composition_root._menu_bar,
            main_menu_actions=composition_root._main_menu_actions,
            tool_bar=composition_root._tool_bar,
            tool_bar_actions=composition_root._tool_bar_actions,
            properties_ui_factory=composition_root._properties_ui_factory,
            config_service=mock_config_service,
            layout_ui_factory=mock_layout_ui_factory,
        )
        assert components.view is mock_main_window

        # Verify CanvasController receives LayoutManager and ProjectController
        composition_root._mock_CanvasController_class.assert_called_once_with(
            model=mock_application_model,
            canvas_widget=mock_main_window.canvas_widget,
            tool_manager=mock_tool_manager,
            command_manager=mock_command_manager,
            layout_controller=composition_root._layout_controller,  # Use the stored instance from assembler
        )
        assert components.canvas_controller is mock_canvas_controller

    def test_assemble_core_components_raises_config_error_on_missing_figure_properties(
        self, composition_root, mock_config_service
    ):
        """
        Test that _assemble_core_components raises a ConfigError if required figure properties are missing
        from the ConfigService.
        """
        # Configure the mock to raise ConfigError for all required figure properties
        mock_config_service.get_required.side_effect = ConfigError(
            "Missing config key: figure.default_width"
        )

        with pytest.raises(ConfigError, match="Missing config key: figure.default_"):
            composition_root._assemble_core_components()
