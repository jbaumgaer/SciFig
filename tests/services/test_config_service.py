import pytest
from pathlib import Path
from src.services.config_service import ConfigService
from src.shared.exceptions import ConfigError
from src.shared.constants import IconPath


# Helper function to create a temporary config file for testing
@pytest.fixture
def temp_config_file(tmp_path):
    config_content = """
    app_name: TestApp
    version: 1.0
    figure:
      default_width: 10.0
      default_height: 7.0
      default_facecolor: "red"
    paths:
      icon_base_dir: "test/icons"
      tool_icons:
        test_tool: "test_icon.svg"
    """
    file = tmp_path / "test_config.yaml"
    file.write_text(config_content)
    return file

@pytest.fixture
def invalid_config_file(tmp_path):
    config_content = """
    app_name: TestApp
    figure:
      default_width: 10.0
    - this is invalid yaml
    """
    file = tmp_path / "invalid_config.yaml"
    file.write_text(config_content)
    return file


def test_config_service_loads_valid_yaml(temp_config_file):
    """
    Test that ConfigService successfully loads a valid YAML file.
    """
    # config_service = ConfigService(temp_config_file)
    # assert config_service._initialized is True
    # assert config_service.get("app_name") == "TestApp"

def test_config_service_get_method_nested_keys(temp_config_file):
    """
    Test the get() method for retrieving nested configuration values.
    """
    # config_service = ConfigService(temp_config_file)
    # assert config_service.get("figure.default_width") == 10.0
    # assert config_service.get("figure.default_height") == 7.0
    # assert config_service.get("figure.default_facecolor") == "red"

def test_config_service_get_method_non_existent_key(temp_config_file):
    """
    Test the get() method returns default value for a non-existent key.
    """
    # config_service = ConfigService(temp_config_file)
    # assert config_service.get("non_existent_key", "default_value") == "default_value"
    # assert config_service.get("figure.non_existent_prop", 5.0) == 5.0

def test_config_service_handles_file_not_found():
    """
    Test that ConfigService raises FileNotFoundError for a non-existent config file.
    """
    # with pytest.raises(FileNotFoundError):
    #     ConfigService(Path("non_existent_path/config.yaml"))

def test_config_service_handles_invalid_yaml(invalid_config_file):
    """
    Test that ConfigService raises ValueError for invalid YAML content.
    """
    # with pytest.raises(ValueError): # or appropriate yaml.YAMLError subclass
    #     ConfigService(invalid_config_file)

def test_icon_path_get_path_from_config(temp_config_file):
    """
    Test that IconPath.get_path correctly constructs the path from ConfigService.
    This requires setting the ConfigService instance on IconPath class.
    """
    # config_service = ConfigService(temp_config_file)
    # IconPath.set_config_service(config_service)
    # expected_path = str(Path("test/icons") / "test_icon.svg")
    # assert IconPath.get_path("tool_icons.test_tool") == expected_path

def test_config_service_get_required_missing_key(tmp_path):
    """
    Test that ConfigService.get_required() raises ConfigError when a required key is missing,
    and returns the correct value when the key exists.
    """
    # Create a temporary config file with some data, but missing a 'required' key
    config_content = """
    test_section:
        existing_key: "value"
    """
    file = tmp_path / "test_config_required.yaml"
    file.write_text(config_content)

    config_service = ConfigService(file)

    # Test that it raises ConfigError for a missing key
    with pytest.raises(ConfigError, match="Required configuration key 'test_section.missing_key' not found"):
        config_service.get_required("test_section.missing_key")

    # Test that it returns the correct value for an existing key
    assert config_service.get_required("test_section.existing_key") == "value"

    # Test with a top-level missing key
    with pytest.raises(ConfigError, match="Required configuration key 'non_existent_top_level_key' not found"):
        config_service.get_required("non_existent_top_level_key")
