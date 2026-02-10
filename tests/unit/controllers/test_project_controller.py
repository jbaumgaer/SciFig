import pytest
from unittest.mock import MagicMock, patch, mock_open
import zipfile
from pathlib import Path
import json
import logging
from PySide6.QtWidgets import QWidget

from src.controllers.project_controller import ProjectController
from src.models.nodes import GroupNode
from src.models.nodes.plot_node import PlotNode

@pytest.fixture
def mock_parent_widget():
    return MagicMock(spec=QWidget)

@pytest.fixture
def project_controller(mock_application_model, mock_command_manager, mock_config_service, mock_layout_manager):
    return ProjectController(mock_application_model, mock_command_manager, mock_config_service, mock_layout_manager)


class TestProjectController:
        
    def test_project_controller_initialization(self, project_controller, mock_application_model, mock_command_manager, mock_config_service, mock_layout_manager):
        """
        Test that ProjectController initializes correctly and its attributes are set.
        """
        assert project_controller.model is mock_application_model
        assert project_controller.command_manager is mock_command_manager
        assert project_controller._config_service is mock_config_service
        assert project_controller._layout_manager is mock_layout_manager

    def test_save_project_calls_qfiledialog(self, project_controller, mock_parent_widget):
        """
        Test that save_project calls QFileDialog.getSaveFileName with the correct arguments and parent.
        """
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=("", "")) as mock_get_save_file_name:
            project_controller.save_project(mock_parent_widget)
            mock_get_save_file_name.assert_called_once_with(
                mock_parent_widget,
                "Save Project",
                "",
                "SciFig Project (*.sci)",
            )

    def test_save_project_success(self, project_controller, mock_application_model, mock_parent_widget, mock_plot_node):
        """
        Test that save_project successfully calls relevant functions for saving the project
        and adding to recent files.
        """
        mock_file_path = "test_project.sci"
        mock_application_model.scene_root.all_descendants.return_value = [mock_plot_node]
        mock_application_model.to_dict.return_value = {"version": "1.0", "scene": {}}

        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=(mock_file_path, "")), \
            patch('tempfile.TemporaryDirectory') as mock_temp_dir_class, \
            patch('builtins.open', mock_open()) as mock_builtin_open, \
            patch('json.dump') as mock_json_dump, \
            patch('zipfile.ZipFile') as mock_zip_file_class, \
            patch.object(project_controller, '_add_to_recent_files') as mock_add_to_recent_files, \
            patch('src.controllers.project_controller.Path') as MockPath_constructor, \
            patch('os.mkdir') as mock_os_mkdir: # <--- Patch os.mkdir to prevent actual directory creation

            # The string path returned by TemporaryDirectory
            temp_dir_str_from_context = "/mock/temp/dir_abc"
            mock_temp_dir_class.return_value.__enter__.return_value = temp_dir_str_from_context

            # Mock the Path object that will be instantiated by Path(temp_dir_str_from_context)
            mock_temp_dir_path_instance = MagicMock(spec=Path)
            mock_temp_dir_path_instance.__str__.return_value = temp_dir_str_from_context
            mock_temp_dir_path_instance.exists.return_value = True # Important for mkdir behavior if parents=False

            # Mock the .rglob() result
            mock_project_json_path = MagicMock(spec=Path)
            mock_project_json_path.__str__.return_value = f"{temp_dir_str_from_context}/project.json"
            # Mock relative_to for the project_json_path mock
            mock_project_json_path.relative_to.return_value = MagicMock(spec=Path, __str__=lambda: "project.json")

            mock_parquet_file_path = MagicMock(spec=Path)
            mock_parquet_file_path.__str__.return_value = f"{temp_dir_str_from_context}/data/{mock_plot_node.id}.parquet"
            # Mock relative_to for the parquet_file_path mock
            mock_parquet_file_path.relative_to.return_value = MagicMock(spec=Path, __str__=lambda: f"data/{mock_plot_node.id}.parquet")


            mock_temp_dir_path_instance.rglob.return_value = [mock_project_json_path, mock_parquet_file_path]


            # Mocking for data_dir = temp_dir / "data"
            mock_data_dir_path_instance = MagicMock(spec=Path)
            mock_data_dir_path_instance.mkdir.return_value = None # Ensure mkdir on data_dir succeeds
            mock_data_dir_path_instance.__str__.return_value = f"{temp_dir_str_from_context}/data"

            # Mocking for parquet_path = data_dir / f"{node.id}.parquet"
            mock_final_parquet_path_instance = MagicMock(spec=Path)
            mock_final_parquet_path_instance.__str__.return_value = f"{temp_dir_str_from_context}/data/{mock_plot_node.id}.parquet"


            # Configure the Path constructor patch:
            # When Path(temp_dir_str_from_context) is called, return mock_temp_dir_path_instance
            def path_constructor_side_effect(arg):
                if str(arg) == temp_dir_str_from_context:
                    return mock_temp_dir_path_instance
                # For Path objects created within the code, ensure they are also mocks
                # This handles Path(some_string) calls for example 'configs/layouts'
                m = MagicMock(spec=Path)
                m.__str__.return_value = str(arg) # Ensure str(Path('some/path')) works
                return m

            MockPath_constructor.side_effect = path_constructor_side_effect

            # Ensure that mock_temp_dir_path_instance / "data" returns mock_data_dir_path_instance
            mock_temp_dir_path_instance.__truediv__.side_effect = lambda other: \
                mock_data_dir_path_instance if str(other) == "data" else MagicMock(spec=Path)

            # Ensure that mock_data_dir_path_instance / f"{node.id}.parquet" returns mock_final_parquet_path_instance
            mock_data_dir_path_instance.__truediv__.side_effect = lambda other: \
                mock_final_parquet_path_instance if str(other) == f"{mock_plot_node.id}.parquet" else MagicMock(spec=Path)


            project_controller.save_project(mock_parent_widget)

            # Assertions
            MockPath_constructor.assert_any_call(temp_dir_str_from_context) # Verify Path() constructor was called for temp_dir

            mock_data_dir_path_instance.mkdir.assert_called_once()

            mock_plot_node.data.to_parquet.assert_called_once_with(mock_final_parquet_path_instance) # Use the specific mock path
            
            mock_application_model.to_dict.assert_called_once()
            mock_json_dump.assert_called_once_with(mock_application_model.to_dict.return_value, mock_builtin_open(), indent=4)
            mock_zip_file_class.assert_called_once_with(mock_file_path, "w", zipfile.ZIP_DEFLATED)

            zip_file_mock_instance = mock_zip_file_class.return_value.__enter__.return_value
            zip_file_mock_instance.write.assert_any_call(
                mock_project_json_path, mock_project_json_path.relative_to.return_value
            )
            zip_file_mock_instance.write.assert_any_call(
                mock_parquet_file_path, mock_parquet_file_path.relative_to.return_value
            )

            mock_add_to_recent_files.assert_called_once_with(mock_file_path)

    def test_save_project_cancellation(self, project_controller, mock_application_model, mock_parent_widget):
        """
        Test that if save_project is cancelled, no file operations or model updates occur.
        """
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=("", "")) as mock_get_save_file_name, \
            patch('tempfile.TemporaryDirectory') as mock_temp_dir_class, \
            patch('builtins.open', mock_open()) as mock_builtin_open, \
            patch('json.dump') as mock_json_dump, \
            patch('zipfile.ZipFile') as mock_zip_file_class, \
            patch.object(project_controller, '_add_to_recent_files') as mock_add_to_recent_files, \
            patch('src.controllers.project_controller.Path') as MockPath_constructor, \
            patch('os.mkdir') as mock_os_mkdir:

            project_controller.save_project(mock_parent_widget)

            # Assert after calling save_project to be sure
            mock_temp_dir_class.assert_not_called()
            mock_builtin_open.assert_not_called()
            mock_json_dump.assert_not_called()
            mock_zip_file_class.assert_not_called()
            mock_add_to_recent_files.assert_not_called()
            mock_os_mkdir.assert_not_called()
            mock_application_model.to_dict.assert_not_called()
            MockPath_constructor.assert_not_called()


    def test_open_project_calls_qfiledialog(self, project_controller, mock_parent_widget):
        """
        Test that open_project calls QFileDialog.getOpenFileName with the correct arguments and parent
        when no file_path is provided.
        """
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=("", "")) as mock_get_open_file_name:
            project_controller.open_project(parent=mock_parent_widget)
            mock_get_open_file_name.assert_called_once_with(
                mock_parent_widget,
                "Open Project",
                "",
                "SciFig Project (*.sci)",
            )

    def test_open_project_success(self, project_controller, mock_application_model, mock_parent_widget):
        """
        Test that open_project successfully calls relevant functions for opening the project,
        loading the model, and adding to recent files.
        """
        mock_file_path = "test_project.sci"
        mock_project_dict = {"version": "1.0", "scene": {"id": "root_node"}}
        
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=(mock_file_path, "")) as mock_get_open_file_name, \
            patch('tempfile.TemporaryDirectory') as mock_temp_dir_class, \
            patch('builtins.open', mock_open(read_data=json.dumps(mock_project_dict))) as mock_builtin_open, \
            patch('json.load', return_value=mock_project_dict) as mock_json_load, \
            patch('zipfile.ZipFile') as mock_zip_file_class, \
            patch.object(project_controller, '_add_to_recent_files') as mock_add_to_recent_files, \
            patch('src.controllers.project_controller.Path') as MockPath_constructor:

            # The string path returned by TemporaryDirectory
            temp_dir_str_from_context = "/mock/temp/dir_open"
            mock_temp_dir_class.return_value.__enter__.return_value = temp_dir_str_from_context

            # Mock the Path object that will be instantiated by Path(temp_dir_str_from_context)
            mock_temp_dir_path_instance = MagicMock(spec=Path)
            mock_temp_dir_path_instance.__str__.return_value = temp_dir_str_from_context
            mock_temp_dir_path_instance.exists.return_value = True # Important for Path.exists() if called

            # Mock project.json path
            mock_json_path_instance = MagicMock(spec=Path)
            mock_json_path_instance.__str__.return_value = f"{temp_dir_str_from_context}/project.json"

            # Configure the Path constructor patch
            def path_constructor_side_effect(arg):
                if str(arg) == temp_dir_str_from_context:
                    return mock_temp_dir_path_instance
                if str(arg) == f"{temp_dir_str_from_context}/project.json":
                    return mock_json_path_instance
                m = MagicMock(spec=Path)
                m.__str__.return_value = str(arg)
                return m
            MockPath_constructor.side_effect = path_constructor_side_effect

            # Mock zipfile.ZipFile.extractall
            mock_zip_file_class.return_value.__enter__.return_value.extractall.return_value = None
            mock_zf_bound_instance = mock_zip_file_class.return_value.__enter__.return_value # Reference the object 'zf' binds to

            project_controller.open_project(parent=mock_parent_widget)

            # Assert QFileDialog was called (if file_path not provided)
            mock_get_open_file_name.assert_called_once()

            # Assert temporary directory was used
            mock_temp_dir_class.assert_called_once()

            # Assert zipfile was opened and extractall called
            mock_zip_file_class.assert_called_once_with(mock_file_path, "r")
            mock_zf_bound_instance.extractall.assert_called_once_with(mock_temp_dir_path_instance) # Assert on the correctly bound mock instance

            # Assert project.json was loaded
            mock_json_load.assert_called_once_with(mock_builtin_open())

            # Assert model was loaded from dict
            mock_application_model.load_from_dict.assert_called_once_with(mock_project_dict, mock_temp_dir_path_instance)

            # Assert _add_to_recent_files is called
            mock_add_to_recent_files.assert_called_once_with(mock_file_path)

            MockPath_constructor.assert_any_call(temp_dir_str_from_context)

    def test_create_new_layout_sets_scene_root(self, project_controller, mock_application_model, mock_config_service):
        """
        Test that create_new_layout correctly sets the ApplicationModel's scene_root
        with a new GroupNode (or other node from template).
        """
        mock_template_name = "2x2_default.json"
        mock_layout_template_data = {"id": "new_root_layout", "type": "group", "name": "Test Layout", "visible": True} # <--- ADDED "visible"
        mock_new_root_node = MagicMock(spec=GroupNode, id="new_root_layout", name="New Root Layout")
        mock_new_plot_node = MagicMock(spec=PlotNode, id="plot_001", name="New Plot Node") # For all_descendants

        mock_config_service.get.side_effect = lambda key, default: {
            "layout.default_template": mock_template_name,
            "paths.layout_templates_dir": "configs/layouts",
            "organization": "TestOrg",
            "app_name": "TestApp",
            "layout.max_recent_files": 10
        }.get(key, default)

        # Mock Path.exists and open for template loading
        with patch('src.controllers.project_controller.Path') as MockPath_constructor, \
            patch('json.load', return_value=mock_layout_template_data) as mock_json_load, \
            patch('src.controllers.project_controller.node_factory', return_value=mock_new_root_node) as mock_node_factory, \
            patch('builtins.open', mock_open()) as mock_builtin_open: # <--- ADD THIS LINE

            # Mock the Path object for the template path
            mock_template_path_instance = MagicMock(spec=Path)
            mock_template_path_instance.exists.return_value = True
            MockPath_constructor.return_value = mock_template_path_instance # default return for Path()
            
            # Ensure that Path(layout_templates_dir) / default_template_name works
            mock_layout_templates_dir_path = MagicMock(spec=Path)
            mock_layout_templates_dir_path.__truediv__.return_value = mock_template_path_instance
            
            def path_constructor_side_effect(arg):
                if str(arg) == "configs/layouts":
                    return mock_layout_templates_dir_path
                # Handle other Path() calls if they arise during the process
                m = MagicMock(spec=Path)
                m.__str__.return_value = str(arg)
                return m
            MockPath_constructor.side_effect = path_constructor_side_effect

            mock_new_root_node.all_descendants.return_value = [mock_new_plot_node] # Simulate plots in new layout

            project_controller.create_new_layout()

            # Assertions
            mock_config_service.get.assert_any_call("layout.default_template", "2x2_default.json")
            mock_config_service.get.assert_any_call("paths.layout_templates_dir", "configs/layouts")
            
            mock_template_path_instance.exists.assert_called_once()
            mock_json_load.assert_called_once()
            mock_node_factory.assert_called_once_with(mock_layout_template_data)
            
            mock_application_model.set_scene_root.assert_called_once_with(mock_new_root_node)

            # Ensure existing plot data is processed (even if empty in this test)
            mock_application_model.scene_root.all_descendants.assert_called() # Called to extract existing states
            # The mock_new_root_node.all_descendants() would be called to iterate new slots
            mock_new_root_node.all_descendants.assert_called()


    def test_open_project_error_logs_exception(self, project_controller, mock_application_model, mock_parent_widget, caplog):
        """
        Test that if an error occurs during open_project, the exception is logged.
        """
        mock_file_path = "error_open_test.sci"

        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=(mock_file_path, "")) as mock_get_open_file_name, \
            patch('tempfile.TemporaryDirectory') as mock_temp_dir_class, \
            patch('builtins.open', mock_open()) as mock_builtin_open, \
            patch('json.load') as mock_json_load, \
            patch('zipfile.ZipFile') as mock_zip_file_class, \
            patch.object(project_controller, '_add_to_recent_files') as mock_add_to_recent_files, \
            patch('src.controllers.project_controller.Path') as MockPath_constructor:

            # Simulate an error during zip file extraction
            mock_zip_file_class.side_effect = zipfile.BadZipFile("Simulated open zip error")

            # Configure mocks for Path objects
            temp_dir_str_from_context = "/mock/temp/dir_open_error"
            mock_temp_dir_class.return_value.__enter__.return_value = temp_dir_str_from_context
            mock_temp_dir_path_instance = MagicMock(spec=Path)
            mock_temp_dir_path_instance.__str__.return_value = temp_dir_str_from_context
            MockPath_constructor.return_value = mock_temp_dir_path_instance # ensure Path() call returns our mock

            def path_constructor_side_effect(arg):
                if str(arg) == temp_dir_str_from_context:
                    return mock_temp_dir_path_instance
                m = MagicMock(spec=Path)
                m.__str__.return_value = str(arg)
                return m
            MockPath_constructor.side_effect = path_constructor_side_effect


            with caplog.at_level(logging.ERROR):
                project_controller.open_project(parent=mock_parent_widget)
                assert "Error opening project file 'error_open_test.sci': Simulated open zip error" in caplog.text

            # Ensure no other functions were called after the error occurred
            mock_temp_dir_class.assert_called_once() # Temporary directory is created before the zip error
            mock_zip_file_class.assert_called_once_with(mock_file_path, "r") # ZipFile is called before error
            mock_zip_file_class.return_value.__enter__.return_value.extractall.assert_not_called() # Extractall not called if ZipFile fails
            mock_builtin_open.assert_not_called()
            mock_json_load.assert_not_called()
            mock_application_model.load_from_dict.assert_not_called()
            mock_add_to_recent_files.assert_not_called()

    def test_open_project_cancellation(self, project_controller, mock_application_model, mock_parent_widget):
        """
        Test that if open_project is cancelled, no file operations or model updates occur.
        """
        # Simulate user cancelling the QFileDialog
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=("", "")) as mock_get_open_file_name, \
            patch('tempfile.TemporaryDirectory') as mock_temp_dir_class, \
            patch('builtins.open', mock_open()) as mock_builtin_open, \
            patch('json.load') as mock_json_load, \
            patch('zipfile.ZipFile') as mock_zip_file_class, \
            patch.object(project_controller, '_add_to_recent_files') as mock_add_to_recent_files, \
            patch('src.controllers.project_controller.Path') as MockPath_constructor:

            project_controller.open_project(parent=mock_parent_widget)

            # Assert no operations occurred
            mock_temp_dir_class.assert_not_called()
            mock_builtin_open.assert_not_called()
            mock_json_load.assert_not_called()
            mock_zip_file_class.assert_not_called()
            mock_application_model.load_from_dict.assert_not_called()
            mock_add_to_recent_files.assert_not_called()
            MockPath_constructor.assert_not_called()

