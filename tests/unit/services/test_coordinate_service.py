import pytest
from src.services.coordinate_service import CoordinateService
from src.shared.types import CoordinateSpace

class TestCoordinateService:

    def test_to_canonical_conversions(self):
        """Verifies unit to CM mapping."""
        # 1 inch = 2.54 cm
        assert CoordinateService.to_canonical(1.0, "inch") == pytest.approx(2.54)
        assert CoordinateService.to_canonical(1.0, "in") == pytest.approx(2.54)
        
        # 10 mm = 1.0 cm
        assert CoordinateService.to_canonical(10.0, "mm") == pytest.approx(1.0)
        
        # 72 points = 1 inch = 2.54 cm
        assert CoordinateService.to_canonical(72.0, "pt") == pytest.approx(2.54)

    def test_from_canonical_conversions(self):
        """Verifies CM to unit mapping."""
        assert CoordinateService.from_canonical(2.54, "inch") == pytest.approx(1.0)
        assert CoordinateService.from_canonical(1.0, "mm") == pytest.approx(10.0)
        assert CoordinateService.from_canonical(2.54, "pt") == pytest.approx(72.0)

    def test_physical_to_fractional_fig(self):
        """Tests CM -> 0-1 (Figure) transformation."""
        # 10cm on a 20cm figure should be 0.5
        val = CoordinateService.transform_value(
            10.0, 
            from_space=CoordinateSpace.PHYSICAL,
            to_space=CoordinateSpace.FRACTIONAL_FIG,
            figure_size_cm=20.0
        )
        assert val == pytest.approx(0.5)

    def test_fractional_fig_to_physical(self):
        """Tests 0-1 (Figure) -> CM transformation."""
        # 0.25 on a 40cm figure should be 10cm
        val = CoordinateService.transform_value(
            0.25, 
            from_space=CoordinateSpace.FRACTIONAL_FIG,
            to_space=CoordinateSpace.PHYSICAL,
            figure_size_cm=40.0
        )
        assert val == pytest.approx(10.0)

    def test_physical_to_display_px(self):
        """Tests CM -> Pixels transformation."""
        # 5cm on a 10cm figure where canvas is 1000px should be 500px
        val = CoordinateService.transform_value(
            5.0,
            from_space=CoordinateSpace.PHYSICAL,
            to_space=CoordinateSpace.DISPLAY_PX,
            figure_size_cm=10.0,
            canvas_size_px=1000.0
        )
        assert val == pytest.approx(500.0)

    def test_display_px_to_physical(self):
        """Tests Pixels -> CM transformation."""
        # 250px on a 1000px canvas with a 20cm figure size should be 5cm
        val = CoordinateService.transform_value(
            250.0,
            from_space=CoordinateSpace.DISPLAY_PX,
            to_space=CoordinateSpace.PHYSICAL,
            figure_size_cm=20.0,
            canvas_size_px=1000.0
        )
        assert val == pytest.approx(5.0)

    def test_fractional_local_transformations(self):
        """Tests transformations involving local parent space (e.g. subplots)."""
        # 0.2 gap relative to a 10cm subplot should be 2cm physical
        val = CoordinateService.transform_value(
            0.2,
            from_space=CoordinateSpace.FRACTIONAL_LOCAL,
            to_space=CoordinateSpace.PHYSICAL,
            parent_size_cm=10.0
        )
        assert val == pytest.approx(2.0)
        
        # 3cm physical transformed to fractional local of a 12cm parent should be 0.25
        val = CoordinateService.transform_value(
            3.0,
            from_space=CoordinateSpace.PHYSICAL,
            to_space=CoordinateSpace.FRACTIONAL_LOCAL,
            parent_size_cm=12.0
        )
        assert val == pytest.approx(0.25)

    def test_error_on_missing_context(self):
        """Verifies that missing required context raises ValueError."""
        with pytest.raises(ValueError, match="figure_size_cm required"):
            CoordinateService.transform_value(
                0.5, 
                from_space=CoordinateSpace.FRACTIONAL_FIG, 
                to_space=CoordinateSpace.PHYSICAL
            )
            
        with pytest.raises(ValueError, match="canvas_size_px"):
            CoordinateService.transform_value(
                10.0, 
                from_space=CoordinateSpace.PHYSICAL, 
                to_space=CoordinateSpace.DISPLAY_PX,
                figure_size_cm=20.0
                # canvas_size_px missing
            )

    def test_format_for_display(self):
        """Verifies display formatting logic."""
        # 2.54 cm is 1.000 inches
        assert CoordinateService.format_for_display(2.54, "inch", precision=3) == "1.000"
        # 1.0 cm is 10.00 mm
        assert CoordinateService.format_for_display(1.0, "mm", precision=2) == "10.00"
