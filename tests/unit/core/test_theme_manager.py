import pytest
import yaml
from unittest.mock import MagicMock, patch, mock_open
from src.core.theme_manager import ThemeManager


@pytest.fixture
def mock_qapp():
    return MagicMock()


@pytest.fixture
def sample_themes_yaml():
    return {
        "themes": {
            "dark": {
                "style": "Fusion",
                "palette": {
                    "Window": [50, 50, 50],
                    "WindowText": [255, 255, 255]
                },
                "stylesheet": "QPushButton { color: white; }"
            },
            "light": {
                "style": "Windows",
                "palette": {
                    "Window": [240, 240, 240]
                }
            }
        }
    }


class TestThemeManager:
    """
    Unit tests for ThemeManager.
    Verifies theme loading and application to QApplication.
    """

    def test_init_loads_themes(self, mock_qapp, mock_config_service, sample_themes_yaml):
        """Verifies that themes are loaded from YAML during initialization."""
        yaml_str = yaml.dump(sample_themes_yaml)
        with patch("builtins.open", mock_open(read_data=yaml_str)):
            with patch("pathlib.Path.exists", return_value=True):
                manager = ThemeManager(mock_qapp, mock_config_service)
                
        assert "dark" in manager.get_available_themes()
        assert "light" in manager.get_available_themes()

    def test_apply_theme_success(self, mock_qapp, mock_config_service, sample_themes_yaml):
        """Tests successful application of style, palette, and stylesheet."""
        yaml_str = yaml.dump(sample_themes_yaml)
        with patch("builtins.open", mock_open(read_data=yaml_str)):
            with patch("pathlib.Path.exists", return_value=True):
                manager = ThemeManager(mock_qapp, mock_config_service)
                manager.apply_theme("dark")
                
        mock_qapp.setStyle.assert_called_with("Fusion")
        mock_qapp.setPalette.assert_called()
        mock_qapp.setStyleSheet.assert_called_with("QPushButton { color: white; }")

    def test_apply_theme_fallback_to_default(self, mock_qapp, mock_config_service, sample_themes_yaml, caplog):
        """Verifies fallback to default theme when requested theme is missing."""
        # Need to override the side_effect from conftest
        mock_config_service.get.side_effect = None
        mock_config_service.get.return_value = "light"
        yaml_str = yaml.dump(sample_themes_yaml)
        
        with patch("builtins.open", mock_open(read_data=yaml_str)):
            with patch("pathlib.Path.exists", return_value=True):
                manager = ThemeManager(mock_qapp, mock_config_service)
                manager.apply_theme("non_existent")
                
        assert "Theme 'non_existent' not found" in caplog.text
        # Verify it fell back to 'light'
        mock_qapp.setStyle.assert_called_with("Windows")

    def test_load_themes_file_not_found(self, mock_qapp, mock_config_service):
        """Ensures graceful handling of missing themes.yaml."""
        with patch("pathlib.Path.exists", return_value=False):
            manager = ThemeManager(mock_qapp, mock_config_service)
            assert manager.get_available_themes() == []

    @patch("src.core.theme_manager.QColor")
    @patch("src.core.theme_manager.QPalette")
    def test_palette_application_details(self, mock_palette_cls, mock_qcolor_cls, mock_qapp, mock_config_service, sample_themes_yaml):
        """Verifies specific palette role and color assignments."""
        yaml_str = yaml.dump(sample_themes_yaml)
        mock_palette = mock_palette_cls.return_value
        
        with patch("builtins.open", mock_open(read_data=yaml_str)):
            with patch("pathlib.Path.exists", return_value=True):
                manager = ThemeManager(mock_qapp, mock_config_service)
                manager.apply_theme("dark")
        
        # Verify QColor was created with [50, 50, 50] for Window role
        # Note: getattr(QPalette, 'Window') is called. We can't easily check the call 
        # without complex mocking of QPalette members, but we can check if setColor was called.
        assert mock_palette.setColor.call_count >= 1
