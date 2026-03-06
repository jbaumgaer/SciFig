import pytest
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, ANY

from src.controllers.project_controller import ProjectController
from src.interfaces.project_io import ProjectLifecycle
from src.models.nodes.group_node import GroupNode
from src.shared.events import Events


@pytest.fixture
def mock_lifecycle():
    """Provides a mock ProjectLifecycle implementation."""
    lifecycle = MagicMock(spec=ProjectLifecycle)
    lifecycle.file_path = None
    lifecycle.is_dirty = False
    lifecycle.as_dict.return_value = {"version": "1.0", "scene_root": {}}
    return lifecycle


@pytest.fixture
def project_controller(mock_lifecycle, mock_command_manager, mock_event_aggregator, tmp_path):
    """Provides a ProjectController instance with mocked dependencies."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    return ProjectController(
        lifecycle=mock_lifecycle,
        command_manager=mock_command_manager,
        template_dir=template_dir,
        max_recent_files=5,
        event_aggregator=mock_event_aggregator
    )


class TestProjectController:

    # --- Initialization & Subscriptions ---

    def test_initialization_subscribes_to_events(self, mock_event_aggregator):
        """Verifies that the controller hooks into relevant lifecycle events."""
        local_event_mock = MagicMock()
        ProjectController(MagicMock(), MagicMock(), Path("."), 5, local_event_mock)
        
        expected_events = [
            Events.WINDOW_TITLE_REQUESTED,
            Events.PROJECT_IS_DIRTY_CHANGED,
            Events.PROJECT_OPENED,
            Events.PROJECT_WAS_RESET
        ]
        for event in expected_events:
            local_event_mock.subscribe.assert_any_call(event, ANY)

    # --- Window Title Management ---

    def test_provide_window_title_untitled_clean(self, project_controller, mock_lifecycle, mock_event_aggregator):
        """Verifies formatting for a new, unsaved project."""
        mock_lifecycle.file_path = None
        mock_lifecycle.is_dirty = False
        
        project_controller._provide_window_title_data()
        
        mock_event_aggregator.publish.assert_called_once_with(
            Events.WINDOW_TITLE_DATA_READY, title="Untitled[*] - SciFig", is_dirty=False
        )

    def test_provide_window_title_named_dirty(self, project_controller, mock_lifecycle, mock_event_aggregator):
        """Verifies formatting for a named, modified project."""
        mock_lifecycle.file_path = Path("my_project.sci")
        mock_lifecycle.is_dirty = True
        
        project_controller._provide_window_title_data()
        
        mock_event_aggregator.publish.assert_called_once_with(
            Events.WINDOW_TITLE_DATA_READY, title="my_project.sci[*] - SciFig", is_dirty=True
        )

    # --- UI Request Handlers ---

    def test_handle_new_project(self, project_controller, mock_lifecycle):
        """Verifies new project intent triggers lifecycle reset."""
        project_controller.handle_new_project()
        mock_lifecycle.reset_state.assert_called_once()

    def test_handle_open_project_request(self, project_controller, mock_event_aggregator):
        """Verifies open request publishes prompt event."""
        project_controller.handle_open_project_request()
        mock_event_aggregator.publish.assert_called_once_with(Events.PROMPT_FOR_OPEN_PATH_REQUESTED)

    def test_handle_save_project_no_path(self, project_controller, mock_lifecycle, mock_event_aggregator):
        """Verifies save-as is triggered if no file path exists."""
        mock_lifecycle.file_path = None
        project_controller.handle_save_project()
        mock_event_aggregator.publish.assert_called_once_with(Events.PROMPT_FOR_SAVE_AS_PATH_REQUESTED)

    # --- Persistence Logic (Round Trip) ---

    def test_save_and_open_round_trip(self, project_controller, mock_lifecycle, tmp_path, mock_event_aggregator):
        """Verifies that project data is correctly archived into a zip and recovered."""
        project_file = tmp_path / "test_save.sci"
        
        # 1. Simulate Save
        project_controller._save_to_path(project_file)
        
        assert project_file.exists()
        assert zipfile.is_zipfile(project_file)
        
        # Verify content of zip
        with zipfile.ZipFile(project_file, 'r') as zf:
            assert "project.json" in zf.namelist()
            with zf.open("project.json") as f:
                data = json.load(f)
                assert data == {"version": "1.0", "scene_root": {}}

        # 2. Simulate Open
        project_controller._open_from_path(project_file)
        
        # Verify lifecycle was called with extracted data
        mock_lifecycle.load_from_state.assert_called_once()
        args = mock_lifecycle.load_from_state.call_args[0]
        assert args[0] == {"version": "1.0", "scene_root": {}}
        # Verify dirty flag reset
        mock_lifecycle.set_dirty.assert_called_with(False)

    # --- Template Logic ---

    def test_on_template_provided(self, project_controller, mock_lifecycle, mock_event_aggregator, mocker):
        """Verifies template loading and hydration trigger."""
        # Setup template file
        template_data = {"type": "GroupNode", "name": "Tmpl", "children": []}
        tmpl_path = project_controller._template_dir / "my_tmpl.json"
        with open(tmpl_path, "w") as f:
            json.dump(template_data, f)
            
        # Mock node_factory to return a real GroupNode
        mock_root = GroupNode(name="Tmpl")
        mocker.patch("src.controllers.project_controller.node_factory", return_value=mock_root)
        
        # Trigger
        project_controller.on_template_provided("my_tmpl")
        
        # Verify state reset and hydration
        mock_lifecycle.set_scene_root.assert_called_once_with(mock_root)
        mock_event_aggregator.publish.assert_any_call(Events.PROJECT_WAS_RESET)
        mock_event_aggregator.publish.assert_any_call(Events.TEMPLATE_LOADED, root_node=mock_root)

    def test_on_template_provided_cancelled(self, project_controller, mock_lifecycle):
        """Ensures no action if template selection was cancelled."""
        project_controller.on_template_provided(None)
        mock_lifecycle.set_scene_root.assert_not_called()

    # --- Robustness & Error Handling ---

    def test_get_template_names(self, project_controller, tmp_path):
        """Verifies globbing of template files."""
        # Setup: 2 valid, 1 invalid file
        (project_controller._template_dir / "tmpl1.json").write_text("{}")
        (project_controller._template_dir / "tmpl2.json").write_text("{}")
        (project_controller._template_dir / "notes.txt").write_text("not a template")
        
        names = project_controller.get_template_names()
        assert len(names) == 2
        assert "tmpl1" in names
        assert "tmpl2" in names

    def test_open_from_path_bad_zip_logs_error(self, project_controller, tmp_path, caplog):
        """Verifies that corrupted project files are handled gracefully."""
        invalid_file = tmp_path / "broken.sci"
        invalid_file.write_text("not a zip")
        
        with caplog.at_level("ERROR"):
            project_controller._open_from_path(invalid_file)
            
        assert "Error opening project file" in caplog.text
        assert "Simulated open zip error" not in caplog.text # verifying real zip check

    def test_open_from_path_missing_json_logs_error(self, project_controller, tmp_path, caplog):
        """Verifies error if zip is valid but missing project.json."""
        missing_json_file = tmp_path / "missing.sci"
        with zipfile.ZipFile(missing_json_file, 'w') as zf:
            zf.writestr("something_else.txt", "data")
            
        with caplog.at_level("ERROR"):
            project_controller._open_from_path(missing_json_file)
            
        assert "Error opening project file" in caplog.text

    def test_on_template_provided_malformed_json_logs_error(self, project_controller, caplog):
        """Verifies error if template file contains invalid JSON."""
        tmpl_path = project_controller._template_dir / "broken.json"
        tmpl_path.write_text("{ invalid json }")
        
        with caplog.at_level("ERROR"):
            project_controller.on_template_provided("broken")
            
        assert "Error loading template" in caplog.text

    # --- Reactive Logic ---

    def test_reacts_to_dirty_changed_event(self, project_controller, mock_event_aggregator):
        """Verifies that title is re-published when project becomes dirty."""
        # Find the handler bound to dirty changed
        handler = None
        for call_args in mock_event_aggregator.subscribe.call_args_list:
            if call_args.args[0] == Events.PROJECT_IS_DIRTY_CHANGED:
                handler = call_args.args[1]
                break
        
        assert handler is not None
        mock_event_aggregator.publish.reset_mock()
        
        # Simulate event trigger
        handler(is_dirty=True)
        
        # Verify title was refreshed
        mock_event_aggregator.publish.assert_called_with(
            Events.WINDOW_TITLE_DATA_READY, title=ANY, is_dirty=ANY
        )
