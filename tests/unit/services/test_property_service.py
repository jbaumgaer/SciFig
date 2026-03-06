import pytest
from src.services.property_service import PropertyService
from src.models.plots.plot_types import TickDirection
from src.models.plots.plot_properties import ScatterArtistProperties, LineProperties


@pytest.fixture
def service():
    """Provides a real, stateless PropertyService instance."""
    return PropertyService()


@pytest.fixture
def props(sample_plot_properties):
    """Provides a fully initialized PlotProperties tree from conftest."""
    return sample_plot_properties


class TestPropertyService:
    """
    Unit tests for PropertyService using the project's actual domain models.
    Verifies navigation, type-safe modification, and wildcard resolution
    within the PlotProperties hierarchy.
    """

    # --- Property Retrieval (get_value) ---

    def test_get_value_navigates_nested_dataclasses(self, service, props):
        """Tests accessing leaf attributes in a deep dataclass hierarchy."""
        # path: coords (Cartesian2DProperties) -> xaxis (AxisProperties) -> margin (float)
        assert service.get_value(props, "coords.xaxis.margin") == 0.05
        
        # path: titles (dict) -> center (TextProperties) -> text (str)
        assert service.get_value(props, "titles.center.text") == "Test"

    def test_get_value_navigates_lists_and_dicts(self, service, props):
        """Tests accessing elements within lists and dictionaries by index/key."""
        # path: artists (list) -> 0 (LineArtistProperties) -> visible (bool)
        assert service.get_value(props, "artists.0.visible") is True
        
        # path: coords -> spines (dict) -> left (SpineProperties) -> visible (bool)
        assert service.get_value(props, "coords.spines.left.visible") is True

    # --- Property Modification (set_value) ---

    def test_set_value_updates_primitive_attributes(self, service, props):
        """Tests direct updates to primitive fields (int, float, bool, str)."""
        service.set_value(props, "coords.xaxis.margin", 0.15)
        assert props.coords.xaxis.margin == 0.15
        
        service.set_value(props, "artists.0.visible", False)
        assert props.artists[0].visible is False

    def test_set_value_with_float_coercion(self, service, props):
        """Verifies that string inputs from UI are coerced to float where expected."""
        # margin is a float in AxisProperties
        service.set_value(props, "coords.xaxis.margin", "0.25")
        assert props.coords.xaxis.margin == 0.25
        assert isinstance(props.coords.xaxis.margin, float)

    def test_set_value_with_enum_coercion(self, service, props):
        """Verifies that string inputs are coerced to the correct Enum member."""
        # direction is a TickDirection Enum in TickProperties
        service.set_value(props, "coords.xaxis.ticks.direction", "in")
        assert props.coords.xaxis.ticks.direction == TickDirection.IN

    # --- Wildcard Resolution (resolve_concrete_paths) ---

    def test_resolve_concrete_paths_with_list_wildcard(self, service, props):
        """Tests expanding '*' wildcards in lists (e.g., all artists)."""
        # Add a second artist for testing
        props.artists.append(ScatterArtistProperties(
            visible=True, zorder=2, visuals=LineProperties(1.0, "-", "red", "o", "red", "black", 0.5, 5.0)
        ))
        
        paths = service.resolve_concrete_paths(props, "artists.*.visible")
        
        assert len(paths) == 2
        assert "artists.0.visible" in paths
        assert "artists.1.visible" in paths

    def test_resolve_concrete_paths_with_dict_wildcard(self, service, props):
        """Tests expanding '*' wildcards in dictionaries (e.g., all spines)."""
        paths = service.resolve_concrete_paths(props, "coords.spines.*.visible")
        
        # sample_plot_properties in conftest defines 'left' and 'bottom' spines
        assert "coords.spines.left.visible" in paths
        assert "coords.spines.bottom.visible" in paths
        assert len(paths) == 2

    # --- Error Handling & Edge Cases ---

    def test_get_value_raises_on_invalid_path(self, service, props):
        """Verifies standard Python exceptions for malformed or non-existent paths."""
        with pytest.raises(AttributeError):
            service.get_value(props, "coords.xaxis.non_existent")
            
        with pytest.raises(KeyError):
            service.get_value(props, "coords.spines.top") # Only left/bottom in fixture
            
        with pytest.raises(IndexError):
            service.get_value(props, "artists.5")

    def test_coerce_value_invalid_enum_returns_original(self, service):
        """Ensures that invalid Enum strings do not crash the service."""
        # Should return the original string if it doesn't match an Enum member
        val = service._coerce_value("invalid_direction", TickDirection)
        assert val == "invalid_direction"

    def test_set_value_on_dictionary_leaf(self, service, props):
        """Verifies that the service can set values directly into dictionary leaves."""
        service.set_value(props, "titles.left.text", "New Left Title")
        assert props.titles["left"].text == "New Left Title"
