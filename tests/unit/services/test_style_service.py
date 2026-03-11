import pytest
from unittest.mock import MagicMock, ANY
import matplotlib as mpl
from src.services.style_service import StyleService, ThemeIncompleteError
from src.models.plots.plot_types import ArtistType, TickDirection, SpinePosition, AxisKey
from src.models.plots.plot_properties import PlotProperties, LineArtistProperties, Cartesian3DProperties, PolarProperties


@pytest.fixture
def style_service(mock_event_aggregator):
    """Provides a StyleService instance with a mocked EventAggregator."""
    return StyleService(event_aggregator=mock_event_aggregator)


@pytest.fixture
def valid_style_file(tmp_path):
    """Creates a temporary .mplstyle file containing all REQUIRED_KEYS with valid data."""
    style_content = ""
    for key in StyleService.REQUIRED_KEYS:
        # Provide valid values for Matplotlib's parser and our StyleService
        if "panecolor" in key:
            val = "(0.1, 0.1, 0.1, 0.5)"
        elif "color" in key:
            val = "black"
        elif "linewidth" in key or "width" in key or "size" in key or "pad" in key or "margin" in key or "alpha" in key:
            val = "1.0"
        elif "linestyle" in key:
            val = "-"
        elif "marker" in key:
            val = "o"
        elif "direction" in key:
            val = "out"
        elif "visible" in key or "axisbelow" in key or "useoffset" in key or "grid" in key or "force_edgecolor" in key:
            val = "True"
        elif "family" in key:
            val = "sans-serif"
        elif "style" in key or "variant" in key or "weight" in key or "stretch" in key:
            val = "normal"
        elif "prop_cycle" in key:
            val = "cycler('color', ['red', 'blue'])"
        elif "autolimit_mode" in key:
            val = "data"
        elif "limits" in key:
            val = "-4, 5"
        elif "offset_threshold" in key or "ndivs" in key or "levels" in key:
            val = "2"
        elif "bins" in key:
            val = "auto"
        elif "cmap" in key:
            val = "viridis"
        else:
            val = "0"
        style_content += f"{key}: {val}\n"
    
    style_path = tmp_path / "valid.mplstyle"
    style_path.write_text(style_content)
    return str(style_path)


@pytest.fixture
def incomplete_style_file(tmp_path):
    """Creates a temporary .mplstyle file missing some required keys."""
    style_path = tmp_path / "incomplete.mplstyle"
    style_path.write_text("font.size: 10\n")
    return str(style_path)


class TestStyleService:
    """
    Unit tests for StyleService.
    Verifies theme loading, property tree generation, and deep hydration.
    """

    # --- Style Loading & Validation ---

    def test_load_style_success(self, style_service, valid_style_file):
        """Verifies that a complete style file is loaded successfully."""
        style_service.load_style(valid_style_file)
        assert style_service._current_style["font.size"] == 1.0
        assert style_service._current_style["image.cmap"] == "viridis"

    def test_load_style_fails_on_incomplete_theme(self, style_service, incomplete_style_file):
        """Verifies that ThemeIncompleteError is raised when keys are missing."""
        with pytest.raises(ThemeIncompleteError, match="missing required keys"):
            style_service.load_style(incomplete_style_file)

    # --- Property Tree Generation ---

    def test_create_themed_properties_line(self, style_service, valid_style_file):
        """Tests generation of a themed PlotProperties tree for a Line plot."""
        style_service.load_style(valid_style_file)
        props = style_service.create_themed_properties(ArtistType.LINE)
        
        assert isinstance(props, PlotProperties)
        assert len(props.artists) == 1
        assert isinstance(props.artists[0], LineArtistProperties)
        assert props.coords.coord_type.value == "cartesian_2d"

    def test_create_themed_properties_surface_3d(self, style_service, valid_style_file):
        """Tests generation of a 3D themed property tree with smart inheritance."""
        style_service.load_style(valid_style_file)
        props = style_service.create_themed_properties(ArtistType.SURFACE)
        
        assert isinstance(props.coords, Cartesian3DProperties)
        assert props.coords.zaxis is not None
        # Verify Z pane color was parsed correctly
        assert props.coords.pane_colors[AxisKey.Z] == (0.1, 0.1, 0.1, 0.5)
        # Verify inheritance: ztick should have inherited from xtick in fixture
        assert props.coords.zaxis.ticks.major_size == 1.0

    def test_create_themed_properties_polar(self, style_service, valid_style_file):
        """Tests generation of a Polar themed property tree."""
        style_service.load_style(valid_style_file)
        props = style_service.create_themed_properties(ArtistType.POLAR_LINE)
        
        assert isinstance(props.coords, PolarProperties)
        assert props.coords.theta_axis is not None
        assert props.coords.r_axis is not None

    # --- Hydration Logic ---

    def test_hydrate_merges_nested_dataclasses(self, style_service, sample_plot_properties):
        """Tests deep merging of a sparse dict into a PlotProperties tree."""
        overrides = {
            "coords": {
                "xaxis": {"margin": 0.2},
                "spines": {"left": {"visible": False}}
            }
        }
        
        style_service.hydrate(sample_plot_properties, overrides)
        
        assert sample_plot_properties.coords.xaxis.margin == 0.2
        assert sample_plot_properties.coords.spines[SpinePosition.LEFT].visible is False
        assert sample_plot_properties._version == 2 # Initial was 1 in fixture

    def test_hydrate_resolves_enums(self, style_service, sample_plot_properties):
        """Tests that hydration correctly resolves Enum members from strings."""
        overrides = {
            "coords": {
                "xaxis": {"ticks": {"direction": "in"}}
            }
        }
        
        style_service.hydrate(sample_plot_properties, overrides)
        assert sample_plot_properties.coords.xaxis.ticks.direction == TickDirection.IN

    def test_hydrate_list_of_artists(self, style_service, sample_plot_properties, valid_style_file):
        """Tests that hydrating 'artists' list re-initializes themed bases."""
        style_service.load_style(valid_style_file)
        overrides = {
            "artists": [
                {"artist_type": "scatter", "zorder": 10},
                {"artist_type": "line", "visuals": {"color": "red"}}
            ]
        }
        
        style_service.hydrate(sample_plot_properties, overrides)
        
        assert len(sample_plot_properties.artists) == 2
        assert sample_plot_properties.artists[0].artist_type == ArtistType.SCATTER
        assert sample_plot_properties.artists[0].zorder == 10
        assert sample_plot_properties.artists[1].visuals.color == "red"

    # --- Factory Methods ---

    def test_create_properties_from_sparse(self, style_service, valid_style_file):
        """Tests the high-level factory that creates a themed base and hydrates it."""
        style_service.load_style(valid_style_file)
        overrides = {
            "plot_type": "scatter",
            "coords": {"xaxis": {"margin": 0.5}}
        }
        
        props = style_service.create_properties_from_sparse(overrides)
        
        assert props.artists[0].artist_type == ArtistType.SCATTER
        assert props.coords.xaxis.margin == 0.5

    # --- Reactive Handlers ---

    def test_on_initialize_theme_requested(self, style_service, valid_style_file, mock_event_aggregator):
        """Verifies the reactive theme initialization handler."""
        style_service.load_style(valid_style_file)
        
        style_service._on_initialize_theme_requested("node_1", ArtistType.LINE)
        
        mock_event_aggregator.publish.assert_called_once_with(
            ANY, # Events.CHANGE_PLOT_NODE_PROPERTY_REQUESTED
            node_id="node_1",
            path="plot_properties",
            value=ANY # PlotProperties
        )

    def test_on_hydrate_properties_requested(self, style_service, valid_style_file, mock_event_aggregator):
        """Verifies the reactive hydration handler."""
        style_service.load_style(valid_style_file)
        overrides = {"artists": [{"artist_type": "bar"}]}
        
        style_service._on_hydrate_properties_requested("node_1", overrides)
        
        mock_event_aggregator.publish.assert_called_once()
        args, kwargs = mock_event_aggregator.publish.call_args
        assert kwargs["node_id"] == "node_1"
        assert kwargs["value"].artists[0].artist_type == ArtistType.BAR
