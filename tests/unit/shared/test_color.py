import pytest
from src.shared.color import Color

class TestColor:
    """Unit tests for the Color value object."""

    def test_initialization(self):
        c = Color(1.0, 0.5, 0.0, 1.0)
        assert c.r == 1.0
        assert c.g == 0.5
        assert c.b == 0.0
        assert c.a == 1.0

    def test_validation_out_of_range(self):
        with pytest.raises(ValueError, match="Color component 'r' must be between 0 and 1"):
            Color(1.1, 0, 0, 1.0)
        with pytest.raises(ValueError, match="Color component 'a' must be between 0 and 1"):
            Color(1.0, 0, 0, -0.1)

    def test_from_mpl_named(self):
        c = Color.from_mpl("red")
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0
        assert c.a == 1.0

    def test_from_hex(self):
        c = Color.from_hex("#ff0000")
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0
        assert c.a == 1.0

    def test_to_hex(self):
        c = Color(1.0, 0.0, 0.0, 1.0)
        # Using keep_alpha=True results in #ff0000ff
        assert c.to_hex() == "#ff0000ff"

    def test_with_alpha(self):
        c = Color(1.0, 1.0, 1.0, 1.0)
        c2 = c.with_alpha(0.5)
        assert c2.a == 0.5
        assert c2.r == 1.0

    def test_equality(self):
        c1 = Color(1, 0, 0, 1)
        c2 = Color.from_mpl("red")
        assert c1 == c2

    def test_unpacking(self):
        r, g, b, a = Color(1, 0.5, 0, 1)
        assert r == 1.0
        assert g == 0.5
        assert b == 0.0
        assert a == 1.0

    def test_immutability(self):
        c = Color(1, 1, 1)
        with pytest.raises(AttributeError):
            c.r = 0.5
