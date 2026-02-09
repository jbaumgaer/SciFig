import pytest
from src.models.plots.plot_properties import PlotMapping

class TestPlotMapping:
    def test_plot_mapping_initialization_defaults(self):
        """
        Test that PlotMapping initializes with default None for x and empty list for y.
        """
        mapping = PlotMapping(x=None, y=[])
        assert mapping.x is None
        assert mapping.y == []

    def test_plot_mapping_initialization_with_values(self):
        """
        Test that PlotMapping initializes correctly with provided values.
        """
        mapping = PlotMapping(x="column_A", y=["column_B", "column_C"])
        assert mapping.x == "column_A"
        assert mapping.y == ["column_B", "column_C"]

    @pytest.mark.parametrize("data, expected_x, expected_y", [
        ({"x": "new_col_X", "y": ["new_col_Y1", "new_col_Y2"]}, "new_col_X", ["new_col_Y1", "new_col_Y2"]),
        ({"x": "only_x"}, "only_x", ["initial_y"]),
        ({"y": ["only_y1", "only_y2"]}, "initial_x", ["only_y1", "only_y2"]),
        ({}, "initial_x", ["initial_y"]),
    ])
    def test_plot_mapping_update_from_dict_full_and_partial(self, data, expected_x, expected_y):
        """
        Test that update_from_dict correctly updates x and y, both fully and partially.
        """
        mapping = PlotMapping(x="initial_x", y=["initial_y"])
        mapping.update_from_dict(data)
        assert mapping.x == expected_x
        assert mapping.y == expected_y

    def test_plot_mapping_update_from_dict_ignore_unknown_keys(self):
        """
        Test that update_from_dict ignores properties not defined in PlotMapping.
        """
        mapping = PlotMapping(x="col_A", y=["col_B"])
        data = {"unknown_key": "some_value", "x": "new_col_A"}
        mapping.update_from_dict(data)
        assert mapping.x == "new_col_A"
        assert mapping.y == ["col_B"]  # y should remain unchanged
        assert not hasattr(mapping, "unknown_key")

    def test_plot_mapping_update_from_dict_non_dict_values_for_attributes(self):
        """
        Test that update_from_dict assigns non-dict values directly.
        """
        mapping = PlotMapping(x="old_x", y=["old_y"])
        data = {"x": 123, "y": "single_string"}
        mapping.update_from_dict(data)
        assert mapping.x == 123
        assert mapping.y == "single_string"
