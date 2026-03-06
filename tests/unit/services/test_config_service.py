import pytest
from pathlib import Path
from src.services.config_service import ConfigService
from src.shared.exceptions import ConfigError
from src.shared.constants import IconPath


@pytest.fixture
def temp_config_file(tmp_path):
    """Provides a valid YAML config file."""
    config_content = """
    app_name: TestApp
    figure:
      default_width: 10.0
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
    """Provides a malformed YAML file."""
    config_content = """
    app_name: TestApp
    - this is invalid yaml
    """
    file = tmp_path / "invalid_config.yaml"
    file.write_text(config_content)
    return file


class TestConfigService:

    def test_initialization_success(self, temp_config_file):
        """Tests successful config loading."""
        service = ConfigService(temp_config_file)
        assert service._initialized is True
        assert service.get("app_name") == "TestApp"

    def test_initialization_file_not_found(self, caplog):
        """Verifies graceful handling of missing files."""
        service = ConfigService(Path("non_existent.yaml"))
        assert service._initialized is False
        assert service._config == {}
        assert "Configuration file not found" in caplog.text

    def test_initialization_invalid_yaml(self, invalid_config_file, caplog):
        """Verifies graceful handling of malformed YAML."""
        service = ConfigService(invalid_config_file)
        assert service._initialized is False
        assert "Error parsing YAML" in caplog.text

    def test_get_nested_keys(self, temp_config_file):
        """Tests retrieval of deeply nested values."""
        service = ConfigService(temp_config_file)
        assert service.get("figure.default_width") == 10.0
        assert service.get("figure.default_facecolor") == "red"

    def test_get_default_fallback(self, temp_config_file):
        """Verifies default return for missing keys."""
        service = ConfigService(temp_config_file)
        assert service.get("missing_key", "default") == "default"
        assert service.get("figure.missing_prop", 5.0) == 5.0

    def test_get_uninitialized_returns_default(self):
        """Ensures service returns default if not initialized."""
        service = ConfigService()
        assert service.get("any_key", "fallback") == "fallback"

    def test_get_required_success(self, temp_config_file):
        """Tests successful required key retrieval."""
        service = ConfigService(temp_config_file)
        assert service.get_required("app_name") == "TestApp"

    def test_get_required_missing_raises_error(self, temp_config_file):
        """Verifies ConfigError for missing required keys."""
        service = ConfigService(temp_config_file)
        with pytest.raises(ConfigError, match="not found"):
            service.get_required("missing_key")

    def test_get_required_uninitialized_raises_error(self):
        """Verifies ConfigError if service is uninitialized."""
        service = ConfigService()
        with pytest.raises(ConfigError, match="not initialized"):
            service.get_required("app_name")

    def test_icon_path_integration(self, temp_config_file):
        """Verifies that IconPath correctly uses the ConfigService."""
        service = ConfigService(temp_config_file)
        IconPath.set_config_service(service)
        
        # Paths are constructed as base_dir / icon_file
        # expected: test/icons/test_icon.svg
        expected = str(Path("test/icons") / "test_icon.svg")
        assert IconPath.get_path("tool_icons.test_tool") == expected
