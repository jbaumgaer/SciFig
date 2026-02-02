from functools import partial
from typing import Union

from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from src.commands.change_property_command import ChangePropertyCommand
from src.commands.command_manager import CommandManager
from src.models import ApplicationModel, PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    PlotMapping,
)
from src.models.nodes.plot_types import PlotType
from .properties_ui_factory import PropertiesUIFactory

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
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.model = model
        self.command_manager = command_manager
        self.plot_types = plot_types

        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self._main_layout)

        self._limit_edits: dict[str, QLineEdit] = {}
        self._current_node: PlotNode | None = None
        self._x_combo = QComboBox()
        self._y_combo = QComboBox()

        self.model.selectionChanged.connect(self.on_selection_changed)
        self.on_selection_changed()

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

    def on_selection_changed(self):
        self._current_node = None
        self._clear_layout(self._main_layout)
        selection = self.model.selection

        if not selection:
            self._main_layout.addWidget(QLabel("No item selected."))
        elif len(selection) > 1:
            self._main_layout.addWidget(QLabel(f"{len(selection)} items selected."))
        else:
            node = selection[0]
            if isinstance(node, PlotNode):
                self._current_node = node
                if not node.plot_properties:
                    self._main_layout.addWidget(
                        QLabel(f"Selected: '{node.name}' (No data)")
                    )
                    return

                form_layout = QFormLayout()
                PropertiesUIFactory.create_ui(
                    node,
                    form_layout,
                    self,
                    self.plot_types,
                    self._on_plot_type_changed,
                    self._on_property_changed,
                    self._on_column_mapping_changed,
                    self._on_limit_editing_finished,
                    self._limit_edits,
                    self._x_combo,
                    self._y_combo,
                )
                self._main_layout.addLayout(form_layout)
                self._main_layout.addStretch()

            else:
                self._main_layout.addWidget(QLabel(f"Selected: '{node.name}'"))

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
            self.on_selection_changed() # Rebuild UI

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

