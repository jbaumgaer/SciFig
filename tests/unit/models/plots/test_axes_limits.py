import pytest
from src.models.plots.plot_properties import AxesLimits

class TestAxesLimits:
    def test_axes_limits_initialization_defaults(self):
        """
        Test that AxesLimits initializes with default (None, None) for xlim and ylim.
        """
        limits = AxesLimits(xlim=(None, None), ylim=(None, None))
        assert limits.xlim == (None, None)
        assert limits.ylim == (None, None)

    def test_axes_limits_initialization_with_values(self):
        """
        Test that AxesLimits initializes correctly with provided values.
        """
        limits = AxesLimits(xlim=(0.0, 100.0), ylim=(-5.0, 5.0))
        assert limits.xlim == (0.0, 100.0)
        assert limits.ylim == (-5.0, 5.0)

    @pytest.mark.parametrize("data, expected_xlim, expected_ylim", [
        ({"xlim": (10.0, 90.0), "ylim": (-10.0, 10.0)}, (10.0, 90.0), (-10.0, 10.0)),
        ({"xlim": (5.0, 95.0)}, (5.0, 95.0), (0.0, 1.0)),
        ({"ylim": (-1.0, 1.0)}, (0.0, 1.0), (-1.0, 1.0)),
        ({}, (0.0, 1.0), (0.0, 1.0)),
    ])
    def test_axes_limits_update_from_dict_full_and_partial(self, data, expected_xlim, expected_ylim):
        """
        Test that update_from_dict correctly updates xlim and ylim, both fully and partially.
        """
        limits = AxesLimits(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
        limits.update_from_dict(data)
        assert limits.xlim == expected_xlim
        assert limits.ylim == expected_ylim

    def test_axes_limits_update_from_dict_ignore_unknown_keys(self):
        """
        Test that update_from_dict ignores properties not defined in AxesLimits.
        """
        limits = AxesLimits(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
        data = {"unknown_key": "some_value", "xlim": (10.0, 20.0)}
        limits.update_from_dict(data)
        assert limits.xlim == (10.0, 20.0)
        assert limits.ylim == (0.0, 1.0) # ylim should remain unchanged
        assert not hasattr(limits, "unknown_key")
