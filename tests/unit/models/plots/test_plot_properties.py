import pytest
from src.models.plots.plot_properties import (
    FontProperties,
    TextProperties,
    LineProperties,
    PatchProperties,
    ScalarMappableProperties,
    TickProperties,
    PlotProperties,
    Cartesian2DProperties,
    PolarProperties,
    LineArtistProperties,
    ScatterArtistProperties,
    BarArtistProperties,
    ImageArtistProperties,
    MeshArtistProperties,
    ContourArtistProperties,
    HistogramArtistProperties,
    StairArtistProperties,
)
from src.models.plots.plot_types import (
    CoordinateSystem,
    ArtistType,
    TickDirection,
)


class TestPlotPropertiesHierarchy:
    """Tests the serialization and reconstruction of the PlotProperties tree."""

    def test_font_properties_serialization(self, sample_font):
        """Tests serialization of leaf FontProperties dataclass."""
        from dataclasses import asdict
        d = asdict(sample_font)
        assert d["family"] == "Arial"
        assert d["size"]["value"] == 10.0
        assert d["size"]["unit"].value == "pt"

    def test_plot_properties_round_trip(self, sample_plot_properties):
        """Tests that a full PlotProperties tree can be serialized and perfectly reconstructed."""
        data = sample_plot_properties.to_dict()
        
        # Verify serialization structure
        assert "coords" in data
        assert "artists" in data
        assert data["coords"]["coord_type"] == CoordinateSystem.CARTESIAN_2D.value

        # Reconstruct
        reconstructed = PlotProperties.from_dict(data)
        
        assert isinstance(reconstructed, PlotProperties)
        assert isinstance(reconstructed.coords, Cartesian2DProperties)
        assert len(reconstructed.artists) == 1
        assert isinstance(reconstructed.artists[0], LineArtistProperties)
        assert reconstructed.artists[0].visuals.linewidth.value == 1.0

    def test_polymorphic_coords_dispatch(self, sample_plot_properties):
        """Tests that from_dict correctly chooses the Coordinate class based on coord_type."""
        data = sample_plot_properties.to_dict()
        
        # Change to Polar
        data["coords"] = {
            "coord_type": "polar",
            "theta_axis": data["coords"]["xaxis"], # Reuse axis data for simplicity
            "r_axis": data["coords"]["yaxis"],
            "spine": data["coords"]["spines"]["left"]
        }
        
        reconstructed = PlotProperties.from_dict(data)
        assert isinstance(reconstructed.coords, PolarProperties)
        assert reconstructed.coords.coord_type == CoordinateSystem.POLAR

    def test_polymorphic_artists_dispatch(self, sample_plot_properties):
        """Tests that from_dict correctly chooses the Artist class based on artist_type."""
        data = sample_plot_properties.to_dict()
        
        # Add a Scatter artist
        data["artists"].append({
            "artist_type": "scatter",
            "visible": True,
            "zorder": 2,
            "visuals": data["artists"][0]["visuals"] # Reuse line visuals
        })
        
        reconstructed = PlotProperties.from_dict(data)
        assert len(reconstructed.artists) == 2
        assert isinstance(reconstructed.artists[0], LineArtistProperties)
        assert isinstance(reconstructed.artists[1], ScatterArtistProperties)

    def test_from_dict_sparse_fallback(self, sample_plot_properties):
        """Tests that from_dict provides an empty artist list if missing."""
        full_data = sample_plot_properties.to_dict()
        data = {
            "titles": full_data["titles"],
            "coords": full_data["coords"],
            "legend": {},
            # missing artists
        }
        reconstructed = PlotProperties.from_dict(data)
        assert reconstructed.artists == []

    def test_tick_direction_enum_parsing(self):
        """Tests that string values from JSON are correctly converted to Enums."""
        from src.models.plots.plot_properties import _from_dict_recursive
        data = {
            "major_size": 1.0,
            "minor_size": 0.5,
            "major_width": 1.0,
            "minor_width": 0.5,
            "major_pad": 1.0,
            "minor_pad": 1.0,
            "direction": "in",
            "color": "black",
            "labelcolor": "black",
            "labelsize": 10,
            "minor_visible": True,
            "minor_ndivs": 2
        }
        ticks = _from_dict_recursive(TickProperties, data)
        assert ticks.direction == TickDirection.IN

    def test_recursive_loader_ignores_unknown_keys(self, sample_font):
        """Tests that extra keys in the dictionary do not crash the reconstruction."""
        from src.models.plots.plot_properties import _from_dict_recursive
        from dataclasses import asdict
        data = asdict(sample_font)
        data["extra_garbage_key"] = "should be ignored"
        
        reconstructed = _from_dict_recursive(FontProperties, data)
        assert isinstance(reconstructed, FontProperties)
        assert not hasattr(reconstructed, "extra_garbage_key")

    @pytest.mark.parametrize("artist_type_str, expected_class_name", [
        ("line", "LineArtistProperties"),
        ("scatter", "ScatterArtistProperties"),
        ("bar", "BarArtistProperties"),
        ("image", "ImageArtistProperties"),
        ("mesh", "MeshArtistProperties"),
        ("contour", "ContourArtistProperties"),
        ("histogram", "HistogramArtistProperties"),
        ("stair", "StairArtistProperties"),
    ])
    def test_polymorphic_artist_resolution_all_types(self, sample_plot_properties, artist_type_str, expected_class_name):
        """Tests that all known artist type strings resolve to their correct class."""
        data = sample_plot_properties.to_dict()
        
        # Define visuals based on type
        line_visuals = {"linewidth": 1.0, "linestyle": "-", "color": "blue", "marker": "o", "markerfacecolor": "red", "markeredgecolor": "black", "markeredgewidth": 0.5, "markersize": 5.0}
        patch_visuals = {"facecolor": "blue", "edgecolor": "black", "linewidth": 1.0, "force_edgecolor": False}
        scalar_visuals = {"cmap": "viridis", "norm_min": 0.0, "norm_max": 1.0, "has_colorbar": True}

        visuals_map = {
            "line": line_visuals,
            "scatter": line_visuals,
            "stair": line_visuals,
            "bar": patch_visuals,
            "histogram": patch_visuals,
            "image": scalar_visuals,
            "mesh": scalar_visuals,
            "contour": scalar_visuals,
        }

        artist_dict = {
            "artist_type": artist_type_str,
            "visible": True,
            "zorder": 1,
            "visuals": visuals_map[artist_type_str],
        }

        # Add type-specific mandatory fields
        if artist_type_str == "bar":
            artist_dict.update({"width": 0.8, "align": "center"})
        elif artist_type_str == "contour":
            artist_dict.update({"levels": 5, "filled": True, "linewidth": 1.0})
        elif artist_type_str == "histogram":
            artist_dict.update({"bins": 10, "density": False, "cumulative": False})
        elif artist_type_str == "stair":
            artist_dict.update({"baseline": 0.0, "fill": False})

        data["artists"] = [artist_dict]
        
        reconstructed = PlotProperties.from_dict(data)
        assert type(reconstructed.artists[0]).__name__ == expected_class_name

    def test_partial_reconstruction_fails_strictly(self):
        """
        Documents the strict nature of the current loader: 
        Missing mandatory positional arguments should raise TypeError.
        """
        from src.models.plots.plot_properties import _from_dict_recursive
        data = {"family": "Arial"} # Missing size, weight, etc.
        with pytest.raises(TypeError):
            _from_dict_recursive(FontProperties, data)

    def test_from_dict_reconstructs_tuples(self, sample_plot_properties):
        """Regression test for tuple reconstruction from JSON-derived lists."""
        data = sample_plot_properties.to_dict()
        
        # Simulate JSON behavior: scientific_limits and limits are lists in JSON
        data["coords"]["xaxis"]["scientific_limits"] = [-3, 4]
        data["coords"]["xaxis"]["limits"] = [1.5, 8.5]
        
        reconstructed = PlotProperties.from_dict(data)
        
        # VERIFY: They are reconstructed as TUPLES, not lists
        assert isinstance(reconstructed.coords.xaxis.scientific_limits, tuple)
        assert reconstructed.coords.xaxis.scientific_limits == (-3, 4)
        
        assert isinstance(reconstructed.coords.xaxis.limits, tuple)
        assert reconstructed.coords.xaxis.limits == (1.5, 8.5)
