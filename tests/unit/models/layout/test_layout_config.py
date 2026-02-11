import pytest
from src.models.layout.layout_config import Margins, Gutters, GridConfig, FreeConfig, LayoutMode
from src.shared.constants import LayoutMode

class TestLayoutConfig:
    def test_margins_init_requires_all_fields(self):
        """
        Test that Margins cannot be initialized without all required fields.
        """
        with pytest.raises(TypeError):
            Margins()
        with pytest.raises(TypeError):
            Margins(top=0.1)
        with pytest.raises(TypeError):
            Margins(top=0.1, bottom=0.1, left=0.1)
        
        # Test successful initialization
        margins = Margins(top=0.1, bottom=0.2, left=0.3, right=0.4)
        assert margins.top == 0.1
        assert margins.bottom == 0.2
        assert margins.left == 0.3
        assert margins.right == 0.4

    def test_margins_from_dict_requires_all_fields(self):
        """
        Test that Margins.from_dict requires all fields in the input dictionary.
        """
        with pytest.raises(KeyError):
            Margins.from_dict({"top": 0.1})
        with pytest.raises(KeyError):
            Margins.from_dict({"top": 0.1, "bottom": 0.1, "left": 0.1})

        # Test successful deserialization
        data = {"top": 0.1, "bottom": 0.2, "left": 0.3, "right": 0.4}
        margins = Margins.from_dict(data)
        assert margins.top == 0.1
        assert margins.bottom == 0.2
        assert margins.left == 0.3
        assert margins.right == 0.4

    def test_gutters_init_requires_all_fields(self):
        """
        Test that Gutters cannot be initialized without all required fields.
        """
        with pytest.raises(TypeError):
            Gutters()
        with pytest.raises(TypeError):
            Gutters(hspace=[0.1])
        
        # Test successful initialization
        gutters = Gutters(hspace=[0.1, 0.2], wspace=[0.3, 0.4])
        assert gutters.hspace == [0.1, 0.2]
        assert gutters.wspace == [0.3, 0.4]

    def test_gutters_from_dict_requires_all_fields(self):
        """
        Test that Gutters.from_dict requires all fields in the input dictionary.
        """
        with pytest.raises(KeyError):
            Gutters.from_dict({"hspace": [0.1]})
        
        # Test successful deserialization
        data = {"hspace": [0.1, 0.2], "wspace": [0.3, 0.4]}
        gutters = Gutters.from_dict(data)
        assert gutters.hspace == [0.1, 0.2]
        assert gutters.wspace == [0.3, 0.4]

    def test_gridconfig_init_requires_all_fields(self):
        """
        Test that GridConfig cannot be initialized without all required fields.
        """
        with pytest.raises(TypeError):
            GridConfig()
        
        # Minimal valid Margins and Gutters for testing
        minimal_margins = Margins(top=0.0, bottom=0.0, left=0.0, right=0.0)
        minimal_gutters = Gutters(hspace=[], wspace=[])

        # Test successful initialization
        config = GridConfig(
            rows=1,
            cols=1,
            row_ratios=[1.0],
            col_ratios=[1.0],
            margins=minimal_margins,
            gutters=minimal_gutters
        )
        assert config.rows == 1
        assert config.cols == 1
        assert config.mode == LayoutMode.GRID

    def test_gridconfig_from_dict_requires_all_fields(self):
        """
        Test that GridConfig.from_dict requires all fields in the input dictionary.
        """
        # Test missing top-level fields
        with pytest.raises(KeyError):
            GridConfig.from_dict({"rows": 1, "cols": 1}) # Missing ratios, margins, gutters

        # Test missing nested fields in margins
        minimal_gutters = Gutters(hspace=[], wspace=[])
        with pytest.raises(KeyError):
            GridConfig.from_dict({
                "rows": 1,
                "cols": 1,
                "row_ratios": [1.0],
                "col_ratios": [1.0],
                "margins": {"top": 0.1}, # Missing other margin fields
                "gutters": minimal_gutters.to_dict()
            })
        
        # Test missing nested fields in gutters
        minimal_margins = Margins(top=0.0, bottom=0.0, left=0.0, right=0.0)
        with pytest.raises(KeyError):
            GridConfig.from_dict({
                "rows": 1,
                "cols": 1,
                "row_ratios": [1.0],
                "col_ratios": [1.0],
                "margins": minimal_margins.to_dict(),
                "gutters": {"hspace": [0.1]} # Missing wspace
            })

        # Test successful deserialization
        data = {
            "mode": "grid",
            "rows": 2,
            "cols": 2,
            "row_ratios": [0.5, 0.5],
            "col_ratios": [0.3, 0.7],
            "margins": {"top": 0.1, "bottom": 0.1, "left": 0.1, "right": 0.1},
            "gutters": {"hspace": [0.05], "wspace": [0.05]},
        }
        config = GridConfig.from_dict(data)
        assert config.rows == 2
        assert config.cols == 2
        assert config.margins.top == 0.1
        assert config.gutters.hspace == [0.05]

    def test_freeconfig_from_dict(self):
        """
        Test that FreeConfig.from_dict works as expected (no changes needed for it).
        """
        config = FreeConfig.from_dict({"mode": "free_form"})
        assert config.mode == LayoutMode.FREE_FORM
