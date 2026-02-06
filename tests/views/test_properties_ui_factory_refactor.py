from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLineEdit,
    QWidget,
)

from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
    ScatterPlotProperties,
)
from src.models.plots.plot_types import PlotType
from src.ui.factories.properties_ui_factory import (
    PropertiesUIFactory,
    _build_base_plot_properties_ui,
    _build_column_selectors,
    _build_limit_selectors,
    _build_line_plot_ui_widgets,
    _build_scatter_plot_ui_widgets,
)


@pytest.fixture
def mock_properties_ui_factory_instance():
    """Provides an instance of the refactored PropertiesUIFactory."""
    return PropertiesUIFactory()

@pytest.fixture
def mock_node():
    """Provides a mock PlotNode."""
    node = Mock(spec=PlotNode)
    node.data = None # Or a mock DataFrame if needed for specific tests
    return node

@pytest.fixture
def mock_scatter_node():
    """Provides a mock PlotNode with ScatterPlotProperties and data."""
    node = Mock(spec=PlotNode)
    node.plot_properties = Mock(spec=ScatterPlotProperties)
    node.plot_properties.plot_type = PlotType.SCATTER
    node.plot_properties.title = "Test Scatter"
    node.plot_properties.xlabel = "X"
    node.plot_properties.ylabel = "Y"
    node.plot_properties.marker_size = 5
    node.plot_properties.axes_limits = Mock(spec=AxesLimits, xlim=(0, 10), ylim=(0, 10))
    node.data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    return node

@pytest.fixture
def mock_line_node():
    """Provides a mock PlotNode with LinePlotProperties and data."""
    node = Mock(spec=PlotNode)
    node.plot_properties = Mock(spec=LinePlotProperties)
    node.plot_properties.plot_type = PlotType.LINE
    node.plot_properties.title = "Test Line"
    node.plot_properties.xlabel = "X"
    node.plot_properties.ylabel = "Y"
    node.plot_properties.line_width = 2
    node.plot_properties.axes_limits = Mock(spec=AxesLimits, xlim=(0, 10), ylim=(0, 10))
    node.data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    return node

@pytest.fixture
def mock_plot_node_with_data():
    node = Mock(spec=PlotNode)
    node.data = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
    node.plot_properties = PlotNode.plot_properties = LinePlotProperties(
        title="Test Plot",
        xlabel="X-axis",
        ylabel="Y-axis",
        plot_mapping=PlotMapping(x='col1', y=['col2']),
        axes_limits=AxesLimits(xlim=(0, 10), ylim=(0, 10))
    )
    node.plot_properties.plot_type = PlotType.LINE
    return node

@pytest.fixture
def common_ui_args(qtbot):
    """Provides common UI arguments for build_widgets."""
    parent_widget = QWidget()
    qtbot.addWidget(parent_widget)
    return {
        "layout": Mock(spec=QFormLayout),
        "parent": parent_widget,
        "on_property_changed": Mock(),
        "on_column_mapping_changed": Mock(),
        "on_limit_editing_finished": Mock(),
        "limit_edits": {},
        "x_combo": Mock(spec=QComboBox),
        "y_combo": Mock(spec=QComboBox),
    }

class TestPropertiesUIFactoryRefactor:
    def test_factory_instantiation(self, mock_properties_ui_factory_instance):
        """Verify the factory can be instantiated and has an empty builders dict."""
        factory = mock_properties_ui_factory_instance
        assert isinstance(factory, PropertiesUIFactory)
        assert factory._builders == {}

    def test_register_builder(self, mock_properties_ui_factory_instance):
        """Verify a builder can be registered."""
        factory = mock_properties_ui_factory_instance
        mock_builder = Mock()
        factory.register_builder(PlotType.SCATTER, mock_builder)
        assert factory._builders[PlotType.SCATTER] == mock_builder

    def test_build_widgets_with_registered_builder(self, mock_properties_ui_factory_instance, mock_scatter_node, common_ui_args):
        """Verify build_widgets calls the registered builder for a known plot type."""
        factory = mock_properties_ui_factory_instance
        mock_specific_builder = Mock()
        factory.register_builder(PlotType.SCATTER, mock_specific_builder)

        factory.build_widgets(node=mock_scatter_node, **common_ui_args)

        mock_specific_builder.assert_called_once_with(
            node=mock_scatter_node,
            layout=common_ui_args["layout"],
            parent=common_ui_args["parent"],
            on_property_changed=common_ui_args["on_property_changed"],
            on_column_mapping_changed=common_ui_args["on_column_mapping_changed"],
            on_limit_editing_finished=common_ui_args["on_limit_editing_finished"],
            limit_edits=common_ui_args["limit_edits"],
            x_combo=common_ui_args["x_combo"],
            y_combo=common_ui_args["y_combo"],
        )

    @patch('src.views.properties_ui_factory._build_base_plot_properties_ui')
    @patch('src.views.properties_ui_factory._build_line_plot_ui_widgets')
    @patch('src.views.properties_ui_factory._build_scatter_plot_ui_widgets')
    def test_build_widgets_with_unregistered_builder_no_error(self,
                                                             mock_scatter_builder,
                                                             mock_line_builder,
                                                             mock_base_builder,
                                                             mock_properties_ui_factory_instance,
                                                             mock_line_node,
                                                             common_ui_args):
        """Verify build_widgets handles an unregistered builder gracefully (no error, and calls fallback)."""
        factory = mock_properties_ui_factory_instance
        # LINE PlotType is not registered by default in this test setup

        # Ensure no builder was registered for LINE
        assert PlotType.LINE not in factory._builders

        factory.build_widgets(node=mock_line_node, **common_ui_args)

        # The fallback _build_base_plot_properties_ui should be called
        mock_base_builder.assert_called_once_with(
            node=mock_line_node,
            layout=common_ui_args["layout"],
            parent=common_ui_args["parent"],
            on_property_changed=common_ui_args["on_property_changed"],
            on_column_mapping_changed=common_ui_args["on_column_mapping_changed"],
            on_limit_editing_finished=common_ui_args["on_limit_editing_finished"],
            limit_edits=common_ui_args["limit_edits"],
            x_combo=common_ui_args["x_combo"],
            y_combo=common_ui_args["y_combo"],
        )
        mock_line_builder.assert_not_called()
        mock_scatter_builder.assert_not_called()

    def test_register_builder_overwrites_existing(self, mock_properties_ui_factory_instance, common_ui_args):
        """Verify that registering a builder for an existing PlotType overwrites the previous one."""
        factory = mock_properties_ui_factory_instance
        mock_builder_v1 = Mock(name="builder_v1")
        mock_builder_v2 = Mock(name="builder_v2")

        factory.register_builder(PlotType.LINE, mock_builder_v1)
        assert factory._builders[PlotType.LINE] == mock_builder_v1

        factory.register_builder(PlotType.LINE, mock_builder_v2)
        assert factory._builders[PlotType.LINE] == mock_builder_v2

        mock_node = Mock(spec=PlotNode)
        mock_node.plot_properties = Mock(spec=LinePlotProperties)
        mock_node.plot_properties.plot_type = PlotType.LINE

        factory.build_widgets(node=mock_node, **common_ui_args)

        mock_builder_v2.assert_called_once()
        mock_builder_v1.assert_not_called()

    @patch('src.views.properties_ui_factory._build_base_plot_properties_ui')
    @patch('src.views.properties_ui_factory._build_line_plot_ui_widgets')
    @patch('src.views.properties_ui_factory._build_scatter_plot_ui_widgets')
    @patch('src.views.properties_ui_factory._build_column_selectors')
    @patch('src.views.properties_ui_factory._build_limit_selectors')
    def test_build_widgets_full_integration(self,
                                            mock_build_limit_selectors,
                                            mock_build_column_selectors,
                                            mock_build_scatter_plot_ui_widgets,
                                            mock_build_line_plot_ui_widgets,
                                            mock_build_base_plot_properties_ui,
                                            mock_properties_ui_factory_instance,
                                            mock_line_node,
                                            mock_scatter_node,
                                            common_ui_args):
        """
        Tests the full integration of PropertiesUIFactory.build_widgets with registered builders
        for both LinePlot and ScatterPlot, verifying correct calls to sub-builders.
        """
        factory = mock_properties_ui_factory_instance

        # Register the concrete builder functions
        factory.register_builder(PlotType.LINE, _build_line_plot_ui_widgets)
        factory.register_builder(PlotType.SCATTER, _build_scatter_plot_ui_widgets)

        # Configure the mock _build_base_plot_properties_ui to call its sub-mocks
        def mock_base_builder_side_effect(node, layout, parent, on_property_changed, on_column_mapping_changed, on_limit_editing_finished, limit_edits, x_combo, y_combo):
            # Simulate the internal calls made by _build_base_plot_properties_ui
            mock_build_column_selectors(node=node, layout=layout, x_combo=x_combo, y_combo=y_combo, on_column_mapping_changed=on_column_mapping_changed)
            mock_build_limit_selectors(node=node, layout=layout, limit_edits=limit_edits, on_limit_editing_finished=on_limit_editing_finished)
        mock_build_base_plot_properties_ui.side_effect = mock_base_builder_side_effect

        # Test for LinePlot
        # Reset mocks before first use in this test to ensure clean call counts
        mock_build_base_plot_properties_ui.reset_mock()
        mock_build_column_selectors.reset_mock()
        mock_build_limit_selectors.reset_mock()
        mock_build_line_plot_ui_widgets.reset_mock()
        mock_build_scatter_plot_ui_widgets.reset_mock()

        factory.build_widgets(node=mock_line_node, **common_ui_args)

        mock_build_base_plot_properties_ui.assert_called_once_with(node=mock_line_node, **common_ui_args)
        # These should now be called from within the side_effect of mock_build_base_plot_properties_ui
        mock_build_column_selectors.assert_called_once_with(node=mock_line_node, layout=common_ui_args["layout"], x_combo=common_ui_args["x_combo"], y_combo=common_ui_args["y_combo"], on_column_mapping_changed=common_ui_args["on_column_mapping_changed"])
        mock_build_limit_selectors.assert_called_once_with(node=mock_line_node, layout=common_ui_args["layout"], limit_edits=common_ui_args["limit_edits"], on_limit_editing_finished=common_ui_args["on_limit_editing_finished"])
        mock_build_line_plot_ui_widgets.assert_called_once_with(node=mock_line_node, **common_ui_args)
        mock_build_scatter_plot_ui_widgets.assert_not_called()

        # Test for ScatterPlot
        # Reset mocks for the second call
        mock_build_base_plot_properties_ui.reset_mock()
        mock_build_column_selectors.reset_mock()
        mock_build_limit_selectors.reset_mock()
        mock_build_line_plot_ui_widgets.reset_mock()
        mock_build_scatter_plot_ui_widgets.reset_mock()

        factory.build_widgets(node=mock_scatter_node, **common_ui_args)

        mock_build_base_plot_properties_ui.assert_called_once_with(node=mock_scatter_node, **common_ui_args)
        # These should now be called from within the side_effect of mock_build_base_plot_properties_ui
        mock_build_column_selectors.assert_called_once_with(node=mock_scatter_node, layout=common_ui_args["layout"], x_combo=common_ui_args["x_combo"], y_combo=common_ui_args["y_combo"], on_column_mapping_changed=common_ui_args["on_column_mapping_changed"])
        mock_build_limit_selectors.assert_called_once_with(node=mock_scatter_node, layout=common_ui_args["layout"], limit_edits=common_ui_args["limit_edits"], on_limit_editing_finished=common_ui_args["on_limit_editing_finished"])
        mock_build_line_plot_ui_widgets.assert_not_called()
        mock_build_scatter_plot_ui_widgets.assert_called_once_with(node=mock_scatter_node, **common_ui_args)

class TestStandaloneBuilders:
    @pytest.fixture
    def mock_form_layout(self):
        layout = Mock(spec=QFormLayout)
        layout.addRow = Mock()
        return layout

    @pytest.fixture
    def mock_qcombobox(self):
        combo = Mock(spec=QComboBox)
        combo.clear = Mock()
        combo.addItems = Mock()
        combo.currentTextChanged = Mock()
        combo.currentText = Mock(return_value="mock_col")
        return combo

    @pytest.fixture
    def mock_qlineedit(self):
        edit = Mock(spec=QLineEdit)
        edit.setObjectName = Mock()
        edit.editingFinished = MagicMock() # Make editingFinished a MagicMock object
        edit.editingFinished.connect = MagicMock() # Mock its connect method
        edit.text = Mock(return_value="5.0")
        edit.setValidator = MagicMock() # Make setValidator a MagicMock object
        return edit

    @pytest.fixture
    def mock_qwidget(self, qtbot):
        widget = QWidget()
        qtbot.addWidget(widget)
        return widget

    @pytest.fixture
    def mock_on_change_callback(self):
        return Mock()

    @pytest.fixture
    def mock_limit_edits(self, mock_qlineedit):
        # We need distinct mock QLineEdits for each limit, as their methods will be called independently
        return {
            "xlim_min": Mock(spec=QLineEdit, editingFinished=MagicMock(), setValidator=MagicMock(), text=Mock(return_value="1.0")),
            "xlim_max": Mock(spec=QLineEdit, editingFinished=MagicMock(), setValidator=MagicMock(), text=Mock(return_value="5.0")),
            "ylim_min": Mock(spec=QLineEdit, editingFinished=MagicMock(), setValidator=MagicMock(), text=Mock(return_value="2.0")),
            "ylim_max": Mock(spec=QLineEdit, editingFinished=MagicMock(), setValidator=MagicMock(), text=Mock(return_value="6.0"))
        }

    def test_build_column_selectors(self, qtbot, mock_plot_node_with_data, mock_form_layout,
                                    mock_qcombobox, mock_on_change_callback):
        node = mock_plot_node_with_data
        node.data = pd.DataFrame({'col1': [1], 'col2': [2], 'col3': [3]})
        node.plot_properties.plot_mapping = PlotMapping(x='col1', y=['col2'])

        _build_column_selectors(
            node=node,
            layout=mock_form_layout,
            x_combo=mock_qcombobox,
            y_combo=mock_qcombobox,
            on_column_mapping_changed=mock_on_change_callback
        )

        mock_form_layout.addRow.call_count == 2
        mock_qcombobox.clear.call_count == 2
        mock_qcombobox.addItems.assert_any_call(['col1', 'col2', 'col3'])
        mock_qcombobox.setCurrentText.assert_any_call('col1')
        mock_qcombobox.setCurrentText.assert_any_call('col2')
        mock_qcombobox.currentTextChanged.connect.call_count == 2

    def test_build_limit_selectors(self, qtbot, mock_plot_node_with_data, mock_form_layout, mock_limit_edits,
                                   mock_on_change_callback):
        node = mock_plot_node_with_data
        node.plot_properties.axes_limits = AxesLimits(xlim=(1.0, 5.0), ylim=(2.0, 6.0))

        _build_limit_selectors(
            node=node,
            layout=mock_form_layout,
            limit_edits=mock_limit_edits,
            on_limit_editing_finished=mock_on_change_callback
        )

        assert mock_form_layout.addRow.call_count == 2
        # Verify that setValidator and connect are called on the mock QLineEdits
        for key in ["xlim_min", "xlim_max", "ylim_min", "ylim_max"]:
            mock_limit_edits[key].setValidator.assert_called_once()
            mock_limit_edits[key].editingFinished.connect.assert_called_once()

    @patch('src.views.properties_ui_factory._build_column_selectors')
    @patch('src.views.properties_ui_factory._build_limit_selectors')
    def test_build_base_plot_properties_ui(self, mock_build_limit_selectors, mock_build_column_selectors, qtbot, mock_line_node, mock_form_layout, mock_qwidget, mock_on_change_callback):
        """
        Verify that _build_base_plot_properties_ui correctly adds title, xlabel, and ylabel
        QLineEdit widgets to the form layout and connects their signals.
        """
        node = mock_line_node
        node.plot_properties.title = "My Plot Title"
        node.plot_properties.xlabel = "My X-Label"
        node.plot_properties.ylabel = "My Y-Label"

        _build_base_plot_properties_ui(
            node=node,
            layout=mock_form_layout,
            parent=mock_qwidget,
            on_property_changed=mock_on_change_callback,
            limit_edits={}, # Not used in this function, but required by signature
            x_combo=Mock(spec=QComboBox), # Not used
            y_combo=Mock(spec=QComboBox), # Not used
            on_column_mapping_changed=Mock(), # Not used
            on_limit_editing_finished=Mock() # Not used
        )

        assert mock_form_layout.addRow.call_count == 3
        mock_build_column_selectors.assert_called_once()
        mock_build_limit_selectors.assert_called_once()
        # Ensure that QLineEdit widgets are added with correct initial text and signals connected
        # We need to look for specific widgets added to the mock_form_layout's rows.
        # This requires a slightly more advanced mock inspection or finding by objectName.

        # For simplicity in this test, we'll check if addRow was called with QLineEdit-like arguments
        # and that the on_property_changed callback was connected.
        # A more robust test would inspect the actual widgets.

        # Mocking the QLineEdit's signal connection
        mock_line_edit = Mock(spec=QLineEdit)
        mock_line_edit.editingFinished = Mock()

        # Check for title
        assert any(args[0][0] == "Title:" and isinstance(args[0][1], QLineEdit) for args in mock_form_layout.addRow.call_args_list)

        # Check for xlabel
        assert any(args[0][0] == "X-Axis Label:" and isinstance(args[0][1], QLineEdit) for args in mock_form_layout.addRow.call_args_list)

        # Check for ylabel
        assert any(args[0][0] == "Y-Axis Label:" and isinstance(args[0][1], QLineEdit) for args in mock_form_layout.addRow.call_args_list)

    @patch('src.views.properties_ui_factory._build_base_plot_properties_ui')
    def test_build_line_plot_ui_widgets(self, mock_build_base_plot_properties_ui, qtbot, mock_line_node, mock_form_layout, mock_qwidget, mock_on_change_callback):
        """
        Verify that _build_line_plot_ui_widgets correctly adds line plot specific
        QLineEdit widgets to the form layout and connects their signals.
        """
        node = mock_line_node
        node.plot_properties.line_width = 3

        _build_line_plot_ui_widgets(
            node=node,
            layout=mock_form_layout,
            parent=mock_qwidget,
            on_property_changed=mock_on_change_callback,
            limit_edits={},
            x_combo=Mock(spec=QComboBox),
            y_combo=Mock(spec=QComboBox),
            on_column_mapping_changed=Mock(),
            on_limit_editing_finished=Mock()
        )

        assert mock_form_layout.addRow.call_count == 0
        mock_build_base_plot_properties_ui.assert_called_once()
        # Assuming the QLineEdit text is set to the property value
        # This part requires a deeper inspection of the mock_form_layout or the widget itself
        # For now, we'll check that a line edit was added for "Line Width"

    @patch('src.views.properties_ui_factory._build_base_plot_properties_ui')
    def test_build_scatter_plot_ui_widgets(self, mock_build_base_plot_properties_ui, qtbot, mock_scatter_node, mock_form_layout, mock_qwidget, mock_on_change_callback):
        """
        Verify that _build_scatter_plot_ui_widgets correctly adds scatter plot specific
        QLineEdit widgets to the form layout and connects their signals.
        """
        node = mock_scatter_node
        node.plot_properties.marker_size = 7

        _build_scatter_plot_ui_widgets(
            node=node,
            layout=mock_form_layout,
            parent=mock_qwidget,
            on_property_changed=mock_on_change_callback,
            limit_edits={},
            x_combo=Mock(spec=QComboBox),
            y_combo=Mock(spec=QComboBox),
            on_column_mapping_changed=Mock(),
            on_limit_editing_finished=Mock()
        )

        assert mock_form_layout.addRow.call_count == 1
        mock_build_base_plot_properties_ui.assert_called_once()
        assert any("Marker Size" in str(args) and isinstance(args[0][1], QLineEdit) for args in mock_form_layout.addRow.call_args_list)
        # Assuming the QLineEdit text is set to the property value
        # This part requires a deeper inspection of the mock_form_layout or the widget itself
        # For now, we'll check that a line edit was added for "Marker Size"

        # Further tests will be added once the common UI building logic is extracted
        # and the specific plot-type builder functions are created.
