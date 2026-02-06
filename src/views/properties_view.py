import logging
from typing import Union

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit, # Kept QLineEdit
    QVBoxLayout,
    QWidget,
    QToolButton,
    QSizePolicy,
)
from PySide6.QtGui import QIcon, QIntValidator, QDoubleValidator

from src.commands.change_property_command import ChangePropertyCommand
from src.commands.command_manager import CommandManager
from src.models import ApplicationModel
from src.models.nodes import PlotNode # Explicitly import PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    PlotMapping,
)
from src.models.nodes.plot_types import PlotType
from src.views.properties_ui_factory import PropertiesUIFactory
from src.views.layout_ui_factory import LayoutUIFactory # New import
from src.layout_manager import LayoutManager # New import
from src.controllers.main_controller import MainController # New import
from src.constants import LayoutMode # New import


Layout = Union[QVBoxLayout, QFormLayout, QHBoxLayout]


class PropertiesView(QWidget):
    """
    A non-modal panel that displays and allows editing of properties
    for the currently selected object(s) in the scene.
    """

    def __init__(
        self,
        model: ApplicationModel,
        command_manager: CommandManager,
        plot_types: list[PlotType],
        properties_ui_factory: PropertiesUIFactory,
        layout_ui_factory: LayoutUIFactory, # New parameter
        layout_manager: LayoutManager, # New parameter
        main_controller: MainController, # New parameter
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setFixedWidth(250) # Set a fixed width for the properties panel
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred) # Set size policy
        self.model = model
        self.command_manager = command_manager
        self.plot_types = plot_types
        self.properties_ui_factory = properties_ui_factory
        self._layout_ui_factory = layout_ui_factory # Store the instance
        self._layout_manager = layout_manager # Store the instance
        self._main_controller = main_controller # Store the instance

        # Main layout for the entire PropertiesView
        self._overall_layout = QVBoxLayout(self)
        self._overall_layout.setContentsMargins(5, 5, 5, 5)

        # Layout Mode Toggle Button (persistent at the top)
        self.layout_mode_toggle_button = QToolButton(self)
        self.layout_mode_toggle_button.setCheckable(True)
        self.layout_mode_toggle_button.setStyleSheet("QToolButton:checked { background-color: lightgray; }")
        
        # Set initial state and text
        initial_layout_mode = self._layout_manager.layout_mode
        self.layout_mode_toggle_button.setChecked(initial_layout_mode == LayoutMode.GRID)
        self._update_layout_mode_toggle_button_ui(initial_layout_mode)
        
        # Connect to main_controller
        self.layout_mode_toggle_button.toggled.connect(self._main_controller.toggle_layout_mode)
        
        # Connect to update UI based on layout manager changes
        self._layout_manager.layoutModeChanged.connect(self._update_layout_mode_toggle_button_ui)

        self._overall_layout.addWidget(self.layout_mode_toggle_button)
        self._overall_layout.addSpacing(10)

        # Container for the dynamic content
        self._dynamic_content_widget = QWidget(self)
        self._main_layout = QVBoxLayout(self._dynamic_content_widget) # This will be the layout for dynamic content
        self._main_layout.setContentsMargins(0,0,0,0) # No margins for the inner layout

        self._overall_layout.addWidget(self._dynamic_content_widget)
        self._overall_layout.addStretch() # Take up remaining space

        self._limit_edits: dict[str, QLineEdit] = {}
        self._current_node: PlotNode | None = None
        self._x_combo: QComboBox | None = None
        self._y_combo: QComboBox | None = None

        self.logger = logging.getLogger(self.__class__.__name__)

        self.model.selectionChanged.connect(self._update_content)
        self._layout_manager.layoutModeChanged.connect(self._update_content) # New connection
        self._update_content() # Initial call at the end of __init__

    def _clear_layout(self, layout: Layout):
        """Recursively clears all widgets and sub-layouts."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clear_layout(sub_layout)
        # Clear references to combo boxes after they are potentially deleted by deleteLater
        self._x_combo = None 
        self._y_combo = None

    def _update_content(self):
        """
        Updates the content of the properties panel based on current selection
        and layout mode.
        """
        self.logger.debug("Updating properties panel content.")
        self._current_node = None
        self._clear_layout(self._main_layout)
        selection = self.model.selection

        # Condition 1: Single PlotNode with data selected
        if len(selection) == 1 and isinstance(selection[0], PlotNode) and selection[0].data is not None:
            node = selection[0]
            self._current_node = node
            form_layout = QFormLayout()
            
            self._x_combo = QComboBox() 
            self._y_combo = QComboBox()

            self.properties_ui_factory.build_widgets(
                node,
                form_layout,
                self,
                self._on_property_changed,
                self._on_column_mapping_changed,
                self._on_limit_editing_finished,
                self._limit_edits,
                self._x_combo,
                self._y_combo,
            )
            self._main_layout.addLayout(form_layout)
            self._main_layout.addStretch()
            self.logger.debug(f"Displayed properties for selected PlotNode: {node.name}")
        # Condition 2: Otherwise (Default/Layout Controls)
        else:
            self.logger.debug("Displaying layout controls.")
            layout_controls_widget = self._layout_ui_factory.build_layout_controls(
                self._layout_manager.layout_mode, self._main_controller, self
            )
            self._main_layout.addWidget(layout_controls_widget)
            self._main_layout.addStretch()
            self.logger.debug("Displayed layout controls.")

    def _update_layout_mode_toggle_button_ui(self, layout_mode: LayoutMode):
        """
        Updates the text and checked state of the layout mode toggle button.
        """
        if layout_mode == LayoutMode.GRID:
            self.layout_mode_toggle_button.setText("Layout Mode: Grid")
            self.layout_mode_toggle_button.setChecked(True)
        else:
            self.layout_mode_toggle_button.setText("Layout Mode: Free Form")
            self.layout_mode_toggle_button.setChecked(False)

    def _on_plot_type_changed(self, new_plot_type_str: str, node: PlotNode):
        """Creates and executes a command when the plot type changes."""
        if not new_plot_type_str:
            return

        new_plot_type = PlotType(new_plot_type_str)

        assert node.plot_properties is not None
        old_plot_type = node.plot_properties.plot_type

        if new_plot_type != old_plot_type:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="plot_type",
                new_value=new_plot_type,
                property_dict_name="plot_properties",
            )
            self.command_manager.execute_command(cmd)
            self.on_selection_changed()  # Rebuild UI

    def _on_property_changed(self, node: PlotNode, prop_name: str, widget: QLineEdit):
        """Creates and executes a command when a QLineEdit's editing is finished."""
        new_value = widget.text()
        old_value = getattr(node.plot_properties, prop_name)

        if new_value != old_value:
            cmd = ChangePropertyCommand(
                node=node,
                property_name=prop_name,
                new_value=new_value,
                property_dict_name="plot_properties",
            )
            self.command_manager.execute_command(cmd)

    def _on_limit_editing_finished(self, node: PlotNode):
        """
        This runs after the user has finished editing in the limit fields.
        It gathers all values and executes a single command.
        """
        if not node:
            return

        def _parse_or_none(text: str) -> float | None:
            try:
                return float(text)
            except (ValueError, TypeError):
                return None

        new_xlim_min = _parse_or_none(self._limit_edits["xlim_min"].text())
        new_xlim_max = _parse_or_none(self._limit_edits["xlim_max"].text())
        new_ylim_min = _parse_or_none(self._limit_edits["ylim_min"].text())
        new_ylim_max = _parse_or_none(self._limit_edits["ylim_max"].text())

        assert node.plot_properties is not None
        old_limits = node.plot_properties.axes_limits
        new_limits = AxesLimits(
            xlim=(new_xlim_min, new_xlim_max),
            ylim=(new_ylim_min, new_ylim_max),
        )

        if old_limits != new_limits:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="axes_limits",
                new_value=new_limits,
                property_dict_name="plot_properties",
            )
            self.command_manager.execute_command(cmd)

    def _on_column_mapping_changed(self, new_text_ignored: str, node: PlotNode):
        """
        Creates and executes a command when a column selection changes.
        Reads from BOTH combo boxes to create a complete mapping.
        """
        x_col = self._x_combo.currentText()
        y_col = self._y_combo.currentText()

        if not x_col or not y_col:
            return

        assert node.plot_properties is not None
        new_mapping = PlotMapping(x=x_col, y=[y_col])
        old_mapping = node.plot_properties.plot_mapping

        if new_mapping != old_mapping:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="plot_mapping",
                new_value=new_mapping,
                property_dict_name="plot_properties",
            )
            self.command_manager.execute_command(cmd)

