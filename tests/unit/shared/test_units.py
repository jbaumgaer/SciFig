import pytest
from src.shared.units import Unit, Dimension

class TestDimension:
    """Unit tests for the Dimension value object."""

    def test_initialization(self):
        d = Dimension(10.0, Unit.CM)
        assert d.value == 10.0
        assert d.unit == Unit.CM

    def test_conversions(self):
        # 1 inch = 2.54 cm
        d = Dimension(1.0, Unit.INCH)
        assert d.cm == pytest.approx(2.54)
        
        # 1 cm to points (72 pts / 2.54 cm per inch)
        d2 = Dimension(2.54, Unit.CM)
        assert d2.pt == pytest.approx(72.0)

    def test_to_unit(self):
        d = Dimension(72.0, Unit.PT)
        assert d.to_unit(Unit.INCH) == pytest.approx(1.0)
        assert d.to_unit(Unit.CM) == pytest.approx(2.54)

    def test_arithmetic_addition(self):
        d1 = Dimension(1.0, Unit.INCH) # 2.54 cm
        d2 = Dimension(1.0, Unit.CM)
        
        # Result inherits unit of d1 (Inch)
        res = d1 + d2
        assert res.unit == Unit.INCH
        assert res.cm == pytest.approx(3.54)

    def test_arithmetic_subtraction(self):
        d1 = Dimension(5.0, Unit.CM)
        d2 = Dimension(1.0, Unit.CM)
        res = d1 - d2
        assert res.value == 4.0

    def test_arithmetic_multiplication(self):
        d = Dimension(2.0, Unit.CM)
        res = d * 3
        assert res.value == 6.0
        assert res.unit == Unit.CM
        
        res2 = 2.5 * d
        assert res2.value == 5.0

    def test_arithmetic_division(self):
        # Dim / Scalar
        d = Dimension(10.0, Unit.CM)
        res = d / 2
        assert res.value == 5.0
        
        # Dim / Dim (Ratio)
        d1 = Dimension(1.0, Unit.INCH)
        d2 = Dimension(2.54, Unit.CM)
        assert (d1 / d2) == pytest.approx(1.0)

    def test_comparisons(self):
        d1 = Dimension(1.0, Unit.INCH)
        d2 = Dimension(2.0, Unit.CM)
        assert d1 > d2
        assert d2 < d1
        assert d1 >= Dimension(2.54, Unit.CM)

    def test_immutability(self):
        d = Dimension(1.0)
        with pytest.raises(AttributeError):
            d.value = 2.0
