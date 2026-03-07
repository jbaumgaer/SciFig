import pytest
from src.shared.geometry import Rect

class TestRect:
    """Unit tests for the Rect geometric primitive."""

    def test_initialization(self):
        """Verifies basic attribute storage."""
        r = Rect(0.1, 0.2, 0.3, 0.4)
        assert r.x == pytest.approx(0.1)
        assert r.y == pytest.approx(0.2)
        assert r.width == pytest.approx(0.3)
        assert r.height == pytest.approx(0.4)

    def test_moved_by(self):
        """Verifies relative movement math."""
        r = Rect(0.1, 0.1, 0.2, 0.2)
        r2 = r.moved_by(0.05, -0.05)
        assert r2.x == pytest.approx(0.15)
        assert r2.y == pytest.approx(0.05)
        assert r2.width == pytest.approx(0.2)
        assert r2.height == pytest.approx(0.2)

    def test_scaled_by_bottom_right(self):
        """Verifies scaling from the top-left anchor (dragging bottom-right)."""
        r = Rect(0.1, 0.1, 0.2, 0.2)
        r2 = r.scaled_by("bottom-right", 0.05, -0.05)
        assert r2.width == pytest.approx(0.25)
        assert r2.y == pytest.approx(0.05)
        assert r2.height == pytest.approx(0.25)

    def test_scaled_by_top_left(self):
        """Verifies scaling from the bottom-right anchor (dragging top-left)."""
        r = Rect(0.1, 0.1, 0.2, 0.2)
        r2 = r.scaled_by("top-left", 0.05, 0.05)
        assert r2.x == pytest.approx(0.15)
        assert r2.width == pytest.approx(0.15)
        assert r2.height == pytest.approx(0.25)

    def test_scaling_min_threshold(self):
        """Ensures rectangles cannot be scaled to negative or zero dimensions."""
        r = Rect(0.1, 0.1, 0.2, 0.2)
        r2 = r.scaled_by("right", -0.5, 0)
        assert r2.width == pytest.approx(0.01)

    def test_contains(self):
        """Verifies point-in-rect hit testing."""
        r = Rect(0.1, 0.1, 0.2, 0.2)
        assert r.contains(0.2, 0.2)
        assert not r.contains(0.0, 0.0)
        assert not r.contains(0.4, 0.2)

    def test_intersects(self):
        """Verifies rectangle overlap detection."""
        r1 = Rect(0.1, 0.1, 0.2, 0.2)
        r2 = Rect(0.2, 0.2, 0.2, 0.2)
        r3 = Rect(0.5, 0.5, 0.1, 0.1)
        assert r1.intersects(r2)
        assert not r1.intersects(r3)

    def test_clamp_to_bounds(self):
        """Verifies boundary constraint logic."""
        r = Rect(-0.1, 1.2, 0.2, 0.2)
        r2 = r.clamp_to_bounds(0, 0, 1, 1)
        assert r2.x == pytest.approx(0.0)
        assert r2.y == pytest.approx(0.8)

    def test_center_logic(self):
        """Verifies center calculation and creation."""
        r = Rect.from_center(0.5, 0.5, 0.2, 0.2)
        assert r.x == pytest.approx(0.4)
        assert r.y == pytest.approx(0.4)
        assert r.get_center()[0] == pytest.approx(0.5)
        assert r.get_center()[1] == pytest.approx(0.5)

    def test_tuple_conversions(self):
        """Verifies round-trip conversion to standard tuple format."""
        t = (0.1, 0.2, 0.3, 0.4)
        r = Rect.from_tuple(t)
        assert r.to_tuple() == t
