import pytest
from unittest.mock import MagicMock, ANY, patch
from pathlib import Path

from src.core.composition_root import CompositionRoot
from src.core.application_components import ApplicationComponents
from src.shared.events import Events


@pytest.fixture
def composition_root(mock_qapplication, mock_config_service, mocker):
    """Provides a CompositionRoot instance with mocked core dependencies."""
    
    # Global patches for this fixture to prevent UI/Matplotlib crashes
    mocker.patch("src.core.composition_root.Figure")
    
    # Controllers & Services
    mock_pc = MagicMock()
    for m in ["handle_new_project", "handle_new_from_template_request", "handle_open_project_request", 
              "handle_save_project", "handle_save_as_project_request", "handle_open_recent_project",
              "on_open_path_provided", "on_save_as_path_provided", "on_template_provided"]:
        getattr(mock_pc, m).__name__ = m
    mocker.patch("src.core.composition_root.ProjectController", return_value=mock_pc)
    
    mock_cm = MagicMock()
    mock_cm.undo.__name__ = "undo"
    mock_cm.redo.__name__ = "redo"
    mocker.patch("src.core.composition_root.CommandManager", return_value=mock_cm)
    
    mock_ds = MagicMock()
    mock_ds.handle_load_request.__name__ = "load"
    mocker.patch("src.core.composition_root.DataService", return_value=mock_ds)
    
    mock_rn = MagicMock()
    mock_rn.handle_node_removal.__name__ = "removal"
    # Refactored: Renderer -> FigureRenderer
    mocker.patch("src.core.composition_root.FigureRenderer", return_value=mock_rn)
    
    mock_lm = MagicMock()
    mock_lm.on_model_reset.__name__ = "reset"
    mocker.patch("src.core.composition_root.LayoutManager", return_value=mock_lm)

    mock_mw = MagicMock()
    mock_mw._prompt_for_open_path_for_node_data.__name__ = "mock_prompt"
    mocker.patch("src.core.composition_root.MainWindow", return_value=mock_mw)
    
    mocker.patch("src.core.composition_root.CanvasWidget")
    mocker.patch("src.core.composition_root.SidePanel")
    mocker.patch("src.core.composition_root.PropertiesTab")
    mocker.patch("src.core.composition_root.LayoutTab")
    mocker.patch("src.core.composition_root.LayersTab")

    # Mock builders
    mock_menu_actions = MagicMock()
    mock_menu_actions.exit_action.triggered.connect = MagicMock()
    mocker.patch("src.ui.builders.menu_bar_builder.MenuBarBuilder.build", return_value=(MagicMock(), mock_menu_actions))
    mocker.patch("src.ui.builders.ribbon_bar_builder.RibbonBarBuilder.build", return_value=(MagicMock(), MagicMock()))
    mocker.patch("src.ui.builders.tool_bar_builder.ToolBarBuilder.build", return_value=(MagicMock(), MagicMock()))

    def unified_config(key, default=None):
        data = {
            "figure.default_width": 5.0,
            "figure.default_height": 3.0,
            "figure.default_dpi": 100,
            "figure.default_facecolor": "white",
            "paths.layout_templates_dir": "templates",
            "layout.max_recent_files": 5,
            "ui.default_layout_mode": "free_form",
            "paths.icon_base_dir": "icons",
            "tool.default_active_tool": "selection"
        }
        return data.get(key, default)

    mock_config_service.get.side_effect = unified_config
    mock_config_service.get_required.side_effect = lambda k: unified_config(k)
    
    return CompositionRoot(mock_qapplication, mock_config_service)


class TestCompositionRoot:

    def test_assemble_returns_valid_components(self, composition_root):
        """Verifies that assemble() returns a fully populated ApplicationComponents object."""
        components = composition_root.assemble()

        assert isinstance(components, ApplicationComponents)
        assert components.application_model is not None
        assert components.event_aggregator is not None
        assert components.view is not None

    def test_dependency_sharing(self, composition_root, mocker):
        """Verifies that assembled components share the same model and event aggregator."""
        from src.services.event_aggregator import EventAggregator
        from src.models.application_model import ApplicationModel
        
        real_ea = EventAggregator()
        mocker.patch("src.core.composition_root.EventAggregator", return_value=real_ea)
        
        # Figure size is required now
        real_model = ApplicationModel(event_aggregator=real_ea, figure_size=(20.0, 15.0))
        mocker.patch("src.core.composition_root.ApplicationModel", return_value=real_model)
        
        components = composition_root.assemble()
            
        ea = components.event_aggregator
        model = components.application_model
        
        assert ea is real_ea
        assert model is real_model
        
        from src.core.composition_root import ProjectController, LayoutManager
        
        args, kwargs = ProjectController.call_args
        assert kwargs["lifecycle"] is model
        assert kwargs["event_aggregator"] is ea
        
        args, kwargs = LayoutManager.call_args
        assert kwargs["event_aggregator"] is ea

    def test_assemble_core_components_figure_config(self, composition_root, mock_config_service, mocker):
        """Verifies Figure is created with specific values from config service."""
        def custom_config(key, default=None):
            data = {
                "figure.default_width": 12.0,
                "figure.default_height": 9.0,
                "figure.default_dpi": 300,
                "figure.default_facecolor": "red",
                "ui.default_layout_mode": "free_form"
            }
            return data.get(key, default)
            
        mock_config_service.get.side_effect = custom_config
        mock_config_service.get_required.side_effect = lambda k: custom_config(k)
        
        mock_figure_class = mocker.patch("src.core.composition_root.Figure")
        composition_root._assemble_core_components()
        
        mock_figure_class.assert_called_once_with(
            figsize=(12.0, 9.0),
            dpi=300,
            facecolor="red"
        )

    def test_event_subscriptions(self, composition_root, mocker):
        """Verifies that assembly triggers the correct event subscriptions."""
        mock_ea = MagicMock()
        mocker.patch("src.core.composition_root.EventAggregator", return_value=mock_ea)
        
        composition_root.assemble()
        
        # Verify critical life-cycle subscriptions
        expected_events = [
            Events.NEW_PROJECT_REQUESTED,
            Events.SAVE_PROJECT_REQUESTED,
            Events.SCENE_GRAPH_CHANGED,
            Events.LAYOUT_CONFIG_CHANGED
        ]
        
        for event in expected_events:
            mock_ea.subscribe.assert_any_call(event, ANY)

    def test_redraw_canvas_callback(self, composition_root):
        """Verifies that the redraw callback orchestrates the renderer and canvas widget."""
        # Use FigureRenderer mock name
        mock_renderer = MagicMock()
        mock_canvas_widget = MagicMock()
        mock_figure = MagicMock()
        mock_model = MagicMock()
        
        composition_root._figure_renderer = mock_renderer
        composition_root._canvas_widget = mock_canvas_widget
        composition_root._figure = mock_figure
        composition_root._application_model = mock_model
        
        composition_root._redraw_canvas_callback()
        
        mock_renderer.render.assert_called_once_with(
            mock_figure, mock_model.scene_root, mock_model.selection
        )
        mock_canvas_widget.figure_canvas.draw.assert_called_once()

    def test_redraw_canvas_callback_syncs_limits(self, composition_root):
        """Verifies that redraw callback triggers limit sync if node_id is provided."""
        mock_renderer = MagicMock()
        composition_root._figure_renderer = mock_renderer
        composition_root._canvas_widget = MagicMock()
        composition_root._application_model = MagicMock()
        composition_root._figure = MagicMock()
        
        composition_root._redraw_canvas_callback(node_id="p123")
        
        mock_renderer.sync_back_limits.assert_called_once_with("p123")
