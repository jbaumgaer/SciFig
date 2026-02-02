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
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.model = model
        self.command_manager = command_manager

        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self._main_layout)

        # To store references to the limit line edits
        self._limit_edits: dict[str, QLineEdit] = {}
        self._current_node: PlotNode | None = None  # Track the node being edited

        # Timer for debouncing limit edits

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
        print("PropertiesView: Selection changed. Rebuilding UI.")
        self._current_node = None  # Clear the tracked node
        self._clear_layout(self._main_layout)
        selection = self.model.selection

        if not selection:
            self._main_layout.addWidget(QLabel("No item selected."))
        elif len(selection) > 1:
            self._main_layout.addWidget(QLabel(f"{len(selection)} items selected."))
        else:
            node = selection[0]
            if isinstance(node, PlotNode):
                self._current_node = node  # Track the new node
                self._build_plotnode_ui(node)
            else:
                self._main_layout.addWidget(QLabel(f"Selected: '{node.name}'"))

    def _build_plotnode_ui(self, node: PlotNode):
        if not node.plot_properties:
            self._main_layout.addWidget(QLabel(f"Selected: '{node.name}' (No data)"))
            return

        form_layout = QFormLayout()
        props = node.plot_properties

        # --- Title ---
        title_edit = QLineEdit(props.title)
        title_edit.setObjectName("title_edit")
        title_edit.editingFinished.connect(
            partial(
                self._on_property_changed,
                node=node,
                prop_name="title",
                widget=title_edit,
            )
        )
        form_layout.addRow("Title:", title_edit)

        # --- X Label ---
        xlabel_edit = QLineEdit(props.xlabel)
        xlabel_edit.setObjectName("xlabel_edit")
        xlabel_edit.editingFinished.connect(
            partial(
                self._on_property_changed,
                node=node,
                prop_name="xlabel",
                widget=xlabel_edit,
            )
        )
        form_layout.addRow("X-Axis Label:", xlabel_edit)

        # --- Y Label ---
        ylabel_edit = QLineEdit(props.ylabel)
        ylabel_edit.setObjectName("ylabel_edit")
        ylabel_edit.editingFinished.connect(
            partial(
                self._on_property_changed,
                node=node,
                prop_name="ylabel",
                widget=ylabel_edit,
            )
        )
        form_layout.addRow("Y-Axis Label:", ylabel_edit)

        self._main_layout.addLayout(form_layout)

        # --- Column Selectors ---
        if node.data is not None:
            self._build_column_selectors(node, form_layout)

        # --- Axes Limits ---
        self._build_limit_selectors(node, form_layout)

        self._main_layout.addStretch()

    def _build_column_selectors(self, node: PlotNode, layout: QFormLayout):
        assert node.data is not None
        assert node.plot_properties is not None
        columns = list(node.data.columns)
        current_mapping = node.plot_properties.plot_mapping
        current_x = current_mapping.x
        current_y_list = current_mapping.y
        current_y = current_y_list[0] if current_y_list else None

        # X Column
        self._x_combo = QComboBox()
        self._x_combo.addItems(columns)
        if current_x in columns:
            self._x_combo.setCurrentText(current_x)
        self._x_combo.currentTextChanged.connect(
            partial(self._on_column_mapping_changed, node=node)
        )
        layout.addRow("X-Axis Column:", self._x_combo)

        # Y Column (for now, only one is supported by properties view)
        self._y_combo = QComboBox()
        self._y_combo.addItems(columns)
        if current_y in columns:
            self._y_combo.setCurrentText(current_y)
        self._y_combo.currentTextChanged.connect(
            partial(self._on_column_mapping_changed, node=node)
        )
        layout.addRow("Y-Axis Column:", self._y_combo)

    def _build_limit_selectors(self, node: PlotNode, layout: QFormLayout):
        assert node.plot_properties is not None
        validator = QDoubleValidator()
        current_limits = node.plot_properties.axes_limits

        # X Limits
        xlim = current_limits.xlim
        self._limit_edits["xlim_min"] = QLineEdit(
            str(xlim[0] if xlim[0] is not None else "")
        )
        self._limit_edits["xlim_min"].setObjectName("xlim_min_edit")
        self._limit_edits["xlim_max"] = QLineEdit(
            str(xlim[1] if xlim[1] is not None else "")
        )
        self._limit_edits["xlim_max"].setObjectName("xlim_max_edit")

        for w in (self._limit_edits["xlim_min"], self._limit_edits["xlim_max"]):
            w.setValidator(validator)
            w.editingFinished.connect(
                partial(self._on_limit_editing_finished, node=node)
            )
        lim_layout_x = QHBoxLayout()
        lim_layout_x.addWidget(self._limit_edits["xlim_min"])
        lim_layout_x.addWidget(QLabel("to"))
        lim_layout_x.addWidget(self._limit_edits["xlim_max"])
        layout.addRow("X-Axis Limits:", lim_layout_x)

        # Y Limits
        ylim = current_limits.ylim
        self._limit_edits["ylim_min"] = QLineEdit(
            str(ylim[0] if ylim[0] is not None else "")
        )
        self._limit_edits["ylim_min"].setObjectName("ylim_min_edit")
        self._limit_edits["ylim_max"] = QLineEdit(
            str(ylim[1] if ylim[1] is not None else "")
        )
        self._limit_edits["ylim_max"].setObjectName("ylim_max_edit")

        for w in (self._limit_edits["ylim_min"], self._limit_edits["ylim_max"]):
            w.setValidator(validator)
            w.editingFinished.connect(
                partial(self._on_limit_editing_finished, node=node)
            )

        lim_layout_y = QHBoxLayout()
        lim_layout_y.addWidget(self._limit_edits["ylim_min"])
        lim_layout_y.addWidget(QLabel("to"))
        lim_layout_y.addWidget(self._limit_edits["ylim_max"])
        layout.addRow("Y-Axis Limits:", lim_layout_y)

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

        # Only execute a command if the limits have actually changed
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
