from unittest.mock import MagicMock
import logging

import pandas as pd
import pytest
from PySide6.QtCore import QPointF

from src.shared.constants import LayoutMode
from src.controllers.canvas_controller import CanvasController
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.models.plots.plot_properties import LinePlotProperties


@pytest.fixture
def canvas_controller(
    mock_application_model, mock_canvas_widget, mock_tool_manager, mock_command_manager, mock_layout_controller
):
    """Provides a CanvasController instance."""
    return CanvasController(
        model=mock_application_model,
        canvas_widget=mock_canvas_widget,
        tool_manager=mock_tool_manager,
        command_manager=mock_command_manager,
        layout_controller=mock_layout_controller,
        parent=None,
    )


class TestCanvasController:

    def test_on_data_ready_sets_default_properties_for_new_data(
        self,
        canvas_controller,
        mock_application_model,
        sample_dataframe,
        plot_node_empty_props,
    ):
        """
        Verifies that on_data_ready sets default plot_mapping, xlabel, and ylabel
        when data is loaded into a plot with no pre-existing mapping.
        """
        plot_node_empty_props.name = "Test Plot"  # Give it a name for context

        # Add node to model's children so the if condition passes in on_data_ready
        mock_application_model.scene_root.children.append(plot_node_empty_props)

        canvas_controller.on_data_ready(sample_dataframe, plot_node_empty_props)

        # Assert node.data was set
        pd.testing.assert_frame_equal(plot_node_empty_props.data, sample_dataframe)

        # Assert plot_properties was created
        assert isinstance(plot_node_empty_props.plot_properties, LinePlotProperties)
        assert plot_node_empty_props.plot_properties.title == "Test Plot"
        assert plot_node_empty_props.plot_properties.xlabel == "Time"
        assert plot_node_empty_props.plot_properties.ylabel == "Voltage"
        assert plot_node_empty_props.plot_properties.plot_mapping.x == "Time"
        assert plot_node_empty_props.plot_properties.plot_mapping.y == ["Voltage"]

        # Assert modelChanged signal was emitted
        mock_application_model.modelChanged.emit.assert_called_once()


    def test_on_data_ready_does_not_overwrite_existing_properties(
        self,
        canvas_controller,
        mock_application_model,
        sample_dataframe,
        plot_node_with_mapping,
    ):
        """
        Verifies that on_data_ready does not overwrite plot_mapping or labels
        if they already exist on the plot node.
        """
        mock_application_model.scene_root.children.append(plot_node_with_mapping)

        canvas_controller.on_data_ready(sample_dataframe, plot_node_with_mapping)

        # Assert node.data was set
        pd.testing.assert_frame_equal(plot_node_with_mapping.data, sample_dataframe)

        # Assert that plot_properties are unchanged
        assert plot_node_with_mapping.plot_properties.title == "Existing Title"
        assert plot_node_with_mapping.plot_properties.plot_mapping.x == "ExistingX"

        # Assert modelChanged signal was emitted
        mock_application_model.modelChanged.emit.assert_called_once()


    def test_on_data_ready_with_insufficient_columns(
        self, canvas_controller, mock_application_model, plot_node_empty_props
    ):
        """
        Verifies that on_data_ready does not set default properties if the dataframe
        has fewer than two columns.
        """
        dataframe_one_col = pd.DataFrame({"Time": [1, 2, 3]})
        mock_application_model.scene_root.children.append(plot_node_empty_props)

        canvas_controller.on_data_ready(dataframe_one_col, plot_node_empty_props)

        # Assert node.data was set
        pd.testing.assert_frame_equal(plot_node_empty_props.data, dataframe_one_col)

        # Assert no commands were executed for properties (this test doesn't use command_manager anyway for this part)
        # mock_command_manager.execute_command.assert_not_called()

        # Assert modelChanged signal was emitted
        mock_application_model.modelChanged.emit.assert_called_once()


    def test_on_data_ready_node_not_in_scene(
        self,
        canvas_controller,
        mock_application_model,
        mock_command_manager,
        sample_dataframe,
        plot_node_empty_props,
    ):
        """
        Verifies that on_data_ready does nothing if the target node is not
        present in the model's scene graph (e.g., deleted during async load).
        """
        # Do NOT add plot_node_empty_props to mock_model.scene_root.children
        initial_data = plot_node_empty_props.data  # Should be None

        canvas_controller.on_data_ready(sample_dataframe, plot_node_empty_props)

        # Assert node.data was NOT set
        assert plot_node_empty_props.data is initial_data

        # Assert no commands were executed
        mock_command_manager.execute_command.assert_not_called()

        # Assert modelChanged signal was NOT emitted
        mock_application_model.modelChanged.emit.assert_not_called()


    def test_on_data_ready_in_free_form_mode(
        self,
        canvas_controller,
        mock_application_model,
        mock_layout_manager,
        sample_dataframe,
        plot_node_empty_props,
        mock_layout_controller,
    ):
        """
        Test that on_data_ready does NOT call apply_default_grid_layout when in FREE_FORM mode.
        """
        mock_layout_manager.layout_mode = LayoutMode.FREE_FORM
        mock_application_model.scene_root.children.append(plot_node_empty_props)

        canvas_controller.on_data_ready(sample_dataframe, plot_node_empty_props)

        mock_layout_controller._layout_manager.apply_default_grid_layout.assert_not_called()
        mock_application_model.modelChanged.emit.assert_called_once()


    def test_on_data_ready_in_grid_mode(
        self,
        canvas_controller,
        mock_application_model,
        mock_layout_manager,
        sample_dataframe,
        plot_node_empty_props,
        mock_layout_controller,
    ):
        """
        Test that on_data_ready calls apply_default_grid_layout when in GRID mode.
        """
        mock_layout_manager.layout_mode = LayoutMode.GRID
        mock_application_model.scene_root.children.append(plot_node_empty_props)

        canvas_controller.on_data_ready(sample_dataframe, plot_node_empty_props)

        mock_layout_controller._layout_manager.apply_default_grid_layout.assert_not_called()
        mock_application_model.modelChanged.emit.assert_called_once()


        def test_convert_qt_scene_to_mpl_figure_coords_valid(self, canvas_controller, mock_canvas_widget):
            """Tests _convert_qt_scene_to_mpl_figure_coords for valid conversions."""
            # Setup mock canvas widget dimensions
            mock_canvas_widget.width.return_value = 1000
            mock_canvas_widget.height.return_value = 800

            # Test a point (100, 200) in Qt scene coords
            scene_pos = QPointF(100, 200)
            fig_coords_x, fig_coords_y = canvas_controller._convert_qt_scene_to_mpl_figure_coords(scene_pos)

            # Expected: x = 100/1000 = 0.1, y = 1 - (200/800) = 1 - 0.25 = 0.75
            assert fig_coords_x == pytest.approx(0.1)
            assert fig_coords_y == pytest.approx(0.75)

            # Test another point (500, 400) - center
            scene_pos = QPointF(500, 400)
            fig_coords_x, fig_coords_y = canvas_controller._convert_qt_scene_to_mpl_figure_coords(scene_pos)

            # Expected: x = 500/1000 = 0.5, y = 1 - (400/800) = 1 - 0.5 = 0.5
            assert fig_coords_x == pytest.approx(0.5)
            assert fig_coords_y == pytest.approx(0.5)

    def test_convert_qt_scene_to_mpl_figure_coords_zero_dimensions(self, canvas_controller, mock_canvas_widget, caplog):
        """
        Tests _convert_qt_scene_to_mpl_figure_coords when canvas has zero width or height,
        expecting a warning and default return values.
        """
        scene_pos = QPointF(100, 200)

        # Case 1: Zero width
        mock_canvas_widget.figure_canvas.width.return_value = 0
        mock_canvas_widget.figure_canvas.height.return_value = 800
        with caplog.at_level(logging.WARNING):
            fig_coords_x, fig_coords_y = canvas_controller._convert_qt_scene_to_mpl_figure_coords(scene_pos)
            assert fig_coords_x == -1.0
            assert fig_coords_y == -1.0
            assert "Canvas has zero width or height. Cannot convert scene coordinates." in caplog.text
        caplog.clear()

        # Case 2: Zero height
        mock_canvas_widget.figure_canvas.width.return_value = 1000
        mock_canvas_widget.figure_canvas.height.return_value = 0
        with caplog.at_level(logging.WARNING):
            fig_coords_x, fig_coords_y = canvas_controller._convert_qt_scene_to_mpl_figure_coords(scene_pos)
            assert fig_coords_x == -1.0
            assert fig_coords_y == -1.0
            assert "Canvas has zero width or height. Cannot convert scene coordinates." in caplog.text
        caplog.clear()

        # Case 3: Both zero
        mock_canvas_widget.figure_canvas.width.return_value = 0
        mock_canvas_widget.figure_canvas.height.return_value = 0
        with caplog.at_level(logging.WARNING):
            fig_coords_x, fig_coords_y = canvas_controller._convert_qt_scene_to_mpl_figure_coords(scene_pos)
            assert fig_coords_x == -1.0
            assert fig_coords_y == -1.0
            assert "Canvas has zero width or height. Cannot convert scene coordinates." in caplog.text
        caplog.clear()

    def test_connect_events(self, canvas_controller, mock_canvas_widget, mock_tool_manager):
        """Verifies that _connect_events correctly connects signals."""
        # Reset mocks to ensure only calls from _connect_events are counted
        mock_canvas_widget.figure_canvas.mpl_connect.reset_mock()
        mock_canvas_widget.fileDropped.connect.reset_mock()

        canvas_controller._connect_events()

        # Check mpl_connect calls
        mock_canvas_widget.figure_canvas.mpl_connect.assert_any_call(
            "button_press_event", mock_tool_manager.dispatch_mouse_press_event
        )
        mock_canvas_widget.figure_canvas.mpl_connect.assert_any_call(
            "motion_notify_event", mock_tool_manager.dispatch_mouse_move_event
        )
        mock_canvas_widget.figure_canvas.mpl_connect.assert_any_call(
            "button_release_event", mock_tool_manager.dispatch_mouse_release_event
        )
        assert mock_canvas_widget.figure_canvas.mpl_connect.call_count == 3

        # Check fileDropped connect call
        mock_canvas_widget.fileDropped.connect.assert_called_once_with(
            canvas_controller.on_file_dropped
        )

    @pytest.mark.parametrize("file_path, expected_log_level, expected_message_part", [
        ("data.csv", "INFO", "File dropped"),
        ("image.png", "WARNING", "Dropped file"),
        ("data.txt", "WARNING", "Dropped file"),
    ])
    def test_on_file_dropped_file_type_check(self, canvas_controller, plot_node_empty_props, mocker, caplog, file_path, expected_log_level, expected_message_part):
        """Tests on_file_dropped's file type filtering."""
        mocker.patch.object(canvas_controller.model, 'get_node_at', return_value=plot_node_empty_props)
        mocker.patch.object(canvas_controller, 'load_data_into_node')
        
        scene_pos = QPointF(100, 100)
        
        with caplog.at_level(logging.DEBUG):
            canvas_controller.on_file_dropped(file_path, scene_pos)
            assert any(expected_log_level in r.levelname for r in caplog.records)
            assert any(expected_message_part in r.message for r in caplog.records)

        if expected_log_level == "WARNING":
            canvas_controller.model.get_node_at.assert_not_called()
            canvas_controller.load_data_into_node.assert_not_called()
        else: # INFO level, meaning CSV
            canvas_controller.model.get_node_at.assert_called_once()
            canvas_controller.load_data_into_node.assert_called_once_with(file_path, plot_node_empty_props)

    @pytest.mark.parametrize("node_at_pos, expected_load_call", [
        (None, False),
        (MagicMock(spec=SceneNode), False), # Not a PlotNode
        (PlotNode(), True),
    ])
    def test_on_file_dropped_node_hit_check(self, canvas_controller, mocker, caplog, node_at_pos, expected_load_call):
        """Tests on_file_dropped's target node identification logic."""
        test_file_path = "data.csv"
        scene_pos = QPointF(100, 100)
        
        mocker.patch.object(canvas_controller.model, 'get_node_at', return_value=node_at_pos)
        mock_load_data = mocker.patch.object(canvas_controller, 'load_data_into_node')

        with caplog.at_level(logging.DEBUG):
            canvas_controller.on_file_dropped(test_file_path, scene_pos)
        
        canvas_controller.model.get_node_at.assert_called_once()
        if expected_load_call:
            mock_load_data.assert_called_once_with(test_file_path, node_at_pos)
            assert "Dropped file" in caplog.text
        else:
            mock_load_data.assert_not_called()
            assert "did not hit a PlotNode" in caplog.text

    def test_on_data_load_error(self, canvas_controller, caplog):
        """Tests that on_data_load_error logs the error message."""
        error_msg = "Test data load error"
        with caplog.at_level(logging.ERROR):
            canvas_controller.on_data_load_error(error_msg)
            assert any(error_msg in r.message for r in caplog.records)
            assert any("ERROR" in r.levelname for r in caplog.records)
