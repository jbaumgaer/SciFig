# Technical Design Document (TDD_2.md) - UI Panel Refactoring and Enhancements

## 1. Introduction
This document details the technical design for refactoring the application's right-side UI panel into a tabbed interface and implementing new features within these tabs. It outlines the architectural changes, affected components, design patterns, and a comprehensive testing strategy. The aim is to enhance modularity, maintainability, user experience, and future extensibility.

## 2. Overall Architectural Changes
*   **Rename `PropertiesPanel` to `SidePanel`:** The existing `PropertiesPanel` (`src/ui/panels/properties_panel.py`) will be renamed to `SidePanel` (`src/ui/panels/side_panel.py`) to reflect its new role as a container for multiple tabs.
*   **New Tab Classes:** Three new `QWidget` subclasses will be created: `PropertiesTab`, `LayoutTab`, and `LayersTab`. These will encapsulate the content and logic for each respective tab, promoting separation of concerns.
*   **Rename `PropertiesUIFactory` to `PlotPropertiesUIFactory`:** The factory responsible for building plot-specific UI elements will be renamed to `PlotPropertiesUIFactory` (`src/ui/factories/plot_properties_ui_factory.py`) to explicitly define its scope and allow for future, separate factories (e.g., `TextPropertiesUIFactory`).
*   **Integration with `MainWindow`:** `MainWindow` will instantiate and dock the `SidePanel`. `SidePanel` will then instantiate and add the individual `*Tab` classes to a `QTabWidget`.

## 3. Design Patterns Overview
The following design patterns will be applied to achieve a robust, maintainable, and extensible solution:

*   **Composite:** The `SidePanel` will act as a composite, treating its constituent `PropertiesTab`, `LayoutTab`, and `LayersTab` components uniformly.
*   **Factory Method:** The `PlotPropertiesUIFactory` (and future similar factories) utilizes this to create specific UI widgets based on plot types or other object types.
*   **Observer (Signals & Slots):** PyQt/PySide's native Signals & Slots mechanism will be used extensively for loose coupling and communication between UI elements, controllers, and the application model.
*   **Command:** All state-modifying actions will be encapsulated in `Command` objects, enabling a robust undo/redo system.
*   **Strategy:** Dynamic UI rendering, such as changing the displayed properties based on the selected plot type, is an application of the Strategy pattern, where `PlotPropertiesUIFactory` provides the "strategy" for UI construction.
*   **Builder:** The internal structure of `PropertiesTab` will use a builder-like approach to construct and arrange its various sections (subplot selector, data source, plot type, dynamic properties).
*   **Dependency Injection:** Maintained throughout the application for loose coupling, testability, and flexible configuration.
*   **Separation of Concerns:** Each class, especially the new `*Tab` classes, will have a clear, focused responsibility, minimizing interdependencies.

## 4. Feature: Refactor `PropertiesPanel` to `SidePanel` with Tabbed Interface

### 4.1. Description
The existing `PropertiesPanel` will be refactored into a `SidePanel` that hosts a `QTabWidget`. This `QTabWidget` will contain three main tabs: "Properties", "Layout", and "Layers", each managed by a dedicated `QWidget` subclass (`PropertiesTab`, `LayoutTab`, `LayersTab`). This enhances modularity and user experience by organizing diverse functionalities.

### 4.2. Design Patterns Applied
*   **Composite:** `SidePanel` as the composite, managing its tab components.
*   **Builder:** The assembly of `SidePanel` and its internal tabs will be handled by `CompositionRoot` using a builder-like approach.

### 4.3. Affected Files and Specific Changes
*   **Rename `src/ui/panels/properties_panel.py` to `src/ui/panels/side_panel.py`:**
    *   Rename class `PropertiesPanel` to `SidePanel`.
    *   Update imports in `src/ui/windows/main_window.py` and `src/core/composition_root.py`.
*   **`src/ui/panels/side_panel.py` (New `SidePanel` class):**
    *   **Initialization (`__init__`)**:
        *   Replace `_overall_layout` with a `QTabWidget` as the main layout.
        *   Remove the `layout_mode_toggle_button` and its associated logic from `SidePanel`.
        *   Instantiate `PropertiesTab`, `LayoutTab`, and `LayersTab`, passing in their respective dependencies (e.g., `ApplicationModel`, controllers, factories, `ConfigService`).
        *   Add these instantiated tabs to the `QTabWidget` with appropriate display labels ("Properties", "Layout", "Layers").
    *   **Content Management (`_update_content`)**:
        *   Simplify this method significantly. It will no longer dynamically build content based on selection, but rather orchestrate the updates of its contained tabs or manage active tab switching.
    *   **Tab Switching (`show_tab_by_name(tab_name: str)`)**:
        *   Add a new public method to allow external components (e.g., `MainWindow`) to programmatically switch to a specific tab.
*   **`src/ui/windows/main_window.py`:**
    *   **Imports**: Update import path for `SidePanel`.
    *   **`_create_properties_dock`**:
        *   Modify to instantiate `SidePanel` instead of the old `PropertiesPanel`.
        *   Ensure all necessary dependencies (model, controllers, factories, etc.) are passed to `SidePanel`'s constructor.
        *   Update `self.properties_view` to reference the new `SidePanel` instance.
*   **`src/core/composition_root.py`:**
    *   **Imports**: Update import path for `SidePanel`.
    *   **Instantiation Logic**: Update to instantiate `SidePanel` and pass the correct dependencies. Ensure `PlotPropertiesUIFactory` (renamed) is correctly passed through to `SidePanel` which then passes it to `PropertiesTab`.

### 4.4. Testing Plan

*   **Unit Tests (`tests/ui/panels/test_side_panel.py` - New file):**
    *   **Setup:** Mock all dependencies (model, controllers, tab classes) that `SidePanel` consumes.
    *   **Test Case: Initialization:**
        *   **Arrange:** Instantiate `SidePanel`.
        *   **Assert:** Verify that `QTabWidget` is the central widget. Verify that `PropertiesTab`, `LayoutTab`, and `LayersTab` instances are correctly created and added to the `QTabWidget` with the expected number of tabs and titles.
    *   **Test Case: Tab Switching:**
        *   **Arrange:** Instantiate `SidePanel`.
        *   **Act:** Call `side_panel.show_tab_by_name("Layout")`.
        *   **Assert:** Verify the "Layout" tab is the currently active tab in the `QTabWidget`. Repeat for other tabs.
*   **Integration Tests (`tests/integration/test_main_window_integration.py` - Existing/Modified file):**
    *   **Setup:** Launch a minimal application instance with `MainWindow` and `SidePanel`.
    *   **Test Case: Dock Visibility and Tab Interaction:**
        *   **Arrange:** Ensure the `SidePanel` is visible.
        *   **Act:** Programmatically click on different tabs within the `SidePanel` or simulate user clicks.
        *   **Assert:** Verify that the content area changes as expected for each tab.
*   **E2E Tests:** Verification of the tabbed interface will be implicitly covered by overall E2E tests for main workflows.

### 4.5. Risks and Mitigations
*   **Risk:** Incorrect wiring of dependencies to the new `*Tab` classes from `SidePanel` and `CompositionRoot`.
*   **Mitigation:** Thorough review of `SidePanel` and `CompositionRoot` instantiation logic. Unit tests for each `*Tab` class ensuring correct dependency injection upon creation.
*   **Risk:** Visual regressions or unexpected layout issues due to the `QTabWidget` integration.
*   **Mitigation:** Comprehensive manual UI inspection during development. Consider integrating automated screenshot testing into CI/CD if a robust framework is available.

---

## 5. Feature: `PropertiesTab` - Content and Logic

### 5.1. Description
This tab will centralize controls for editing the properties of a selected `SceneNode`, with an initial focus on `PlotNode`s. It will include a subplot selector, data source management with file selection, a plot type selector, and a dynamically rendered area for plot-specific properties. Visual sectioning will improve readability.

### 5.2. Design Patterns Applied
*   **Factory Method:** `PlotPropertiesUIFactory` will be utilized to build plot-specific UI components.
*   **Observer (Signals & Slots):** Used for connecting UI input fields (QComboBox, QLineEdit, QPushButton) to `NodeController` methods and for `PropertiesTab` to react to `ApplicationModel` changes.
*   **Command:** All property modifications will be encapsulated in `ChangePropertyCommand` objects, managed by `CommandManager`.
*   **Strategy:** The dynamic rendering of plot-specific properties based on `PlotType` (or `SceneNode` type) is an application of the Strategy pattern, where `PlotPropertiesUIFactory` provides the "strategy" for UI construction.
*   **Builder:** The internal structure of `PropertiesTab` will use a builder-like approach to construct and arrange its various sections (subplot selector, data source, plot type, dynamic properties).

### 5.3. Affected Files and Specific Changes
*   **New file `src/ui/panels/properties_tab.py` (`PropertiesTab` class):**
    *   **Initialization (`__init__`)**:
        *   Accept `ApplicationModel`, `NodeController`, `PlotPropertiesUIFactory` (renamed), `ConfigService`, `ProjectController` (for data loading).
        *   Set up a main `QVBoxLayout`.
        *   **Subplot Selection Section (QGroupBox):**
            *   Layout: `QFormLayout` or `QVBoxLayout`.
            *   Components:
                *   `QComboBox` for selecting a `PlotNode` from all available plots in the `ApplicationModel`.
                *   `QLineEdit` to display the current `PlotNode.data_file_path`.
                *   `QPushButton` labeled "Select File" to open a file dialog.
                *   `QPushButton` labeled "Apply" to trigger data loading with the selected file path.
        *   **Plot Type Selection Section (QGroupBox):**
            *   Layout: `QFormLayout`.
            *   Components:
                *   `QComboBox` for selecting a `PlotType` (Line, Scatter, etc.).
        *   **Dynamic Properties Section (QGroupBox):**
            *   Layout: `QVBoxLayout`. This group will contain the dynamically built UI from `PlotPropertiesUIFactory`.
    *   **Content Update Methods**:
        *   **`_update_content()`:** This central method will be connected to `model.selectionChanged` and `model.modelChanged`. It will orchestrate calls to the specific update methods below. It will ensure that the current `PlotNode` is available for property editing.
        *   **`_update_subplot_selection_ui(selected_plot_node: Optional[PlotNode])`:**
            *   Populates the subplot `QComboBox` with all `PlotNode`s (ID or a user-friendly name) from `ApplicationModel.scene_root.all_descendants(of_type=PlotNode)`.
            *   Sets the `QComboBox`'s current index to match `selected_plot_node`.
            *   Updates the data file path `QLineEdit` with `selected_plot_node.data_file_path`.
        *   **`_update_plot_type_selector_ui(selected_plot_node: Optional[PlotNode])`:**
            *   Populates the plot type `QComboBox` with all `PlotType` enum values.
            *   Sets the `QComboBox`'s current index to match `selected_plot_node.plot_properties.plot_type`.
        *   **`_update_node_specific_properties_ui(selected_plot_node: Optional[PlotNode])`:**
            *   Clears the existing widgets from the "Dynamic Properties Section" layout.
            *   If `selected_plot_node` is valid, it calls `plot_properties_ui_factory.build_widgets(selected_plot_node, ...)` to build and add the plot-type-specific UI elements into this section's layout.
            *   Handles cases where no plot is selected or `plot_properties` is `None` by displaying a placeholder message.
    *   **Signal Connections**:
        *   `model.selectionChanged.connect(self._update_content)`
        *   `model.modelChanged.connect(self._update_content)`
        *   Subplot `QComboBox.currentTextChanged.connect(node_controller.on_subplot_selection_changed)`
        *   "Select File" button `clicked.connect(node_controller.on_select_file_clicked)`
        *   "Apply" button `clicked.connect(node_controller.on_apply_data_clicked)`
        *   Plot type `QComboBox.currentTextChanged.connect(node_controller.on_plot_type_changed)`
*   **Rename `src/ui/factories/properties_ui_factory.py` to `src/ui/factories/plot_properties_ui_factory.py`:**
    *   Rename class `PropertiesUIFactory` to `PlotPropertiesUIFactory`.
    *   Update all references and imports accordingly (e.g., in `src/core/composition_root.py`, `src/ui/panels/side_panel.py`).
*   **`src/models/nodes/plot_node.py`:**
    *   Add `data_file_path: Optional[Path] = None` as a new attribute to the `PlotNode` dataclass.
    *   Modify `to_dict()` and `from_dict()` methods to include `data_file_path` for proper project serialization and deserialization.
*   **`src/ui/factories/plot_properties_ui_factory.py` (Renamed):**
    *   **Modify `_build_base_plot_properties_ui`:**
        *   Integrate creation of the plot type `QComboBox` into this method, connecting its signal to `node_controller.on_plot_type_changed`. This `QComboBox` will be passed from `PropertiesTab`.
    *   **New Helper Method (`_build_data_source_ui`)**:
        *   Create a new private helper method (e.g., `_build_data_source_ui`) that builds and returns the `QLineEdit` for `data_file_path` and the "Select File"/"Apply" `QPushButton`s. This will be called from `PropertiesTab` when setting up the subplot selection section.
    *   **Visual Sectioning:** Use `QGroupBox` or `QFrame` elements to logically group related properties (e.g., "General Plot Properties", "Axis Labels", "Data Source") within the UI generated by this factory.
*   **`src/controllers/node_controller.py`:**
    *   **`on_subplot_selection_changed(plot_id: str)` (New method):**
        *   Receives the ID of the newly selected plot.
        *   Finds the corresponding `PlotNode` in `ApplicationModel`.
        *   Updates `ApplicationModel.selection` to contain only this `PlotNode`.
    *   **`on_select_file_clicked(node: PlotNode)` (New method):**
        *   Opens a `QFileDialog` to allow the user to select a data file (e.g., CSV).
        *   Stores the *selected file path* temporarily (e.g., as an instance variable or within the `PlotNode` itself in a "pending" state) but does *not* load data immediately.
    *   **`on_apply_data_clicked(node: PlotNode, selected_file_path: Optional[Path])` (New method):**
        *   Receives the `PlotNode` and the path to the data file to be loaded.
        *   Delegates actual data loading to a `DataLoader` service (potentially accessed via `ProjectController`).
        *   On successful loading, creates a `ChangePropertyCommand` to update `node.data` and `node.data_file_path` in the `ApplicationModel`. This ensures undo/redo.
        *   Handles errors during data loading (e.g., file not found, parsing error).
    *   **`on_plot_type_changed` (Existing method):** No direct changes, but its execution will now trigger `PropertiesTab` to rebuild the dynamic UI section via `model.modelChanged`.

### 5.4. Testing Plan

*   **Unit Tests (`tests/ui/panels/test_properties_tab.py` - New file):**
    *   **Setup:** Instantiate `PropertiesTab` with mocked `ApplicationModel`, `NodeController`, `PlotPropertiesUIFactory`.
    *   **Test Case: Initialization & Initial Content:**
        *   **Arrange:** Mock `ApplicationModel.scene_root.all_descendants` to return a list of `PlotNode`s.
        *   **Act:** Instantiate `PropertiesTab`.
        *   **Assert:** Verify subplot `QComboBox` is populated. Verify data path `QLineEdit` is empty or reflects default. Verify plot type `QComboBox` is populated. Verify dynamic properties section is empty or shows placeholder.
    *   **Test Case: `_update_content` on Selection Change:**
        *   **Arrange:** Instantiate `PropertiesTab`. Mock `model.selection` to return a `PlotNode`.
        *   **Act:** Emit `model.selectionChanged`.
        *   **Assert:** Verify `_update_subplot_selection_ui`, `_update_plot_type_selector_ui`, `_update_node_specific_properties_ui` are called. Verify correct `PlotNode` is selected in dropdowns. Verify `PlotPropertiesUIFactory.build_widgets` was called with the selected `PlotNode`.
    *   **Test Case: Subplot `QComboBox` Interaction:**
        *   **Arrange:** `PropertiesTab` instantiated and `model.selectionChanged` already triggered for a plot.
        *   **Act:** Simulate selecting a different plot from the subplot `QComboBox`.
        *   **Assert:** Verify `node_controller.on_subplot_selection_changed` is called with the correct `PlotNode` ID.
    *   **Test Case: Data File "Select File" Button:**
        *   **Arrange:** A `PlotNode` is selected.
        *   **Act:** Simulate "Select File" button click.
        *   **Assert:** Verify `node_controller.on_select_file_clicked` is called with the current `PlotNode`.
    *   **Test Case: Data File "Apply" Button:**
        *   **Arrange:** A `PlotNode` is selected, and a file path has been selected (mock this state in `node_controller`).
        *   **Act:** Simulate "Apply" button click.
        *   **Assert:** Verify `node_controller.on_apply_data_clicked` is called with the current `PlotNode` and the pending file path.
    *   **Test Case: Plot Type `QComboBox` Interaction:**
        *   **Arrange:** A `PlotNode` is selected.
        *   **Act:** Simulate selecting a different `PlotType` from the `QComboBox`.
        *   **Assert:** Verify `node_controller.on_plot_type_changed` is called. Verify `_update_node_specific_properties_ui` is triggered and `PlotPropertiesUIFactory.build_widgets` is called again with the new plot type.
*   **Unit Tests (`tests/controllers/test_node_controller.py` - Existing/Modified file):**
    *   **Setup:** Instantiate `NodeController` with mocked `ApplicationModel`, `CommandManager`, `ProjectController` (for data loading).
    *   **Test Case: `on_subplot_selection_changed`:**
        *   **Arrange:** Mock `ApplicationModel.scene_root.find_node_by_id`.
        *   **Act:** Call `node_controller.on_subplot_selection_changed("plot_id_1")`.
        *   **Assert:** Verify `application_model.selection` is updated correctly.
    *   **Test Case: `on_select_file_clicked`:**
        *   **Arrange:** Mock `QFileDialog.getOpenFileName` to return a specific path.
        *   **Act:** Call `node_controller.on_select_file_clicked(mock_plot_node)`.
        *   **Assert:** Verify the selected file path is stored temporarily (e.g., on the node).
    *   **Test Case: `on_apply_data_clicked` (Success):**
        *   **Arrange:** Mock `ProjectController.load_data_into_plot_node` to succeed.
        *   **Act:** Call `node_controller.on_apply_data_clicked(mock_plot_node, Path("test_data.csv"))`.
        *   **Assert:** Verify `CommandManager.execute_command` is called with a `ChangePropertyCommand` for `node.data` and `node.data_file_path`.
    *   **Test Case: `on_apply_data_clicked` (Failure):**
        *   **Arrange:** Mock `ProjectController.load_data_into_plot_node` to raise an exception.
        *   **Act:** Call `node_controller.on_apply_data_clicked(mock_plot_node, Path("invalid.csv"))`.
        *   **Assert:** Verify error handling (e.g., logging, user notification) and no command is executed.
*   **Unit Tests (`tests/models/nodes/test_plot_node.py` - Existing/Modified file):**
    *   Test `PlotNode` serialization/deserialization with `data_file_path`.
*   **Unit Tests (`tests/ui/factories/test_plot_properties_ui_factory.py` - New/Renamed file):**
    *   **Setup:** Instantiate `PlotPropertiesUIFactory`. Mock `PlotNode`, `NodeController`.
    *   **Test Case: `build_widgets` for Line Plot:**
        *   **Arrange:** Mock a `PlotNode` with `PlotType.LINE`.
        *   **Act:** Call `build_widgets`.
        *   **Assert:** Verify common UI elements (title, labels, columns, limits) are created. Verify line-specific UI elements (if any) are created. Verify no scatter-specific elements. Verify `QGroupBox`/`QFrame` usage.
    *   **Test Case: `build_widgets` for Scatter Plot:**
        *   **Arrange:** Mock a `PlotNode` with `PlotType.SCATTER`.
        *   **Act:** Call `build_widgets`.
        *   **Assert:** Verify common UI elements. Verify scatter-specific UI elements (`marker_size`) are created. Verify no line-specific elements.
*   **Integration Tests (`tests/integration/test_properties_tab_interaction.py` - New file):**
    *   **Setup:** Launch app, load a project with multiple plot nodes.
    *   **Test Case: Subplot Selection and Property Update:**
        *   **Arrange:** Select the "Properties" tab.
        *   **Act:** Use the subplot dropdown to select a different plot. Change its title.
        *   **Assert:** Verify the canvas updates, and undo/redo functions correctly.
    *   **Test Case: Data Loading Workflow:**
        *   **Arrange:** Select a plot.
        *   **Act:** Click "Select File", choose a valid data file. Click "Apply".
        *   **Assert:** Verify the plot on canvas updates with new data. Verify the data file path is displayed. Verify undo/redo.
    *   **Test Case: Plot Type Change and Dynamic UI:**
        *   **Arrange:** Select a plot.
        *   **Act:** Change the plot type (e.g., from Line to Scatter). Observe the dynamic properties section. Modify a new property (e.g., Marker Size).
        *   **Assert:** Verify the dynamic UI changes correctly. Verify property change is reflected on canvas and undo/redo works.
*   **E2E Tests:** Part of comprehensive E2E tests covering project creation, data loading, plot modification, save/load, and undo/redo.

### 5.5. Risks and Mitigations
*   **Risk:** Complexity of dynamic UI generation in `PropertiesTab` leading to bugs or performance issues.
*   **Mitigation:** Clear separation of concerns into helper methods (`_update_subplot_selection_ui`, `_update_node_specific_properties_ui`). Thorough unit testing of `PropertiesTab` and `PlotPropertiesUIFactory`. Use `QLayout`s for efficient widget management.
*   **Risk:** Data loading from "Apply" button might be asynchronous and require careful handling to avoid UI freezes.
*   **Mitigation:** Implement data loading in a separate thread (e.g., using `QThreadPool` or `QFuture`). Provide visual feedback (progress bar, spinner) during loading. The `NodeController` method will initiate this and update the model when complete.
*   **Risk:** Inconsistent state between the data file path `QLineEdit` and the actual `PlotNode.data_file_path` if "Apply" is not clicked.
*   **Mitigation:** `NodeController`'s `on_select_file_clicked` should store the path internally (e.g., in a temporary attribute on the node or controller) until "Apply" is pressed. The `QLineEdit` will display the *pending* path, and `PlotNode.data_file_path` only updates on "Apply".

---

## 6. Feature: `LayoutTab` - Content and Logic

### 6.1. Description
This tab will centralize the layout configuration controls. It will include a renamed toggle button to switch between displaying the grid layout parameters and the free-form layout alignment/distribution controls.

### 6.2. Design Patterns Applied
*   **Observer (Signals & Slots):** For connecting the toggle button and layout parameter input fields to `LayoutController` methods.
*   **Command:** Layout parameter changes and alignment/distribution actions are handled by existing `ChangeGridParametersCommand` and `BatchChangePlotGeometryCommand`.

### 6.3. Affected Files and Specific Changes
*   **New file `src/ui/panels/layout_tab.py` (`LayoutTab` class):**
    *   **Initialization (`__init__`)**:
        *   Accept `ApplicationModel`, `LayoutController`, `LayoutUIFactory`.
        *   Set up a main `QVBoxLayout`.
        *   **Layout UI Type Toggle Section (QGroupBox):**
            *   Contains a `QToolButton` (or `QPushButton` with checkable state).
            *   Set initial `checked` state based on `layout_controller._layout_manager.ui_selected_layout_mode == LayoutMode.GRID`.
            *   Set button text to "Switch to Grid Layout UI" or "Switch to Free-Form Layout UI" (dynamically updated).
            *   Connect `toggled` signal to `layout_controller.toggle_layout_mode`.
        *   **Dynamic Layout Controls Container (`QStackedWidget` or `QStackedLayout`):**
            *   This widget will dynamically display the output of `LayoutUIFactory.build_layout_controls`. A `QStackedWidget` is ideal here as `LayoutUIFactory` returns a full `QWidget`.
    *   **Content Update (`_update_content()`)**:
        *   This method will be connected to `layout_controller._layout_manager.uiLayoutModeChanged`.
        *   It will clear the current widget in the `QStackedWidget`.
        *   Call `layout_ui_factory.build_layout_controls` to get the appropriate UI widget.
        *   Add the new widget to the `QStackedWidget`.
    *   **Button Text Update (`_update_toggle_button_text(layout_mode: LayoutMode)`)**:
        *   A helper method to dynamically change the text of the toggle button based on the current `ui_selected_layout_mode`.
*   **`src/ui/panels/side_panel.py` (Modified `SidePanel`):**
    *   Ensure the `layout_mode_toggle_button` and its associated logic are *completely removed* from `SidePanel`'s `__init__` and any `_update_...` methods.
*   **`src/ui/factories/layout_ui_factory.py`:**
    *   No direct changes needed here, as its `build_layout_controls` method is already designed to return the correct widget based on the mode provided.

### 6.4. Testing Plan

*   **Unit Tests (`tests/ui/panels/test_layout_tab.py` - New file):**
    *   **Setup:** Instantiate `LayoutTab` with mocked `ApplicationModel`, `LayoutController`, `LayoutUIFactory`.
    *   **Test Case: Initialization:**
        *   **Arrange:** Mock `layout_controller._layout_manager.ui_selected_layout_mode`.
        *   **Act:** Instantiate `LayoutTab`.
        *   **Assert:** Verify toggle button's initial text and checked state are correct. Verify `layout_ui_factory.build_layout_controls` is called once with the initial mode.
    *   **Test Case: Toggle Button Interaction:**
        *   **Arrange:** `LayoutTab` instantiated.
        *   **Act:** Simulate clicking the toggle button.
        *   **Assert:** Verify `layout_controller.toggle_layout_mode` is called. Verify `_update_content` is triggered. Verify toggle button text updates.
    *   **Test Case: `_update_content` on `uiLayoutModeChanged`:**
        *   **Arrange:** `LayoutTab` instantiated.
        *   **Act:** Emit `layout_controller._layout_manager.uiLayoutModeChanged` with `LayoutMode.FREE_FORM`.
        *   **Assert:** Verify `layout_ui_factory.build_layout_controls` is called with `LayoutMode.FREE_FORM`. Verify the `QStackedWidget` displays the new UI.
*   **Integration Tests (`tests/integration/test_layout_tab_interaction.py` - New file):**
    *   **Setup:** Launch app, with `SidePanel` visible and "Layout" tab active.
    *   **Test Case: Toggle and Layout Control Interaction:**
        *   **Arrange:** A simple layout of plots is on the canvas.
        *   **Act:** Click the layout UI toggle button to switch between modes.
        *   **Assert:** Verify the UI controls in the tab change. Interact with parameters (e.g., rows, cols in Grid mode, alignment buttons in Free-Form mode). Verify canvas reflects changes. Verify undo/redo.

### 6.5. Risks and Mitigations
*   **Risk:** Incorrect state synchronization between the toggle button in `LayoutTab` and `layout_controller._layout_manager.ui_selected_layout_mode`.
*   **Mitigation:** Thorough unit tests for `LayoutTab` initialization and signal connections. Ensure `layout_controller.toggle_layout_mode` is the single source of truth for UI selected mode changes.
*   **Risk:** The dynamic loading of layout controls might lead to memory leaks if old widgets are not properly deleted.
*   **Mitigation:** Ensure `_update_content` correctly clears and `deleteLater()`s old widgets before adding new ones.

---

## 7. Feature: `LayersTab` - Content and Logic

### 7.1. Description
This tab will provide a hierarchical view of all `SceneNode`s (`PlotNode`, `GroupNode`, future `TextNode`, `ShapeNode`) present on the canvas. It will offer controls for managing node visibility, lock state, Z-order (reordering), grouping/ungrouping, and in-place renaming.

### 7.2. Design Patterns Applied
*   **Observer (Signals & Slots):** For connecting UI elements within the `QTreeWidget` (checkboxes, drag-and-drop events) to `NodeController` methods.
*   **Command:** All scene graph modifications (visibility, locking, reordering, grouping, renaming) will be encapsulated in `Command` objects, ensuring undo/redo.
*   **Composite:** The `LayersTab` directly visualizes and interacts with the `SceneNode` composite structure managed by `ApplicationModel`.

### 7.3. Affected Files and Specific Changes
*   **New file `src/ui/panels/layers_tab.py` (`LayersTab` class):**
    *   **Initialization (`__init__`)**:
        *   Accept `ApplicationModel`, `NodeController`, `ConfigService`.
        *   Set up a main `QVBoxLayout`.
        *   **`QTreeWidget`**: Will display the hierarchical list of `SceneNode`s. Configure for drag-and-drop.
        *   Add buttons for "Group", "Ungroup", etc. (optional, can be context menu).
    *   **Content Update (`_update_content()`)**:
        *   This method will be connected to `model.modelChanged`.
        *   It will clear the `QTreeWidget` and rebuild the entire node hierarchy from `ApplicationModel.scene_root`. This simplifies initial implementation.
        *   Helper method `_build_node_item(node: SceneNode)`: Recursively creates `QTreeWidgetItem`s for a given `SceneNode` and its children, including checkboxes for `visible` and `locked` states, and sets item flags for editability and drag-and-drop.
    *   **Signal Connections**:
        *   `model.modelChanged.connect(self._update_content)` (Triggers full rebuild).
        *   `QTreeWidget.itemChanged.connect(self._handle_item_changed)`: This will handle changes to `visible`, `locked` checkboxes, and in-place renaming. It will dispatch to `NodeController`.
        *   Override `QTreeWidget` drag-and-drop event handlers (`dragEnterEvent`, `dropEvent`, `startDrag`) to manage node reordering.
*   **`src/models/nodes/scene_node.py`:**
    *   **New Attributes:** Add `visible: bool = True` and `locked: bool = False` to the `SceneNode` dataclass.
    *   **Serialization:** Update `to_dict()` and `from_dict()` methods to include `visible` and `locked` for persistence.
*   **`src/controllers/node_controller.py`:**
    *   **`set_node_visibility(node_id: str, visible: bool)` (New method):**
        *   Finds the `SceneNode` by `node_id`.
        *   Creates and executes a `ChangePropertyCommand` to update `node.visible`.
    *   **`set_node_locked(node_id: str, locked: bool)` (New method):**
        *   Finds the `SceneNode` by `node_id`.
        *   Creates and executes a `ChangePropertyCommand` to update `node.locked`.
    *   **`reorder_nodes(parent_id: str, node_id: str, new_index: int)` (New method):**
        *   Finds the parent `SceneNode` (or `SceneRoot`) and the `SceneNode` to reorder.
        *   Creates and executes a `ChangeChildrenOrderCommand` (new command) to modify the order of children within the parent.
    *   **`group_nodes(node_ids: List[str])` (New method):**
        *   Finds all `SceneNode`s corresponding to `node_ids`.
        *   Creates a new `GroupNode`.
        *   Creates and executes a `GroupNodesCommand` (new command) to move the selected nodes into the new `GroupNode` and add the `GroupNode` to the scene.
    *   **`ungroup_node(group_id: str)` (New method):**
        *   Finds the `GroupNode` by `group_id`.
        *   Creates and executes an `UngroupNodesCommand` (new command) to move children of the `GroupNode` to its parent and then remove the `GroupNode`.
    *   **`rename_node(node_id: str, new_name: str)` (New method):**
        *   Finds the `SceneNode` by `node_id`.
        *   Creates and executes a `ChangePropertyCommand` to update `node.name`.
*   **New Command Classes (`src/services/commands/change_children_order_command.py`, `src/services/commands/group_nodes_command.py`, `src/services/commands/ungroup_nodes_command.py`):**
    *   Define these new `BaseCommand` subclasses with appropriate `execute` and `undo` logic to perform the respective scene graph modifications.

### 7.4. Testing Plan

*   **Unit Tests (`tests/ui/panels/test_layers_tab.py` - New file):**
    *   **Setup:** Instantiate `LayersTab` with mocked `ApplicationModel`, `NodeController`.
    *   **Test Case: Initialization & `_update_content`:**
        *   **Arrange:** Mock `ApplicationModel.scene_root` with a complex hierarchy (plots, groups, nested groups).
        *   **Act:** Instantiate `LayersTab`. Emit `model.modelChanged`.
        *   **Assert:** Verify `QTreeWidget` accurately reflects the `SceneNode` hierarchy and properties (visible/locked state).
    *   **Test Case: Visibility Toggle:**
        *   **Arrange:** A `LayersTab` with a `PlotNode` item.
        *   **Act:** Simulate checking/unchecking the visibility checkbox for a `PlotNode` item.
        *   **Assert:** Verify `node_controller.set_node_visibility` is called with the correct node ID and state.
    *   **Test Case: Lock Toggle:**
        *   **Arrange:** A `LayersTab` with a `PlotNode` item.
        *   **Act:** Simulate checking/unchecking the lock checkbox for a `PlotNode` item.
        *   **Assert:** Verify `node_controller.set_node_locked` is called with the correct node ID and state.
    *   **Test Case: In-place Renaming:**
        *   **Arrange:** A `LayersTab` with a `PlotNode` item.
        *   **Act:** Simulate in-place editing of an item's text and committing the change.
        *   **Assert:** Verify `node_controller.rename_node` is called with the correct node ID and new name.
    *   **Test Case: Drag-and-Drop Reordering:**
        *   **Arrange:** A `LayersTab` with multiple sibling `PlotNode` items.
        *   **Act:** Simulate drag-and-drop to change the order of two items.
        *   **Assert:** Verify `node_controller.reorder_nodes` is called with the correct parent ID, source node ID, and new index.
    *   **Test Case: Grouping (via button/context menu):**
        *   **Arrange:** Select multiple `PlotNode` items in the `QTreeWidget`.
        *   **Act:** Simulate clicking a "Group" button/menu action.
        *   **Assert:** Verify `node_controller.group_nodes` is called with the selected node IDs.
    *   **Test Case: Ungrouping (via button/context menu):**
        *   **Arrange:** Select a `GroupNode` item in the `QTreeWidget`.
        *   **Act:** Simulate clicking an "Ungroup" button/menu action.
        *   **Assert:** Verify `node_controller.ungroup_node` is called with the group ID.
*   **Unit Tests (`tests/controllers/test_node_controller.py` - Existing/Modified file):**
    *   **Setup:** Instantiate `NodeController` with mocked `ApplicationModel`, `CommandManager`.
    *   **Test Case: `set_node_visibility`:**
        *   **Arrange:** Mock `ApplicationModel.scene_root.find_node_by_id`.
        *   **Act:** Call `set_node_visibility`.
        *   **Assert:** Verify `CommandManager.execute_command` is called with `ChangePropertyCommand` for `visible`.
    *   **Test Case: `set_node_locked`:** (Similar to visibility)
    *   **Test Case: `reorder_nodes`:**
        *   **Arrange:** Mock `ApplicationModel.scene_root.find_node_by_id` to return a parent node with children.
        *   **Act:** Call `reorder_nodes`.
        *   **Assert:** Verify `CommandManager.execute_command` is called with `ChangeChildrenOrderCommand`.
    *   **Test Case: `group_nodes`:** (Requires mocking `ApplicationModel.create_group_node`)
    *   **Test Case: `ungroup_node`:**
    *   **Test Case: `rename_node`:**
        *   **Arrange:** Mock `ApplicationModel.scene_root.find_node_by_id`.
        *   **Act:** Call `rename_node`.
        *   **Assert:** Verify `CommandManager.execute_command` is called with `ChangePropertyCommand` for `name`.
*   **Unit Tests (`tests/models/nodes/test_scene_node.py` - Existing/Modified file):**
    *   **Setup:** Instantiate `SceneNode`.
    *   **Test Case: `visible` and `locked` persistence:**
        *   **Arrange:** Create `SceneNode` with `visible=False`, `locked=True`.
        *   **Act:** Call `to_dict()` and `from_dict()`.
        *   **Assert:** Verify `visible` and `locked` are correctly serialized and deserialized.
*   **Unit Tests (`tests/services/commands/test_new_commands.py` - New file):**
    *   **Setup:** Instantiate new command classes (`ChangeChildrenOrderCommand`, `GroupNodesCommand`, `UngroupNodesCommand`) with mocked `ApplicationModel`.
    *   **Test Case: `execute()` and `undo()` for each new command:**
        *   **Act:** Call `execute()` and then `undo()`.
        *   **Assert:** Verify `ApplicationModel` state changes correctly and is restored on undo.
*   **Integration Tests (`tests/integration/test_layers_tab_interaction.py` - New file):**
    *   **Setup:** Launch app, load a project with a complex scene graph.
    *   **Test Case: Full Layers Tab Interaction:**
        *   **Arrange:** Select the "Layers" tab.
        *   **Act:** Toggle visibility, lock state. Drag to reorder. Group selected plots. Ungroup a group. Rename a node.
        *   **Assert:** Verify UI updates, canvas reflects changes, and undo/redo functions correctly for all actions.

### 7.5. Risks and Mitigations
*   **Risk:** Complexity of `QTreeWidget` interactions (drag-and-drop, in-place editing) leading to difficult-to-debug UI issues or crashes.
*   **Mitigation:** Extensive unit tests for `LayersTab` event handlers. Break down complex interactions into smaller, testable methods. Utilize existing `QTreeWidget` examples for robust drag-and-drop implementation.
*   **Risk:** Performance degradation with a very large number of `SceneNode`s in the `QTreeWidget`, especially during full rebuilds on `model.modelChanged`.
*   **Mitigation:** Implement optimization: initially, full rebuild. If performance becomes an issue, explore incremental updates using `QTreeWidget.dataChanged` and `QTreeWidget.modelAboutToBeReset`/`modelReset` signals, or implement a custom `QAbstractItemModel` for `QTreeView`.

---

## 8. Feature: Update Double-Click Behavior on Canvas

### 8.1. Description
When a `PlotNode` is double-clicked on the canvas, the `SidePanel` will automatically open (if not already open) and programmatically switch to the "Properties" tab. Additionally, the double-clicked plot will be set as the active selection, automatically reflecting in the `PropertiesTab`'s subplot dropdown.

### 8.2. Design Patterns Applied
*   **Observer (Signals & Slots):** `CanvasWidget` emits a signal indicating a double-click on a `PlotNode`. `MainWindow` (or `CanvasController`) observes this, and `SidePanel` observes `model.selectionChanged`.

### 8.3. Affected Files and Specific Changes
*   **`src/ui/widgets/canvas_widget.py`:**
    *   **`mouseDoubleClickEvent(event: QMouseEvent)`**:
        *   Override this method.
        *   Perform hit-testing to identify if a `PlotNode` is under the mouse cursor at the double-click position.
        *   If a `PlotNode` is identified, set `application_model.selection` to include only this `PlotNode` (and clear any other selections). This action is crucial as `model.selectionChanged` drives subsequent UI updates.
*   **`src/ui/windows/main_window.py`:**
    *   **`show_properties_panel()` (Existing method):** Rename to `show_side_panel()` to reflect the new `SidePanel`.
    *   **Connection**: Ensure that when a `PlotNode` is selected (e.g., via `CanvasWidget`'s double-click or any other selection mechanism), the `MainWindow` observes `model.selectionChanged`. If a `PlotNode` is in the new selection, call `self.side_panel.show_tab_by_name("Properties")`. This might require `MainWindow` to have a direct reference to `SidePanel` and a connection to `model.selectionChanged`.
*   **`src/ui/panels/side_panel.py`:**
    *   **Connection**: Connect `model.selectionChanged` to a new internal method `_on_selection_changed()`.
    *   **`_on_selection_changed()` (New method):**
        *   Checks if the new selection contains a `PlotNode`.
        *   If so, it calls `self.tab_widget.setCurrentIndex(0)` (assuming "Properties" is the first tab, or use `self.show_tab_by_name("Properties")`) to activate the "Properties" tab.

### 8.4. Testing Plan

*   **Unit Tests (`tests/ui/widgets/test_canvas_widget.py` - Existing/Modified file):**
    *   **Setup:** Instantiate `CanvasWidget` with mocked `ApplicationModel`. Place mock `PlotNode`s at known coordinates.
    *   **Test Case: Double-click on PlotNode:**
        *   **Arrange:** Simulate a `QMouseEvent` for a double-click at coordinates covering a mock `PlotNode`.
        *   **Act:** Call `canvas_widget.mouseDoubleClickEvent(event)`.
        *   **Assert:** Verify `application_model.selection` is updated to include the correct `PlotNode`.
    *   **Test Case: Double-click on Empty Space:**
        *   **Arrange:** Simulate a `QMouseEvent` for a double-click on empty canvas space.
        *   **Act:** Call `canvas_widget.mouseDoubleClickEvent(event)`.
        *   **Assert:** Verify `application_model.selection` remains unchanged or is cleared (depending on desired behavior for empty space double-click).
*   **Integration Tests (`tests/integration/test_canvas_double_click_interaction.py` - New file):**
    *   **Setup:** Launch the full application, load a project with a visible `PlotNode`. Ensure `SidePanel` is initially closed or on a different tab.
    *   **Test Case: Double-click Workflow:**
        *   **Act:** Use simulated mouse events to double-click on a `PlotNode` displayed on the `CanvasWidget`.
        *   **Assert:**
            *   Verify `SidePanel` appears/becomes visible.
            *   Verify the "Properties" tab is the active tab.
            *   Verify `PropertiesTab` displays the properties of the *correct* `PlotNode` (i.e., the one that was double-clicked).
*   **E2E Tests:** Part of general user workflow testing.

### 8.5. Risks and Mitigations
*   **Risk:** `CanvasWidget`'s hit-testing for `PlotNode`s is inaccurate, leading to incorrect plot selection on double-click.
*   **Mitigation:** Thorough unit tests for `CanvasWidget`'s hit-testing logic, covering overlapping plots, small plots, and plots near boundaries.
*   **Risk:** `SidePanel` fails to correctly switch tabs or `PropertiesTab` fails to update its content after a `PlotNode` is double-clicked and selected.
*   **Mitigation:** Unit tests for `SidePanel`'s `_on_selection_changed` method and `PropertiesTab`'s `_update_content` method, particularly their reactions to `model.selectionChanged` when a `PlotNode` is involved.

