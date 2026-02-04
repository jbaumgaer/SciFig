# Backlog

This document tracks the implemented and future features of the Data Analysis GUI.

---

## Implemented Features

This section describes the functionality currently available in the application.


## Epic: Project File Management

### Feature: Project File Management (`.sci` files)
**Task:** Implement a complete workflow for saving, loading, and accessing recent projects using a custom `.sci` file format.

**Background & Context:** A robust file management system is critical for a good user experience. The chosen format must handle a complex scene graph, various metadata, and potentially large datasets efficiently and safely. A single-file format is strongly preferred.

**Architectural Decisions:**
*   **Hybrid Archive Format (`.sci`):** The `.sci` file will be a zip archive containing a `project.json` for metadata and a `data/` directory for high-performance data serialization. This provides the readability of JSON for the project structure and the performance/efficiency of Parquet for the data, while avoiding the security risks of formats like `pickle`.
*   **Deserialization Strategy (Factory Pattern):** A factory function will be used to reconstruct nodes from the `project.json`. This function will read a `class_name` key from each node's dictionary and instantiate the corresponding Python class (e.g., `PlotNode`, `GroupNode`), making the process extensible.
*   **Recent Files Persistence (`QSettings`):** The `QSettings` class will be used to store a persistent, platform-agnostic list of recently opened files, providing a much more robust solution than a manual text or JSON file.

**`.sci` File Structure:**
```
my_project.sci (zip archive)
├── project.json
└── data/
    ├── {node_id_1}.parquet
    ├── {node_id_2}.parquet
    └── ...
```

**Implementation - Save Workflow:**
1.  **Controller (`save_project`):** Opens a `QFileDialog`, creates a temporary directory to stage files, iterates through the model's nodes to save data, creates `project.json` from the model's dictionary, zips the temp directory into the final `.sci` file, and cleans up.
2.  **Model (`to_dict`):** Nodes serialize their metadata. `PlotNode`s reference their data via a `data_path` (e.g., `data/node_id.parquet`) instead of embedding the data itself.

**Implementation - Open Workflow:**
1.  **Controller (`open_project`):** Opens a `QFileDialog` to select a `.sci` file. Unzips the file to a temporary directory, reads the `project.json`, and passes the resulting dictionary to the model for reconstruction. It will also handle adding the path to the recent files list.
2.  **Model (`load_from_dict`):** A new method in `ApplicationModel` will clear the current scene and then use a factory to recursively reconstruct the entire scene graph from the dictionary.
3.  **Node Deserialization (`from_dict`):** Each `SceneNode` subclass will have a `from_dict` class method. `PlotNode.from_dict` will be responsible for reading the `data_path` key and loading the corresponding Parquet file from the temporary directory into its `.data` attribute.

**Implementation - Open Recent Workflow:**
1.  **`QSettings` Management:** On successful save or open, the file path will be added to the top of a list stored in `QSettings`. The list will be capped at a reasonable number (e.g., 10).
2.  **Dynamic Menu:** The `MenuBarBuilder` will connect to the `aboutToShow` signal of the "Open Recent Projects" menu. The connected slot will clear the menu and repopulate it with `QAction`s for each path stored in `QSettings`. Clicking an action will call `open_project` with the corresponding path.

**Test Plan:**
- Unit tests for `to_dict` and `from_dict` methods on all node classes.
- Integration test for the full save workflow.
- Integration test for the full open workflow (save a file, then open it and assert the model state is identical).
- Integration test for the "Open Recent" menu logic, using a mocked `QSettings`.


### Feature: Single-File Project Save/Load (`.sci` files)
**Status:** Implemented
**Task:** Implemented the ability to save the entire application state into a single `.sci` project file.
**Architectural Decision:** A hybrid archive format was chosen. The `.sci` file is a zip archive containing a `project.json` for all metadata (scene graph, node properties, etc.) and a `data/` directory containing high-performance Parquet files for each plot's DataFrame. This provides a balance of human-readable metadata and efficient binary storage for large datasets, while avoiding the security risks of formats like `pickle`.

### Feature: MainWindow Construction Refactoring
**Status:** Implemented
**Task:** Refactor the construction of the `MainWindow` to improve type safety, readability, and maintainability. This involved eliminating the monolithic `MainWindowBuilder` and making the `MainWindow` responsible for its own construction.

### Feature: Pluggable Plot Properties and Dynamic View
**Status:** Completed
**Task:** Refactor `PlotProperties` into a hierarchical, type-specific structure and make the `PropertiesView` dynamically update its UI based on the selected plot type.
**Background & Context:** The current `PlotProperties` is a monolithic dataclass, and the plot type is a simple string. As more node types are added, this becomes difficult to maintain.

**Phase 1: Model Refactoring**
1.  **Create `PlotType` Enum:**
    *   In a new file, `src/models/plot_types.py`, define a `PlotType` enum using `enum.Enum`.
    *   `class PlotType(str, Enum): LINE = "line"; SCATTER = "scatter"` (inheriting from `str` helps with serialization if needed).
2.  **Refactor `PlotProperties` Hierarchy:**
    *   In `src/models/nodes/plot_properties.py`:
        *   Rename the existing `PlotProperties` dataclass to `BasePlotProperties`.
        *   Change its `plot_type` attribute from `str` to `PlotType`.
        *   Create new dataclasses `LinePlotProperties` and `ScatterPlotProperties`, both inheriting from `BasePlotProperties`.
        *   For now, these subclasses will be simple `pass` statements, but this establishes the required structure. For example, `ScatterPlotProperties` could later have `marker_size: int = 10`.
3.  **Update Core Model and Renderer:**
    *   In `PlotNode`, change the type hint for `plot_properties` to `Optional[BasePlotProperties]`.
    *   In the `Renderer`, change the keys of the `plotting_strategies` dictionary from strings to `PlotType` enum members (e.g., `{PlotType.LINE: LinePlotStrategy(), ...}`).
    *   In `PropertiesView`, update its `__init__` to accept `list[PlotType` and modify the `QComboBox` to be populated from this list. The `_on_plot_type_changed` signal will now emit a `PlotType` member.

**Phase 2: Dynamic View Implementation**
1.  **Create `PropertiesUIFactory`:**
    *   Create a new class `PropertiesUIFactory` in `src/views/properties_ui_factory.py`.
    *   This class will be responsible for building the specific QWidgets needed for a given `BasePlotProperties` instance.
    *   It will have a central method, e.g., `build_widgets(props: BasePlotProperties, layout: QFormLayout, command_manager: CommandManager)`.
    *   Inside `build_widgets`, it will use `isinstance` checks to determine which specific builder method to call (e.g., `if isinstance(props, ScatterPlotProperties): self._build_scatter_widgets(...)`).
    *   The specific builder methods (`_build_scatter_widgets`) will create the `QSpinBox` for `marker_size`, connect its `valueChanged` signal to a `ChangePropertyCommand`, etc.
2.  **Refactor `PropertiesView`:**
    *   In `PropertiesView.__init__`, create an instance of the `PropertiesUIFactory`.
    *   In `_build_plotnode_ui`, after creating the common widgets (Title, Labels, Plot Type dropdown), it will call `self.ui_factory.build_widgets(props, form_layout, self.command_manager)`. This delegates the creation of type-specific widgets to the factory, keeping the main view clean.

**Test Plan:**
-   Update existing tests that fail due to the `PlotProperties` and `PlotType` refactoring.
-   Write a unit test for the `PropertiesUIFactory` to ensure it calls the correct builder method for each property type.
-   Write an integration test to verify that when the user changes the `plot_type` in the `PropertiesView` dropdown, the old type-specific widgets are removed and the new ones are created correctly. For example, changing from "scatter" to "line" should make the `marker_size` editor disappear.

**Risks & Mitigations:**
-   **Risk:** The refactoring is significant and will touch many files, potentially breaking existing functionality.
-   **Mitigation:** The work is broken into two phases. After Phase 1, the application should still be fully functional before proceeding to Phase 2. The comprehensive test suite will be relied upon to catch regressions.

### Feature: Pluggable Node Renderer Strategy
**Status:** Implemented
**Task:** Refactored the main rendering loop to use a Strategy Pattern for rendering different `SceneNode` types.
**Outcome:** Simplified the `_render_node` method, making it more extensible and maintainable by delegating node-specific rendering logic to a strategy map. This adheres to the Open/Closed Principle, allowing new node types to be added without modifying existing rendering logic.

### Refactoring Task: Decouple Controller-View Initialization
**Status:** Implemented
**Task:** Refactored the application startup sequence to remove the circular dependency between `MainController` and `MainWindow`. This involved centralizing the wiring of signals and slots in `main.py`'s `setup_application` function and modifying `MainController` methods to accept a `parent` widget for `QFileDialog` calls.
**Outcome:** Achieved a linear, unidirectional, and clearer initialization process for core application components, improving maintainability and reducing the potential for bugs. All automated tests were updated and pass, confirming no regressions.

---

## Future Features Roadmap

This section outlines planned features that are not yet implemented.

### Architectural Enhancements
- **Plugin Architecture**: Develop a plugin system to allow new features (tools, plot types, import/export formats) to be added to the application dynamically without modifying the core codebase.

### Illustrator-Inspired Design & Layout Features

#### Object & Layer Management
- **Layer Panel**: A dedicated panel to manage layers (create, delete, rename, reorder, lock, toggle visibility).
- **Grouping UI**: UI controls to group and ungroup multiple objects.
- **Zoom Feature**: In the lower corner, there is a little icon and a number indicating the current level of magnification
- **Alignment & Distribution Panel**: A panel with tools to align and distribute selected objects.

#### Drawing & Annotation
- **Shape Tools**: Basic geometric shape tools for rectangles, ellipses, and lines.
- **Path Tool (Pen Tool)**: An advanced Pen tool for drawing custom Bezier curves.
- **Advanced Text Tool**: On-canvas text editing, rich text support (bold, italic), and LaTeX integration.
- **Image Import (Drag and Drop)**: Allow users to drag and drop image files (e.g., PNG, JPG) directly onto a Matplotlib subplot. The application would load the image data as a NumPy array (e.g., using Pillow and NumPy) and display it within that subplot using Matplotlib, allowing for easy integration of images into figures.

#### Styling & Appearance
- **Strokes, Fills, and Gradients**: Detailed controls for object appearance (line styles, fill colors, gradients).
- **Eyedropper Tool**: A tool to pick a style from one object and apply it to another.
- **Reusable Styles/Templates**: Allow users to save appearance properties as named styles.

### Origin-Inspired Data & Analysis Features

#### Data Management
- **Interactive Data Worksheet**: A dockable panel that shows the data of a selected plot in a spreadsheet-like table. This "worksheet" would allow for viewing, sorting, and direct manipulation of the underlying data, with changes instantly reflecting on the plot.
- **Display Data Source Path**: In the properties panel, display the source file path for the data loaded in a plot, with an option to change or reload the data.
- **Folder Batch Import**: Allow dragging and dropping an entire folder onto the canvas to automatically find all data files within it and create a grid of plots, one for each file.
- **Multi-Sheet Workbooks**: Support for workbooks containing multiple data sheets.
- **Data Connectors**: Support for importing from sources beyond CSV (e.g., Excel, HDF5, SQL).

#### Plotting & Data Visualization
- **Selectable Plot Types**: In the properties panel, add a dropdown to change the plot type for the selected subplot (e.g., from Line to Scatter, Bar, etc.).
- **Multi-Axis Plots**: Support for plots with multiple Y-axes or linked X-axes.
- **Trellis/Facet Plots**: Automatically generate a grid of plots based on categories in the data.

#### Data Analysis & Fitting
- **Analysis Gadgets**: Interactive tools for performing quick analysis on a graph (e.g., a "Region of Interest" tool).
- **Curve Fitting Panel**: A dedicated panel for advanced curve fitting with built-in and user-defined functions.
- **Signal Processing**: Basic signal processing tools like smoothing, filtering, and FFT.

### General Application Features

- **Project Files**: The ability to save and load the entire workspace into a single project file.
- **Export Engine**: High-quality vector (SVG, PDF, EPS) and raster (PNG, TIFF) export.
- **Templating**: Allow an entire project layout to be saved and reused as a template.
- **File Paths**: Use the pathlib library to handle paths, instead of strings

---

## Proposed Refactoring Roadmap

This section tracks agreed-upon architectural improvements to enhance code quality and maintainability.

### Refactoring Task: Enhance Tool Management Architecture
**Status:** Implemented
**Task:** Refactor the core tool management and event dispatching mechanism to support a pluggable and extensible tool system.

**Background & Context:** The current `CanvasController` directly handles canvas events, which will lead to unmaintainable `if/elif/else` chains as more interactive tools are introduced. The `ToolManager` is currently a basic container. To support a rich toolbar and interactive tools, a more robust, decoupled architecture is required.

**Proposed Solution:** Implement a Strategy-like pattern where the `ToolManager` acts as the context, and individual tools are strategies that handle specific user interactions. The UI will trigger state changes in the `ToolManager`, and the UI will react to signals from the `ToolManager`.

**Implementation Plan:**

1.  **Create `src/controllers/tools/base_tool.py`:**
    *   Define an abstract base class `BaseTool` (inheriting from `ABC` from `abc` module and `QObject` from `PySide6.QtCore`).
    *   It will have an `__init__` method accepting `model: ApplicationModel`, `command_manager: CommandManager`, and `canvas_widget: CanvasWidget`.
    *   Define abstract methods that all tools must implement. These include:
        *   `name(self) -> str` (property: unique name of the tool, e.g., "selection")
        *   `icon_path(self) -> str` (property: path to the tool's icon)
        *   `on_activated(self)`: Called when the tool becomes active.
        *   `on_deactivated(self)`: Called when the tool becomes inactive.
        *   `mouse_press_event(self, event: QMouseEvent)`
        *   `mouse_move_event(self, event: QMouseEvent)`
        *   `mouse_release_event(self, event: QMouseEvent)`
        *   `key_press_event(self, event: QKeyEvent)` (Optional, with a default no-op implementation)
        *   `paint_event(self, painter: QPainter)` (Optional, for tools that need to draw temporary overlays on the canvas)

2.  **Refactor `src/controllers/tool_manager.py`:**
    *   Add a `_tools: Dict[str, BaseTool]` attribute to store registered tools.
    *   Add a `_active_tool_name: str | None` attribute to track the currently active tool.
    *   Add a `activeToolChanged = Signal(str)` to emit when the active tool changes.
    *   Modify `add_tool(self, name: str, tool: BaseTool)` to store the tool.
    *   Modify `set_active_tool(self, tool_name: str)`:
        *   If an old tool was active, call `old_tool.on_deactivated()`.
        *   Set the new active tool.
        *   Call `new_tool.on_activated()`.
        *   Emit `self.activeToolChanged.emit(tool_name)`.
    *   Add methods to dispatch canvas events to the active tool:
        *   `dispatch_mouse_press_event(self, event: QMouseEvent)` -> `self.active_tool.mouse_press_event(event)`
        *   `dispatch_mouse_move_event(self, event: QMouseEvent)` -> `self.active_tool.mouse_move_event(event)`
        *   `dispatch_mouse_release_event(self, event: QMouseEvent)` -> `self.active_tool.mouse_release_event(event)`
        *   `dispatch_key_press_event(self, event: QKeyEvent)` -> `self.active_tool.key_press_event(event)`

3.  **Refactor `src/controllers/canvas_controller.py`:** EDIT: This is where we left off last time
    *   Remove all event handling logic (mouse presses, moves, releases) from `CanvasController` itself.
    *   Its `__init__` will now take `tool_manager: ToolManager` as an argument.
    *   Connect the `canvas_widget`'s event signals directly to the `tool_manager`'s dispatch methods (e.g., `canvas_widget.mousePress.connect(tool_manager.dispatch_mouse_press_event)`).
    *   The `CanvasController` effectively becomes a pure event *forwarder* to the `ToolManager`.

4.  **Refactor `src/controllers/tools/selection_tool.py`:**
    *   Make `SelectionTool` inherit from `BaseTool`.
    *   Implement all abstract methods defined in `BaseTool`.
    *   Move its current event handling logic into the corresponding `BaseTool` methods.
    *   Ensure `SelectionTool.name` property returns "selection".

**Test Plan:**
-   Unit tests for `BaseTool` (ensure abstract methods are enforced).
-   Unit tests for `ToolManager`:
    *   `add_tool` correctly registers tools.
    *   `set_active_tool` correctly activates/deactivates tools and emits `activeToolChanged` signal.
    *   Event dispatch methods correctly call the active tool's methods.
-   Unit tests for `CanvasController`: Ensure it correctly forwards events to `ToolManager`.
-   Unit tests for `SelectionTool`: Ensure it correctly implements `BaseTool` and its existing logic still functions.
-   Integration tests: Verify that activating a tool in `ToolManager` changes the application's behavior on the canvas as expected.

**Risks & Mitigations:**
-   **Risk:** Extensive changes to core event handling might introduce regressions.
-   **Mitigation:** A phased refactoring approach will be used, starting with `BaseTool`, then `ToolManager`, then `CanvasController`, and finally existing tools. Comprehensive unit and integration tests will be crucial at each step.
-   **Risk:** The `paint_event` method for `BaseTool` might be complex for overlay drawing.
-   **Mitigation:** Start with a simple implementation, providing the `QPainter` directly. Refine as needed for complex overlays or integrate with a dedicated overlay manager later.



1.  **Create Placeholder Icons:**
    *   Create a new directory: `src/assets/icons`.
    *   Programmatically generate simple SVG icons for each tool:
        *   `selection_tool.svg` (e.g., an arrow)
        *   `direct_selection_tool.svg` (e.g., white arrow)
        *   `shape_tool.svg` (e.g., a square)
        *   `path_tool.svg` (e.g., pen nib)
        *   `text_tool.svg` (e.g., "T")
        *   `eyedropper_tool.svg` (e.g., eyedropper)
        *   `plot_tool.svg` (e.g., simple line graph)
        *   `zoom_tool.svg` (e.g., magnifying glass)
        *   `rotate_tool.svg` (e.g., circular arrow)
        *   `figure_tool.svg` (e.g., small window icon)

2.  **Create `src/builders/tool_bar_builder.py`:**
    *   Define a `ToolBarBuilder` class.
    *   `__init__(self, parent_window: QMainWindow, tool_manager: ToolManager)`
    *   Define a `ToolBarActions` dataclass to hold references to the created `QAction`s.
    *   `build(self) -> Tuple[QToolBar, ToolBarActions]`:
        *   Create `tool_bar = QToolBar("Tools", self._parent_window)`.
        *   Set `tool_bar.setMovable(False)`, `tool_bar.setFloatable(False)`.
        *   Add `tool_bar` to `parent_window` using `self._parent_window.addToolBar(Qt.LeftToolBarArea, tool_bar)`.
        *   For each tool, create a `QAction`:
            *   Load the SVG icon (`QIcon(tool_icon_path)`).
            *   Set a tooltip (`action.setToolTip("Selection Tool")`).
            *   Set the action to be checkable (`action.setCheckable(True)`).
            *   Connect `action.triggered.connect(lambda checked, tool_name=tool_name: self._tool_manager.set_active_tool(tool_name))`.
            *   Add the action to the toolbar.
        *   Connect `self._tool_manager.activeToolChanged.connect(self._update_tool_bar_state)`.
        *   Return the `QToolBar` and the `ToolBarActions` dataclass.
    *   `_update_tool_bar_state(self, active_tool_name: str)`:
        *   Iterate through all tool actions in `ToolBarActions`.
        *   Set `action.setChecked(action.tool_name == active_tool_name)`.

3.  **Integrate with `main.py` (`setup_application` function):**
    *   Instantiate `ToolManager`.
    *   Instantiate `ToolBarBuilder`, passing it the `MainWindow` and `ToolManager`.
    *   Call `tool_bar_builder.build()` and store the returned toolbar and actions.
    *   Register all tools (e.g., `tool_manager.add_tool("selection", SelectionTool(...))`) after `MainWindow` is created, as the tools will need the `canvas_widget`.
    *   Ensure the `ToolManager` is passed to the `CanvasController` and any other components that need it.

4.  **Integrate with `src/views/main_window.py`:**
    *   Import `ToolBarBuilder`.
    *   Store the created `QToolBar` and `ToolBarActions` as attributes (e.g., `self.tool_bar`, `self.tool_actions`).
    *   **Crucially:** `MainWindow` itself should not instantiate the `ToolBarBuilder` directly but receive the built `QToolBar` and `ToolBarActions` from `setup_application` (similar to how `MenuBarBuilder` is handled in `MainWindow`).

**Test Plan:**
-   Unit tests for `ToolBarBuilder`:
    *   Ensure it correctly creates a `QToolBar` and all `QAction`s.
    *   Verify icons, tooltips, and checkable states are set.
    *   Test that `_update_tool_bar_state` correctly sets the checked state of actions.
-   Integration tests:
    *   Run the application, click toolbar buttons, and verify that the `ToolManager`'s active tool changes.
    *   Verify that when the active tool changes (e.g., programmatically via `tool_manager.set_active_tool()`), the correct toolbar button becomes checked.
    *   Verify that placeholder icons are correctly displayed.

**Risks & Mitigations:**
-   **Risk:** Managing SVG icons might require `PySide6.QtSvgWidgets` or similar, adding a dependency.
-   **Mitigation:** Verify if `QIcon` can load SVGs directly. If not, consider a simpler icon format or add `QtSvgWidgets`.
-   **Risk:** The `setup_application` function in `main.py` is becoming quite large due to all the wiring.
-   **Mitigation:** This is acceptable for a "composition root." If it becomes unwieldy, a dedicated `ApplicationBuilder` class could be introduced later to encapsulate `setup_application`'s logic.

1. The "God Function" Composition Root (`setup_application`): As we've discussed, this function in main.py is doing far too much. It's not  
      just a composition root; it's the entire factory, assembler, and wiring diagram in one monolithic, fragile block of code. This is a major
      violation of the Single Responsibility Principle.


   2. Prevalence of "Magic Strings": The code relies heavily on hard-coded strings to identify key entities:
       * Tool Names: "selection", "direct_selection", etc., are used in builders, the tool manager, and for setting the active tool. A typo in 
         any of these strings would introduce a silent failure or a difficult-to-debug KeyError.
       * Icon Paths: Paths like "src/assets/icons/toolbar/Select.svg" are hard-coded. If the asset structure changes, these strings must be    
         hunted down and changed individually.
       * Object Names: Qt objects are sometimes identified with strings (e.g., dock.setObjectName("Properties")).


   3. Scattered Configuration and "Magic Numbers": Configuration values are spread throughout the codebase. For example, the default figure    
      properties (figsize=(8.5, 6), dpi=150) are hard-coded directly in main.py. This makes it difficult to manage or change application-wide  
      settings consistently.


   4. Implicit Contracts between Components: The relationship between a PlotNode's properties (like LinePlotProperties) and the UI that can    
      edit them (PropertiesView and PropertiesUIFactory) is implicit. The PropertiesUIFactory uses isinstance checks to decide which widgets to
      build. While functional, this approach violates the Open/Closed Principle: to add a new plot type, you must modify the factory class     
      itself. As the number of plot types grows, this will become a large, complex if/elif/else block.


   5. Business Logic in Controllers: The MainController currently handles the logic for saving and loading projects, including file dialogs and
      potentially, in the future, the details of zipping/unzipping and JSON serialization. While simple now, this mixes UI-coordination logic  
      (handling a menu click) with data persistence logic (the details of the .sci file format).

  Anticipating Future Expansion: A Strategy for Scalability


  To ensure the codebase is prepared for significant future expansion, I will integrate the following strategic principles into the "Clean     
  Application Composition" refactoring. This isn't about adding more work now, but about doing the current refactoring the right way to        
  establish robust patterns.

  Strategy 1: Eradicate Magic Strings with Enums and Constants

  As we refactor, we will stop using raw strings for identification.


   * Proposal: Introduce a new file, src/constants.py (or a src/config/ package), to house application-wide constants and enumerations.        
   * Implementation Example:


    1     # src/constants.py
    2     from enum import Enum
    3
    4     class ToolName(str, Enum):
    5         SELECTION = "selection"
    6         DIRECT_SELECTION = "direct_selection"
    7         EYEDROPPER = "eyedropper"
    8         # ... etc.
    9
   10     class IconPath:
   11         SELECT_TOOL = "src/assets/icons/toolbar/Select.svg"
   12         # ... etc.
   * How it will be used: The ToolBarBuilder and ToolManager will now use ToolName.SELECTION instead of "selection". This provides a single    
     source of truth, enables static analysis and auto-complete, and makes refactoring safe and trivial.


  Strategy 2: Establish a Centralized Configuration Service (Dependency Injection)

  We will lay the groundwork for the Pydantic configuration system mentioned in the TDD.

   * Proposal: Create a simple, dedicated configuration service that is responsible for providing all system-wide settings.
   * Implementation Example:


   1     # src/services/config_service.py (New File)
   2     class ConfigService:
   3         DEFAULT_FIGURE_SIZE = (8.5, 6)
   4         DEFAULT_DPI = 150
   * How it will be used: The new ApplicationAssembler will be the only place that instantiates ConfigService. It will then inject this service
     (or specific values from it) into any component that needs them. The Figure creation will become
     Figure(figsize=config.DEFAULT_FIGURE_SIZE, dpi=config.DEFAULT_DPI). This removes magic numbers and establishes the correct dependency     
     injection pattern for all future configuration needs.

  Strategy 3: Formalize the UI Factory with a Registration Pattern

  We will improve the PropertiesUIFactory to make it truly extensible, adhering to the Open/Closed Principle.


   * Proposal: Instead of a large isinstance block, the factory will have a registration mechanism. It will maintain a dictionary that maps a  
     PlotType enum to a function responsible for building the corresponding UI widgets.
   * Implementation Example:


    1     # src/views/properties_ui_factory.py (Refactored)
    2     class PropertiesUIFactory:
    3         def __init__(self):
    4             self._builders = {}
    5
    6         def register_builder(self, plot_type: PlotType, builder_func: Callable):
    7             self._builders[plot_type] = builder_func
    8
    9         def build_widgets(self, props: BasePlotProperties, ...):
   10             builder = self._builders.get(props.plot_type)
   11             if builder:
   12                 builder(props, ...) # Call the registered function
   * How it will be used: The ApplicationAssembler will be responsible for this registration. It will import the specific widget-building      
     functions and register them with the factory instance. To add UI for a new plot type, a developer will only need to create a new builder  
     function and add a single registration line in the ApplicationAssembler, without ever modifying the factory itself.

     The `ApplicationAssembler` uses an initialization pattern where many attributes are set to `None` initially, and then populated sequentially by various `_assemble_` methods within its `assemble()` method. While this might initially seem to lead to an uninitialized state, it's a common and effective design pattern for a "composition root" or "dependency injector" in applications of this nature.

Here's a breakdown of why this approach is used and how it mitigates potential issues:

**Purpose of the ApplicationAssembler:**
The `ApplicationAssembler`'s primary role is to orchestrate the creation and wiring of all the application's components (models, controllers, views, tools). It acts as a central hub where dependencies are resolved, and the entire application graph is constructed in a controlled manner.

**Advantages of this Initialization Pattern:**
1.  **Clear Separation of Concerns:** Each `_assemble_` method (e.g., `_assemble_core_components`, `_assemble_menus`, `_assemble_tooling`) is responsible for building a specific, logical part of the application. This makes the code easier to understand, maintain, and reason about.
2.  **Controlled Initialization Order:** The `assemble()` method explicitly defines the sequence in which components are built. This is crucial for managing dependencies; for instance, the `ApplicationModel` (which is a core component) must be assembled before the `MenuBarBuilder` can be instantiated if it depends on the model.
3.  **Reduced Circular Dependencies:** By centralizing the creation and wiring of components, this pattern helps prevent scenarios where components might try to instantiate each other directly, potentially leading to circular dependencies.
4.  **Single Point of Configuration:** All major application components are instantiated and connected in one place. This simplifies understanding the application's overall structure and how its various parts interact.
5.  **Facilitates Testing:** While the assembler itself might be complex, individual `_assemble_` methods and the components they create can often be tested more easily in isolation.

**Mitigation of "Not Fully Initialized State" Concern:**
Your concern about a "not fully initialized state" is valid if the `ApplicationAssembler`'s attributes were accessed before the `assemble()` method completes or if `assemble()` were not guaranteed to run to completion. However, in the current design:
*   The `assemble()` method is designed to be called once, at the application's startup (`main.py` calls `setup_application()`, which in turn calls `assembler.assemble()`).
*   The `assemble()` method ensures that all necessary `_assemble_` sub-methods are called sequentially.
*   The `ApplicationAssembler` instance itself is primarily an internal build mechanism. After `assemble()` completes, it returns a fully formed `ApplicationComponents` object. It's this `ApplicationComponents` object, containing all the fully initialized and wired parts of the application, that is then used by the rest of the application. This ensures that any code interacting with the application's components will always receive fully initialized objects.

In summary, for an application like this, which has multiple interconnected components, this pattern provides a robust and organized way to manage complexity and ensure that the application starts in a consistent, fully configured state. The initial `None` assignments are merely placeholders that are guaranteed to be populated by the time the `assemble()` method finishes and the `ApplicationComponents` object is returned.