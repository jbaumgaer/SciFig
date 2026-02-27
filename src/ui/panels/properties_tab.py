import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_types import ArtistType
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events
from src.ui.factories.plot_properties_ui_factory import PlotPropertiesUIFactory


class PropertiesTab(QWidget):
    def __init__(
        self,
        model: ApplicationModel,
        event_aggregator: EventAggregator,
        plot_properties_ui_factory: PlotPropertiesUIFactory,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.model = model
        self._event_aggregator = event_aggregator
        self._plot_properties_ui_factory = plot_properties_ui_factory
        self.logger = logging.getLogger(self.__class__.__name__)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Subplot Selection Section ---
        self._subplot_selection_group = QGroupBox("Selected Subplot", self)
        self._subplot_selection_layout = QFormLayout(self._subplot_selection_group)

        self._subplot_selector_combo = QComboBox(self)
        self._subplot_selector_combo.setObjectName("subplot_selector_combo")
        self._subplot_selection_layout.addRow("Subplot:", self._subplot_selector_combo)

        self._data_file_path_edit = QLineEdit(self)
        self._data_file_path_edit.setPlaceholderText("No data file loaded")
        self._data_file_path_edit.setReadOnly(True)
        self._data_file_path_edit.setObjectName("data_file_path_edit")

        self._select_file_button = QPushButton("Select File", self)
        self._select_file_button.setObjectName("select_file_button")

        self._apply_data_button = QPushButton("Apply", self)
        self._apply_data_button.setObjectName("apply_data_button")
        # TODO: I get a Failed to load data, project controller has no attribute data_loader error here

        h_layout_data_buttons = QHBoxLayout()
        h_layout_data_buttons.addWidget(self._select_file_button)
        h_layout_data_buttons.addWidget(self._apply_data_button)

        self._subplot_selection_layout.addRow("Data File:", self._data_file_path_edit)
        self._subplot_selection_layout.addRow(
            "", h_layout_data_buttons
        )  # Empty label to align buttons
        #TODO: Is this the tangling widget that I see in the properties?

        self._main_layout.addWidget(self._subplot_selection_group)

        # --- Plot Type Selection Section ---
        self._plot_type_group = QGroupBox("Plot Type", self)
        self._plot_type_layout = QFormLayout(self._plot_type_group)

        self._plot_type_selector_combo = QComboBox(self)
        self._plot_type_selector_combo.setObjectName("plot_type_selector_combo")
        for plot_type in ArtistType:
            self._plot_type_selector_combo.addItem(plot_type.value)
        self._plot_type_layout.addRow("Type:", self._plot_type_selector_combo)
        
        self._main_layout.addWidget(self._plot_type_group)

        # --- Dynamic Properties Section ---
        self._dynamic_properties_area = QWidget(self)
        self._dynamic_properties_layout = QVBoxLayout(self._dynamic_properties_area)
        self._dynamic_properties_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addWidget(self._dynamic_properties_area)

        self._main_layout.addStretch()

        self._limit_edits: dict = {}
        self._x_combo: QComboBox = QComboBox(self)
        self._y_combo: QComboBox = QComboBox(self)

        self._subscribe_to_events()
        self._connect_widgets_to_events()
        
        self.logger.info("PropertiesTab initialized.")
        self._update_content()  # Initial call

    def _subscribe_to_events(self):
        """Subscribes to notification events to update the UI."""
        self._event_aggregator.subscribe(Events.SELECTION_CHANGED, self._update_content)
        self._event_aggregator.subscribe(Events.NODE_RENAMED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.NODE_VISIBILITY_CHANGED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.NODE_LOCKED_CHANGED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.PLOT_TITLE_CHANGED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.PLOT_XLABEL_CHANGED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.PLOT_YLABEL_CHANGED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.PLOT_MARKER_SIZE_CHANGED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.PLOT_AXIS_LIMITS_CHANGED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.PLOT_MAPPING_CHANGED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.PLOT_TYPE_CHANGED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.NODE_DATA_FILE_PATH_UPDATED, self._update_content_if_selected)
        self._event_aggregator.subscribe(Events.NODE_DATA_LOADED, self._update_content_if_selected)

    def _connect_widgets_to_events(self):
        """Connects UI widgets to publish request events."""
        self._subplot_selector_combo.currentTextChanged.connect(
            lambda text: self._event_aggregator.publish(
                Events.SUBPLOT_SELECTION_IN_UI_CHANGED, plot_id=self._subplot_selector_combo.currentData()
            )
        )
        self._plot_type_selector_combo.currentTextChanged.connect(
            lambda text: self._event_aggregator.publish(
                Events.CHANGE_PLOT_TYPE_REQUESTED,
                node_id=self._subplot_selector_combo.currentData(),
                new_plot_type_str=text,
            )
        )
        self._select_file_button.clicked.connect(
            lambda: self._event_aggregator.publish(
                Events.SELECT_DATA_FILE_FOR_NODE_REQUESTED,
                node_id=self._subplot_selector_combo.currentData(),
            )
        )
        self._apply_data_button.clicked.connect(
            lambda: self._event_aggregator.publish(
                Events.APPLY_DATA_TO_NODE_REQUESTED,
                node_id=self._subplot_selector_combo.currentData(),
                file_path=Path(self._data_file_path_edit.text()),
            )
        )

    def _clear_layout(self, layout_obj: QVBoxLayout | QFormLayout):
        """Recursively clears all widgets and sub-layouts from a layout."""
        if layout_obj is None:
            return
        while layout_obj.count():
            item = layout_obj.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clear_layout(sub_layout)

    def _update_content_if_selected(self, node_id: str, *args, **kwargs):
        """Triggers a content update only if the event's node_id matches the currently selected plot."""
        current_selected_plot_id = self._subplot_selector_combo.currentData()
        if node_id == current_selected_plot_id:
            self._update_content()

    def _update_content(self, selected_node_ids: Optional[list[str]] = None):
        """
        Updates the content of the PropertiesTab based on the current selection.
        This method orchestrates updates for all sections of the tab.
        TODO: The UI should never directly check the model for any information. That's the whole point of the MVP architecture.
        """
        self.logger.debug("PropertiesTab: Updating content.")
        selected_nodes = self.model.selection
        
        self._update_subplot_selection_ui(selected_nodes)
        self._update_plot_type_selector_ui(selected_nodes)
        self._update_node_specific_properties_ui(selected_nodes)

    def _update_subplot_selection_ui(self, selected_nodes: list[QObject]):
        """
        Populates the subplot selector combo box and updates the data file path display.
        TODO: The UI should never directly check the model for any information. That's the whole point of the MVP architecture.
        """
        self.logger.debug("PropertiesTab: Updating subplot selection UI.")
        self._subplot_selector_combo.blockSignals(True)
        
        self._subplot_selector_combo.clear()
        all_plots = [
            node
            for node in self.model.scene_root.all_descendants()
            if isinstance(node, PlotNode)
        ]

        plot_id_to_name = {plot.id: plot.name for plot in all_plots}

        if not all_plots:
            self._subplot_selector_combo.addItem("No plots available")
            self._subplot_selector_combo.setEnabled(False)
            self._data_file_path_edit.clear()
            self._select_file_button.setEnabled(False)
            self._apply_data_button.setEnabled(False)
            self.logger.debug("PropertiesTab: No plots available, UI disabled.")
            self._subplot_selector_combo.blockSignals(False)
            return

        self._subplot_selector_combo.setEnabled(True)
        for plot in all_plots:
            self._subplot_selector_combo.addItem(plot.name, userData=plot.id)

        current_selected_plot_id = None
        if len(selected_nodes) == 1 and isinstance(selected_nodes[0], PlotNode):
            current_selected_plot_id = selected_nodes[0].id

        if current_selected_plot_id:
            index = self._subplot_selector_combo.findData(current_selected_plot_id)
            if index != -1:
                self._subplot_selector_combo.setCurrentIndex(index)
                self.logger.debug(
                    f"PropertiesTab: Subplot selector set to: {plot_id_to_name.get(current_selected_plot_id)}"
                )
                selected_plot_node = selected_nodes[0]
                self._data_file_path_edit.setText(
                    str(selected_plot_node.data_file_path)
                    if selected_plot_node.data_file_path
                    else ""
                )
                # TODO: The data file path is not actaully being updated right now. Also, that should be a separate method
                self._select_file_button.setEnabled(True)
                self._apply_data_button.setEnabled(True)
            else:
                self._data_file_path_edit.clear()
                self._select_file_button.setEnabled(False)
                self._apply_data_button.setEnabled(False)
                self.logger.warning(
                    f"PropertiesTab: Current selected plot ID {current_selected_plot_id} not found in combo box."
                )
        else:
            self._subplot_selector_combo.setCurrentIndex(0)
            self._data_file_path_edit.clear()
            self._select_file_button.setEnabled(False)
            self._apply_data_button.setEnabled(False)
            self.logger.debug(
                "PropertiesTab: No specific plot selected, default combo box selection."
            )

        self._subplot_selector_combo.blockSignals(False)

    def _update_plot_type_selector_ui(self, selected_nodes: list[QObject]):
        """
        Updates the plot type selector combo box based on the selected plot's properties.
        """
        self.logger.debug("PropertiesTab: Updating plot type selection UI.")
        self._plot_type_selector_combo.blockSignals(True)

        current_node: Optional[PlotNode] = None
        if len(selected_nodes) == 1 and isinstance(selected_nodes[0], PlotNode):
            current_node = selected_nodes[0]
        
        if current_node and current_node.plot_properties:
            current_plot_type = current_node.plot_properties.plot_type
            self._plot_type_selector_combo.setCurrentText(current_plot_type.value)
            self._plot_type_selector_combo.setEnabled(True)
            self.logger.debug(f"PropertiesTab: Plot type selector set to: {current_plot_type.value}")
        else:
            self._plot_type_selector_combo.setCurrentIndex(0)
            self._plot_type_selector_combo.setEnabled(False)
            self.logger.debug("PropertiesTab: No plot selected, plot type selector disabled.")

        self._plot_type_selector_combo.blockSignals(False)

    def _update_node_specific_properties_ui(self, selected_nodes: list[QObject]):
        """
        Clears and rebuilds the plot-specific properties UI based on the selected node.
        """
        self.logger.debug("PropertiesTab: Updating node-specific properties UI.")
        self._clear_layout(self._dynamic_properties_layout)

        current_node: Optional[PlotNode] = None
        if len(selected_nodes) == 1 and isinstance(selected_nodes[0], PlotNode):
            current_node = selected_nodes[0]

        if current_node:
            self._plot_properties_ui_factory.build_widgets(
                node=current_node,
                layout=self._dynamic_properties_layout,
                parent=self._dynamic_properties_area,
                limit_edits=self._limit_edits,
                x_combo=self._x_combo,
                y_combo=self._y_combo,
            )
        else:
            self._dynamic_properties_layout.addWidget(
                QLabel(
                    "Select a plot to view its properties.",
                    self._dynamic_properties_area,
                )
            )
