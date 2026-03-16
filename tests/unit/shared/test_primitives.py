import pytest
from src.shared.primitives import Alpha, ZOrder

class TestAlpha:
    """Unit tests for the Alpha refined primitive."""

    def test_valid_alpha(self):
        a = Alpha(0.5)
        assert a == 0.5
        # It's a float
        assert a + 0.1 == pytest.approx(0.6)

    def test_invalid_alpha(self):
        with pytest.raises(ValueError, match="Alpha must be between 0.0 and 1.0"):
            Alpha(1.1)
        with pytest.raises(ValueError, match="Alpha must be between 0.0 and 1.0"):
            Alpha(-0.1)

class TestZOrder:
    """Unit tests for the ZOrder refined primitive."""

    def test_valid_zorder(self):
        z = ZOrder(10)
        assert z == 10
        # It's an int
        assert z + 1 == 11

    def test_invalid_zorder(self):
        with pytest.raises(ValueError, match="ZOrder must be non-negative"):
            ZOrder(-1)
