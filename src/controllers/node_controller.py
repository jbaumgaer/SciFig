import logging
from functools import partial
import dataclasses
from typing import Callable, List, Optional, Tuple, Union

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QLineEdit, QComboBox

from src.models.application_model import ApplicationModel
from src.services.commands.command_manager import CommandManager
from src.services.commands.change_property_command import ChangePropertyCommand
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import AxesLimits, PlotMapping, BasePlotProperties
from src.models.plots.plot_types import PlotType


class NodeController(QObject):
    def __init__(self, model: ApplicationModel, command_manager: CommandManager):
        super().__init__()
        self.model = model
        self.command_manager = command_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("NodeController initialized.")

    def on_plot_type_changed(self, new_plot_type_str: str, node: PlotNode):
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
            # Rebuilding UI would typically be handled by properties_panel listening to modelChanged/selectionChanged
            # self.on_selection_changed()  # Rebuild UI

    def on_property_changed(self, node: PlotNode, prop_name: str, new_value: str):
        """Creates and executes a command when a QLineEdit's editing is finished."""
        old_value = getattr(node.plot_properties, prop_name)

        if new_value != old_value:
            cmd = ChangePropertyCommand(
                node=node,
                property_name=prop_name,
                new_value=new_value,
                property_dict_name="plot_properties",
            )
            self.command_manager.execute_command(cmd)

    def on_limit_editing_finished(self, node: PlotNode, xlim_min_text: str, xlim_max_text: str, ylim_min_text: str, ylim_max_text: str):
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

        new_xlim_min = _parse_or_none(xlim_min_text)
        new_xlim_max = _parse_or_none(xlim_max_text)
        new_ylim_min = _parse_or_none(ylim_min_text)
        new_ylim_max = _parse_or_none(ylim_max_text)

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

    def on_column_mapping_changed(self, new_text_ignored: str, node: PlotNode, x_combo: QComboBox, y_combo: QComboBox):
        """
        Creates and executes a command when a column selection changes.
        Reads from BOTH combo boxes to create a complete mapping.
        """
        x_col = x_combo.currentText()
        y_col = y_combo.currentText()

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