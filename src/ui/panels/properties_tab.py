import logging
from typing import List, Optional

from PySide6.QtCore import QObject  # Qt for Alignment - Removed Qt as not directly used in this version
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

from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.ui.factories.plot_properties_ui_factory import PlotPropertiesUIFactory
from src.models.plots.plot_types import PlotType


class PropertiesTab(QWidget):
    def __init__(
        self,
        model: ApplicationModel,
        node_controller: NodeController,
        plot_properties_ui_factory: PlotPropertiesUIFactory,
        project_controller: ProjectController,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.model = model
        self.node_controller = node_controller
        self.plot_properties_ui_factory = plot_properties_ui_factory
        self.project_controller = project_controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("PropertiesTab initialized.")

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

        h_layout_data_buttons = QHBoxLayout()
        h_layout_data_buttons.addWidget(self._select_file_button)
        h_layout_data_buttons.addWidget(self._apply_data_button)

        self._subplot_selection_layout.addRow("Data File:", self._data_file_path_edit)
        self._subplot_selection_layout.addRow(
            "", h_layout_data_buttons
        )  # Empty label to align buttons

        self._main_layout.addWidget(self._subplot_selection_group)

        # --- Plot Type Selection Section (managed by PropertiesTab directly) ---
        self._plot_type_group = QGroupBox("Plot Type", self)
        self._plot_type_layout = QFormLayout(self._plot_type_group)

        self._plot_type_selector_combo = QComboBox(self)
        self._plot_type_selector_combo.setObjectName("plot_type_selector_combo")
        for plot_type in PlotType:
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

        # Connect signals
        self.model.modelChanged.connect(
            self._update_content
        )  # For changes that affect list of plots or properties
        self.model.selectionChanged.connect(
            self._update_content
        )  # For when selected plot changes

        # Connect subplot selector and plot type selector to their handlers
        self._subplot_selector_combo.currentTextChanged.connect(
            self.node_controller.on_subplot_selection_changed
        )
        self._plot_type_selector_combo.currentTextChanged.connect(
            self._on_plot_type_combo_changed
        ) # Connect to local handler

        self._select_file_button.clicked.connect(self._on_select_file_clicked)
        self._apply_data_button.clicked.connect(self._on_apply_data_clicked)

        self._update_content()  # Initial call

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

    def _update_content(self):
        """
        Updates the content of the PropertiesTab based on the current selection.
        This method orchestrates updates for all sections of the tab.
        """
        self.logger.debug("PropertiesTab: Updating content.")
        selected_nodes = self.model.selection
        
        self._update_subplot_selection_ui(selected_nodes)
        self._update_plot_type_selector_ui(selected_nodes) # New call
        self._update_node_specific_properties_ui(selected_nodes)

    def _update_subplot_selection_ui(self, selected_nodes: List[QObject]):
        """
        Populates the subplot selector combo box and updates the data file path display.
        """
        self.logger.debug("PropertiesTab: Updating subplot selection UI.")
        # Temporarily block signals to prevent triggering on_subplot_selection_changed during repopulation
        self._subplot_selector_combo.blockSignals(True)
        
        self._subplot_selector_combo.clear()
        all_plots = [
            node
            for node in self.model.scene_root.all_descendants()
            if isinstance(node, PlotNode)
        ]

        plot_id_to_name = {plot.id: plot.name for plot in all_plots}
        # plot_ids = [plot.id for plot in all_plots] # Not used

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
            # Find the index of the currently selected plot
            index = self._subplot_selector_combo.findData(current_selected_plot_id)
            if index != -1:
                self._subplot_selector_combo.setCurrentIndex(index)
                self.logger.debug(
                    f"PropertiesTab: Subplot selector set to: {plot_id_to_name.get(current_selected_plot_id)}"
                )
                # Update data file path edit for the selected plot
                selected_plot_node = selected_nodes[
                    0
                ]  # Assumed to be PlotNode based on if condition
                self._data_file_path_edit.setText(
                    str(selected_plot_node.data_file_path)
                    if selected_plot_node.data_file_path
                    else ""
                )
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
            self._subplot_selector_combo.setCurrentIndex(
                0
            )  # Select first item if nothing specific selected
            self._data_file_path_edit.clear()
            self._select_file_button.setEnabled(False)
            self._apply_data_button.setEnabled(False)
            self.logger.debug(
                "PropertiesTab: No specific plot selected, default combo box selection."
            )

        self._subplot_selector_combo.blockSignals(False)

    def _update_plot_type_selector_ui(self, selected_nodes: List[QObject]):
        """
        Updates the plot type selector combo box based on the selected plot's properties.
        """
        self.logger.debug("PropertiesTab: Updating plot type selection UI.")
        self._plot_type_selector_combo.blockSignals(True) # Block signals during update

        current_node: Optional[PlotNode] = None
        if len(selected_nodes) == 1 and isinstance(selected_nodes[0], PlotNode):
            current_node = selected_nodes[0]
        
        if current_node and current_node.plot_properties:
            current_plot_type = current_node.plot_properties.plot_type
            self._plot_type_selector_combo.setCurrentText(current_plot_type.value)
            self._plot_type_selector_combo.setEnabled(True)
            self.logger.debug(f"PropertiesTab: Plot type selector set to: {current_plot_type.value}")
        else:
            self._plot_type_selector_combo.setCurrentIndex(0) # Default to first item
            self._plot_type_selector_combo.setEnabled(False)
            self.logger.debug("PropertiesTab: No plot selected, plot type selector disabled.")

        self._plot_type_selector_combo.blockSignals(False)

    def _on_plot_type_combo_changed(self, new_plot_type_str: str):
        """
        Handler for when the plot type combo box selection changes.
        Triggers the NodeController to update the plot type in the model.
        """
        self.logger.debug(f"PropertiesTab: Plot type combo changed to: {new_plot_type_str}")
        selected_plot_id = self._subplot_selector_combo.currentData()
        if not selected_plot_id:
            self.logger.warning("PropertiesTab: Plot type changed but no plot selected in combo box.")
            return

        selected_plot_node = self.model.scene_root.find_node_by_id(selected_plot_id)
        if selected_plot_node:
            self.node_controller.on_plot_type_changed(new_plot_type_str, selected_plot_node)
        else:
            self.logger.error(f"PropertiesTab: Could not find PlotNode with ID {selected_plot_id} for plot type change.")


    def _on_select_file_clicked(self):
        """Handles the 'Select File' button click."""
        selected_plot_id = self._subplot_selector_combo.currentData()
        if not selected_plot_id:
            self.logger.warning(
                "PropertiesTab: Select File clicked but no plot selected in combo box."
            )
            return

        # Get the actual PlotNode instance
        selected_plot_node = self.model.scene_root.find_node_by_id(selected_plot_id)
        if selected_plot_node:
            self.node_controller.on_select_file_clicked(selected_plot_node)
            # The node_controller updates node.data_file_path and emits modelChanged, triggering _update_content
        else:
            self.logger.error(
                f"PropertiesTab: Could not find PlotNode with ID {selected_plot_id} for 'Select File' action."
            )

    def _on_apply_data_clicked(self):
        """Handles the 'Apply' data button click."""
        selected_plot_id = self._subplot_selector_combo.currentData()
        if not selected_plot_id:
            self.logger.warning(
                "PropertiesTab: Apply clicked but no plot selected in combo box."
            )
            return

        selected_plot_node = self.model.scene_root.find_node_by_id(selected_plot_id)
        if selected_plot_node and selected_plot_node.data_file_path:
            self.node_controller.on_apply_data_clicked(
                selected_plot_node, selected_plot_node.data_file_path
            )
            # The node_controller handles loading and updating the model
        elif selected_plot_node:
            self.logger.warning(
                f"PropertiesTab: Apply clicked for node {selected_plot_id}, but no data file path is set."
            )
        else:
            self.logger.error(
                f"PropertiesTab: Could not find PlotNode with ID {selected_plot_id} for 'Apply' action."
            )

    def _update_node_specific_properties_ui(self, selected_nodes: List[QObject]):
        """
        Clears and rebuilds the plot-specific properties UI based on the selected node.
        """
        self.logger.debug("PropertiesTab: Updating node-specific properties UI.")
        self._clear_layout(self._dynamic_properties_layout)

        current_node: Optional[PlotNode] = None
        if len(selected_nodes) == 1 and isinstance(selected_nodes[0], PlotNode):
            current_node = selected_nodes[0]

        if current_node:
            # Pass all necessary items, including the combo boxes and edits to be populated by the factory
            self.plot_properties_ui_factory.build_widgets(
                node=current_node,
                layout=self._dynamic_properties_layout,  # Expects QVBoxLayout now
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
