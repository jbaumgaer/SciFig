import pytest
from dataclasses import FrozenInstanceError

from src.models.layout.layout_config import (
    FreeConfig,
    GridConfig,
    Gutters,
    LayoutConfig,
    Margins,
    NO_GUTTERS,
    NO_MARGINS,
)
from src.shared.constants import LayoutMode


class TestLayoutConfig:
    """Tests for the LayoutConfig hierarchy and its components."""

    # --- Margins Tests ---

    def test_margins_init(self):
        """Verifies Margins initialization and field access."""
        margins = Margins(top=0.1, bottom=0.2, left=0.3, right=0.4)
        assert margins.top == 0.1
        assert margins.bottom == 0.2
        assert margins.left == 0.3
        assert margins.right == 0.4

    def test_margins_immutability(self):
        """Ensures Margins is a frozen dataclass."""
        margins = Margins(0.1, 0.1, 0.1, 0.1)
        with pytest.raises(FrozenInstanceError):
            margins.top = 0.5

    def test_margins_serialization(self):
        """Verifies Margins to_dict and from_dict symmetry."""
        data = {"top": 0.1, "bottom": 0.2, "left": 0.3, "right": 0.4}
        margins = Margins.from_dict(data)
        assert margins.to_dict() == data

    def test_margins_from_dict_validation(self):
        """Ensures KeyError is raised on missing fields during deserialization."""
        with pytest.raises(KeyError):
            Margins.from_dict({"top": 0.1})

    # --- Gutters Tests ---

    def test_gutters_init(self):
        """Verifies Gutters initialization."""
        gutters = Gutters(hspace=[0.1, 0.2], wspace=[0.3, 0.4])
        assert gutters.hspace == [0.1, 0.2]
        assert gutters.wspace == [0.3, 0.4]

    def test_gutters_immutability(self):
        """Ensures Gutters is a frozen dataclass."""
        gutters = Gutters([], [])
        with pytest.raises(FrozenInstanceError):
            gutters.hspace = [0.1]

    def test_gutters_serialization(self):
        """Verifies Gutters to_dict and from_dict symmetry."""
        data = {"hspace": [0.1], "wspace": [0.2]}
        gutters = Gutters.from_dict(data)
        assert gutters.to_dict() == data

    # --- Polymorphic LayoutConfig Entry Point Tests ---

    def test_layout_config_from_dict_free(self):
        """Tests that LayoutConfig.from_dict correctly delegates to FreeConfig."""
        data = {"mode": "free_form"}
        config = LayoutConfig.from_dict(data)
        assert isinstance(config, FreeConfig)
        assert config.mode == LayoutMode.FREE_FORM

    def test_layout_config_from_dict_grid(self):
        """Tests that LayoutConfig.from_dict correctly delegates to GridConfig."""
        data = {
            "mode": "grid",
            "rows": 1,
            "cols": 1,
            "row_ratios": [1.0],
            "col_ratios": [1.0],
            "margins": {"top": 0, "bottom": 0, "left": 0, "right": 0},
            "gutters": {"hspace": [], "wspace": []},
        }
        config = LayoutConfig.from_dict(data)
        assert isinstance(config, GridConfig)
        assert config.mode == LayoutMode.GRID
        assert config.rows == 1

    def test_layout_config_from_dict_errors(self):
        """Tests error handling for invalid modes in LayoutConfig.from_dict."""
        with pytest.raises(ValueError, match="missing 'mode' field"):
            LayoutConfig.from_dict({})

        with pytest.raises(ValueError, match="'invalid_mode' is not a valid LayoutMode"):
            LayoutConfig.from_dict({"mode": "invalid_mode"})

    # --- Concrete Config Tests ---

    def test_free_config_init(self):
        """Verifies FreeConfig default state."""
        config = FreeConfig()
        assert config.mode == LayoutMode.FREE_FORM
        assert config.to_dict() == {"mode": "free_form"}

    def test_grid_config_init(self):
        """Verifies GridConfig initialization and attributes."""
        margins = Margins(0.1, 0.1, 0.1, 0.1)
        gutters = Gutters([0.05], [0.05])
        config = GridConfig(
            rows=2,
            cols=3,
            row_ratios=[0.5, 0.5],
            col_ratios=[0.33, 0.33, 0.34],
            margins=margins,
            gutters=gutters,
        )
        assert config.rows == 2
        assert config.cols == 3
        assert config.margins == margins
        assert config.gutters == gutters
        assert config.mode == LayoutMode.GRID

    def test_grid_config_serialization(self):
        """Verifies full GridConfig serialization round-trip."""
        data = {
            "mode": "grid",
            "rows": 2,
            "cols": 2,
            "row_ratios": [0.5, 0.5],
            "col_ratios": [0.5, 0.5],
            "margins": {"top": 0.1, "bottom": 0.1, "left": 0.1, "right": 0.1},
            "gutters": {"hspace": [0.05], "wspace": [0.05]},
        }
        config = GridConfig.from_dict(data)
        assert config.to_dict() == data

    def test_grid_config_immutability(self):
        """Ensures GridConfig is frozen."""
        config = GridConfig(1, 1, [1], [1], NO_MARGINS, NO_GUTTERS)
        with pytest.raises(FrozenInstanceError):
            config.rows = 5

    # --- Sentinels and Constants Tests ---

    def test_sentinel_values(self):
        """Verifies the predefined sentinel values for margins and gutters."""
        assert NO_MARGINS.top == 0.0
        assert NO_MARGINS.bottom == 0.0
        assert NO_GUTTERS.hspace == []
        assert NO_GUTTERS.wspace == []
