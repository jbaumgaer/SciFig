import pytest
from src.services.property_service import PropertyService
from src.models.plots.plot_types import TickDirection
from src.models.plots.plot_properties import ScatterArtistProperties, LineProperties, SpinePosition


@pytest.fixture
def service():
    """Provides a real, stateless PropertyService instance."""
    return PropertyService()


class TestPropertyService:
    """
    Unit tests for PropertyService using the project's actual domain models.
    Verifies navigation, type-safe modification, and wildcard resolution
    within the PlotProperties hierarchy.
    """

    # --- Property Retrieval (get_value) ---

    def test_get_value_navigates_nested_dataclasses(self, service, sample_plot_properties):
        """Tests accessing leaf attributes in a deep dataclass hierarchy."""
        # path: coords (Cartesian2DProperties) -> xaxis (AxisProperties) -> margin (float)
        assert service.get_value(sample_plot_properties, "coords.xaxis.margin") == 0.05
        
        # path: titles (dict) -> center (TextProperties) -> text (str)
        assert service.get_value(sample_plot_properties, "titles.center.text") == "Test"

    def test_get_value_navigates_lists_and_dicts(self, service, sample_plot_properties):
        """Tests accessing elements within lists and dictionaries by index/key."""
        # path: artists (list) -> 0 (LineArtistProperties) -> visible (bool)
        assert service.get_value(sample_plot_properties, "artists.0.visible") is True
        
        # path: coords -> spines (dict) -> left (SpineProperties) -> visible (bool)
        assert service.get_value(sample_plot_properties, "coords.spines.left.visible") is True

    # --- Property Modification (set_value) ---

    def test_set_value_updates_primitive_attributes(self, service, sample_plot_properties):
        """Tests direct updates to primitive fields (int, float, bool, str)."""
        new_root = service.set_value(sample_plot_properties, "coords.xaxis.margin", 0.15)
        assert new_root.coords.xaxis.margin == 0.15
        
        new_root = service.set_value(new_root, "artists.0.visible", False)
        assert new_root.artists[0].visible is False

    def test_set_value_with_float_coercion(self, service, sample_plot_properties):
        """Verifies that string inputs from UI are coerced to float where expected."""
        # margin is a float in AxisProperties
        new_root = service.set_value(sample_plot_properties, "coords.xaxis.margin", "0.25")
        assert new_root.coords.xaxis.margin == 0.25
        assert isinstance(new_root.coords.xaxis.margin, float)

    def test_set_value_with_enum_coercion(self, service, sample_plot_properties):
        """Verifies that string inputs are coerced to the correct Enum member."""
        # direction is a TickDirection Enum in TickProperties
        new_root = service.set_value(sample_plot_properties, "coords.xaxis.ticks.direction", "in")
        assert new_root.coords.xaxis.ticks.direction == TickDirection.IN

    # --- Wildcard Resolution (resolve_concrete_paths) ---

    def test_resolve_concrete_paths_with_list_wildcard(self, service, sample_plot_properties):
        """Tests expanding '*' wildcards in lists (e.g., all artists)."""
        from dataclasses import replace
        from src.shared.units import Unit, Dimension
        from src.shared.color import Color
        from src.shared.primitives import ZOrder
        
        # Add a second artist for testing (immutable replacement)
        new_artist = ScatterArtistProperties(
            visible=True, 
            zorder=ZOrder(2), 
            visuals=LineProperties(
                linewidth=Dimension(1.0, Unit.PT), 
                linestyle="-", 
                color=Color.from_mpl("red"), 
                marker="o", 
                markerfacecolor=Color.from_mpl("red"), 
                markeredgecolor=Color.from_mpl("black"), 
                markeredgewidth=Dimension(0.5, Unit.PT), 
                markersize=Dimension(5.0, Unit.PT)
            )
        )
        test_root = replace(sample_plot_properties, artists=sample_plot_properties.artists + [new_artist])
        
        paths = service.resolve_concrete_paths(test_root, "artists.*.visible")
        
        assert len(paths) == 2
        assert "artists.0.visible" in paths
        assert "artists.1.visible" in paths

    def test_resolve_concrete_paths_with_dict_wildcard(self, service, sample_plot_properties):
        """Tests expanding '*' wildcards in dictionaries (e.g., all spines)."""
        paths = service.resolve_concrete_paths(sample_plot_properties, "coords.spines.*.visible")
        
        # sample_plot_properties in conftest defines 'left' and 'bottom' spines
        assert "coords.spines.left.visible" in paths
        assert "coords.spines.bottom.visible" in paths
        assert len(paths) == 2

    # --- Error Handling & Edge Cases ---

    def test_get_value_raises_on_invalid_path(self, service, sample_plot_properties):
        """Verifies standard Python exceptions for malformed or non-existent paths."""
        with pytest.raises(AttributeError):
            service.get_value(sample_plot_properties, "coords.xaxis.non_existent")
            
        with pytest.raises(KeyError):
            service.get_value(sample_plot_properties, "coords.spines.top") # Only left/bottom in fixture
            
        with pytest.raises(IndexError):
            service.get_value(sample_plot_properties, "artists.5")

    def test_coerce_value_invalid_enum_returns_original(self, service):
        """Ensures that invalid Enum strings do not crash the service."""
        # Should return the original string if it doesn't match an Enum member
        val = service._coerce_value("invalid_direction", TickDirection)
        assert val == "invalid_direction"

    def test_set_value_on_dictionary_leaf(self, service, sample_plot_properties):
        """Verifies that the service can set values directly into dictionary leaves."""
        new_root = service.set_value(sample_plot_properties, "titles.left.text", "New Left Title")
        assert new_root.titles["left"].text == "New Left Title"
