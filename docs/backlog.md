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

 ✓ Refactor src/views/properties_ui_factory.py: Change PropertiesUIFactory from a static class to an instance-based class.
 ✓ Refactor src/views/properties_ui_factory.py: Add __init__(self) method to initialize self._builders = {}.
 ✓ Refactor src/views/properties_ui_factory.py: Implement register_builder(self, plot_type: PlotType, builder_func: Callable) to store builder 
   functions in self._builders.
 ✓ Refactor src/views/properties_ui_factory.py: Modify create_ui (rename to build_widgets) to accept self and use
   self._builders.get(props.plot_type) to retrieve and call the appropriate builder function.
 ☐ Refactor src/views/properties_ui_factory.py: Extract common UI building logic into a default builder function or helper methods.
 ☐ Create Plot-Specific UI Builder Functions: For each PlotType (e.g., PlotType.LINE, PlotType.SCATTER), create a dedicated function
   encapsulating UI logic.
 ☐ Update src/application_assembler.py: Instantiate PropertiesUIFactory within ApplicationAssembler.
 ☐ Update src/application_assembler.py: Register the plot-specific UI builder functions with the PropertiesUIFactory instance.
 ☐ Update src/views/main_window.py: Modify the MainWindow's constructor or setup method to accept the PropertiesUIFactory instance.
 ☐ Update src/views/main_window.py: Ensure that wherever PropertiesUIFactory.create_ui was previously called, it now calls
   factory_instance.build_widgets.
 ☐ Unit Test PropertiesUIFactory instantiation (__init__).
 ☐ Unit Test PropertiesUIFactory.register_builder: Ensure builder functions are correctly stored.
 ☐ Unit Test PropertiesUIFactory.build_widgets with registered builders: Assert correct builder function is called.
 ☐ Unit Test PropertiesUIFactory.build_widgets with unregistered builders: Ensure graceful handling.
 ☐ Unit Test plot-specific builder functions directly.
 ☐ Integration Test ApplicationAssembler: Verify correct instantiation and registration of PropertiesUIFactory and builders.
 ☐ End-to-End Test: Run existing user workflow tests to ensure no regressions.

 ---

## Epic: Configuration Management

This epic focuses on externalizing various application settings, user preferences, and content layouts into configurable files, moving away from hardcoded values. This enhances flexibility, maintainability, and user customizability, ensuring the application scales gracefully for future features.

### Feature: Application-Level Defaults (Base Configuration)
**Description:** Externalize application-wide default settings, "magic strings", and initial values into a `configs/default_config.yaml` file. This provides a stable, easily modifiable baseline for the application's core behavior, independent of code changes.

**Planned Implementation:**

1.  **Create `configs/default_config.yaml`:**
    *   **Task:** Create a new directory `configs/` in the project root.
    *   **Task:** Create the `default_config.yaml` file within `configs/`.
    *   **Task:** Populate `default_config.yaml` with the following initial structure and example values. This structure includes application metadata, UI/window defaults, Matplotlib figure defaults, layout/grid defaults, paths/resources, processing defaults, tool defaults, and debugging options.
        ```yaml
        # Application Metadata
        app_name: "SciFig"
        version: "1.0.0"
        organization: "YourOrganization" # Used for QSettings
        website: "https://www.scifig.org"
        authors:
          - "Your Name"
        license: "MIT"

        # UI/Window Defaults
        window_title_prefix: "SciFig - "
        default_window_geometry:
          x: 50
          y: 50
          width: 800
          height: 600
        default_toolbar_area: "LeftToolBarArea" # Corresponds to Qt.ToolBarArea.LeftToolBarArea
        default_dock_widget_area_properties: "RightDockWidgetArea" # Corresponds to Qt.DockWidgetArea.RightDockWidgetArea
        default_dock_widget_area_history: "LeftDockWidgetArea" # Example for future
        splash_screen_path: "src/assets/images/splash.png" # Example for future
        theme: "dark" # "dark", "light", etc.

        # Matplotlib Figure Defaults
        figure:
          default_width: 8.5
          default_height: 6
          default_dpi: 150
          default_facecolor: "white"
          default_edgecolor: "black" # Example for future
          subplot_left: 0.125 # Example for future
          subplot_right: 0.9 # Example for future
          subplot_bottom: 0.11 # Example for future
          subplot_top: 0.88 # Example for future
          subplot_wspace: 0.2 # Example for future
          subplot_hspace: 0.2 # Example for future
          axes_facecolor: "white" # Example for future
          axes_edgecolor: "black" # Example for future
          font_family: "sans-serif" # Example for future
          font_size: 10 # Example for future
          line_width: 1.0 # Example for future
          marker_size: 6.0 # Example for future

        # Layout & Grid Defaults
        layout:
          default_margin: 10
          default_gutter: 5
          max_recent_files: 10
          default_template: "2x2_default.json" # Points to a file in configs/layouts

        # Paths & Resources
        paths:
          icon_base_dir: "src/assets/icons"
          layout_templates_dir: "configs/layouts"
          project_extension: ".sci"
          default_save_location: "~Documents/SciFig Projects" # Default for user, can be overridden by QSettings

        # Processing Defaults
        processing:
          default_delimiter: "\t"
          default_comment_char: "#"
          max_file_size_mb: 100
          max_lines_preview: 1000

        # Tool Defaults
        tool:
          default_active_tool: "Selection" # Name of the tool
          selection:
            default_color: "red"
          zoom:
            zoom_factor: 1.15
            scroll_factor: 1 # In units of notches

        # Debugging/Developer Options
        debug:
          log_level: "INFO" # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
          enable_dev_tools: false
          show_perf_metrics: false
        ```

2.  **Add `PyYAML` to Dependencies:**
    *   **Task:** Add `pyyaml` to `requirements.txt`.
    *   **Task:** Add `PyYAML` to `pyproject.toml` (if using Poetry/Flit).

3.  **Create `src/config_service.py`:**
    *   **Task:** Create a new file `src/config_service.py`.
    *   **Task:** Implement a `ConfigService` class in this file.
        *   It should be responsible for loading the `default_config.yaml` at initialization.
        *   Implement a method `get(key_path: str, default=None)` that allows accessing nested configuration values using a dot-separated string (e.g., `config.get("figure.default_width")`).
        *   Consider making it a singleton or a module-level instance for easy access, or passing it via dependency injection.
        *   Handle file not found or parsing errors gracefully, falling back to hardcoded defaults or raising specific exceptions.
    *   **Task:** Create basic unit tests for `ConfigService` (e.g., `tests/test_config_service.py`) to ensure it loads and retrieves values correctly.

4.  **Modify `src/application_assembler.py`:**
    *   **Task:** Import `ConfigService`.
    *   **Task:** In `ApplicationAssembler.__init__`, instantiate `ConfigService`.
    *   **Task:** In `_assemble_core_components`, modify the `figure` creation to use values from `ConfigService`:
        ```python
        # old: figure = Figure(figsize=(8.5, 6), dpi=150, facecolor='white')
        # new:
        figure_width = self._config_service.get("figure.default_width", 8.5)
        figure_height = self._config_service.get("figure.default_height", 6)
        figure_dpi = self._config_service.get("figure.default_dpi", 150)
        figure_facecolor = self._config_service.get("figure.default_facecolor", "white")
        figure = Figure(figsize=(figure_width, figure_height), dpi=figure_dpi, facecolor=figure_facecolor)
        ```
    *   **Task:** Pass the `ConfigService` instance to other components (e.g., `ApplicationModel`, `MainController`) that will need access to application defaults during their construction.

5.  **Refactor `src/constants.py`:**
    *   **Task:** Modify `IconPath` and `ToolName` (and any other constants) to retrieve their values from the `ConfigService` instance (passed in or accessed globally if singleton). This might involve changing their implementation to be more dynamic (e.g., functions that return paths based on config).
    *   **Task:** Remove hardcoded values that are now in `default_config.yaml`.

6.  **Modify `src/controllers/main_controller.py`:**
    *   **Task:** Update `__init__` to accept the `ConfigService` instance.
    *   **Task:** Store `ConfigService` as a member variable `self._config_service`.
    *   **Task:** Replace hardcoded values for `default_margin`, `default_gutter`, and `MAX_RECENT_FILES` with values retrieved from `ConfigService`.

**Testing Plan:**
*   **Unit Tests (`tests/test_config_service.py`):**
    *   Verify `ConfigService` loads valid YAML.
    *   Test `get()` method for various key paths (nested, non-existent, default values).
    *   Test error handling for invalid YAML or non-existent files.
*   **Integration Tests (`tests/test_application_assembler.py`, `tests/test_main_window.py`):**
    *   Verify `ApplicationAssembler` successfully initializes `ConfigService` and uses its values for `Figure` creation (e.g., check `figure.get_figwidth()` after assembly).
    *   Verify `main_controller` uses config values for layout defaults.
    *   Ensure the application starts up correctly and the UI elements (e.g., toolbars) are initialized with paths/names derived from the config.
*   **Manual Verification:**
    *   Change values in `default_config.yaml` (e.g., default window size, figure facecolor) and verify that the application reflects these changes on startup.

**Risks & Mitigations:**
*   **Risk:** Circular dependencies if `ConfigService` tries to access components that depend on it during its own initialization.
*   **Mitigation:** `ConfigService` should only load and provide data; it should not depend on other application components. Its instantiation should happen very early in `ApplicationAssembler`.
*   **Risk:** Performance overhead if config values are re-read excessively.
*   **Mitigation:** Load the config once at startup and pass around the `ConfigService` instance. Cache values internally if necessary.
*   **Risk:** Errors due to incorrect key paths or missing values.
*   **Mitigation:** `ConfigService.get()` should provide robust default value handling. Consider a validation layer (e.g., Pydantic model for the config itself) for the `default_config.yaml` to ensure it always conforms to an expected schema.

### Feature: Customizable UI Layout (User-Level Preferences)
**Description:** Enable the application to save and restore the user's preferred main window geometry, toolbar positions, and dock widget states using Qt's `QSettings` mechanism. This ensures a persistent and personalized workspace.

**Planned Implementation:**

1.  **Modify `src/views/main_window.py`:**
    *   **Task:** Import `QSettings` from `PySide6.QtCore` and `QCloseEvent` from `PySide6.QtGui`.
    *   **Task:** In `MainWindow.__init__`:
        *   Instantiate `self.settings = QSettings(self._config_service.get("organization"), self._config_service.get("app_name"))`. The organization and app name should come from `ConfigService`.
        *   **Task:** After all dock widgets and toolbars have been added to the `QMainWindow` (this is crucial for `restoreState()` to work correctly), attempt to restore the state:
            ```python
            # ... after self.setCentralWidget, self.addToolBar, self.addDockWidget calls ...

            # Restore geometry and state
            geometry = self.settings.value("mainWindowGeometry")
            if geometry:
                self.restoreGeometry(geometry)
            else: # Apply default geometry if no saved state
                default_geom = self._config_service.get("default_window_geometry")
                if default_geom:
                    self.setGeometry(default_geom["x"], default_geom["y"], default_geom["width"], default_geom["height"])

            state = self.settings.value("mainWindowState")
            if state:
                self.restoreState(state)
            else: # Apply default toolbar/dock areas if no saved state
                # This would involve explicitly setting default toolbar and dock widget areas
                # if they were not set during their initial creation.
                # Since toolbars and dock widgets are already added with default positions,
                # this 'else' block might be primarily for future complex default layouts.
                pass # For now, relying on initial placement from Assembler
            ```
    *   **Task:** Override `MainWindow.closeEvent(self, event: QCloseEvent)`:
        ```python
        class MainWindow(QMainWindow):
            # ...
            def closeEvent(self, event: QCloseEvent):
                self.settings.setValue("mainWindowGeometry", self.saveGeometry())
                self.settings.setValue("mainWindowState", self.saveState())
                super().closeEvent(event)
        ```
    *   **Task:** Update `MainWindow.__init__` signature to accept `config_service: ConfigService`.
    *   **Task:** Store `config_service` as a member variable `self._config_service`.

2.  **Modify `src/application_assembler.py`:**
    *   **Task:** Pass the `ConfigService` instance to the `MainWindow` constructor.

**Testing Plan:**
*   **Manual Verification:**
    *   Run the application. Resize and reposition the main window. Move and resize dock widgets. Close the application. Re-open and verify that the window and dock widget layout are restored to their previous state.
    *   (Optional) Delete the `QSettings` file/registry entry for SciFig to verify that default geometry is applied on first run.
*   **Integration Tests:**
    *   A simple integration test could launch the application, programmatically move/resize elements, simulate close, and then relaunch to assert the state is restored. This might be complex for initial implementation.

**Risks & Mitigations:**
*   **Risk:** `restoreState()` might not work correctly if dock widgets or toolbars are not yet created when it's called.
*   **Mitigation:** Ensure `restoreState()` is called *after* all relevant UI elements have been added to the `QMainWindow` in `MainWindow.__init__`.
*   **Risk:** Conflicts between application defaults and user settings.
*   **Mitigation:** `QSettings` values should always take precedence over application defaults. The `ConfigService` provides the fallback if `QSettings` has no value.

### Feature: Externalized Content Layouts (Project-Level Templates)
**Description:** Replace the hardcoded logic for creating layouts (e.g., the "2x2 layout") with a system that loads predefined layout templates from external JSON files. This allows for flexible and extensible canvas content arrangements.

**Planned Implementation:**

1.  **Create `configs/layouts` Directory and Layout Templates:**
    *   **Task:** Create a new directory `configs/layouts` in the project root.
    *   **Task:** Create `2x2_default.json` (and potentially other layout files like `vertical_split.json`) within `configs/layouts`.
    *   **Task:** Populate `2x2_default.json` with a serialized `GroupNode` structure, similar to the `.sci` file content but only containing the layout definition.
        ```json
        {
          "type": "GroupNode",
          "name": "2x2 Layout",
          "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}, # Full canvas
          "children": [
            {
              "type": "PlotNode",
              "name": "Plot 1",
              "geometry": { "x": 0.0, "y": 0.0, "width": 0.5, "height": 0.5 },
              "plot_properties": { /* default properties, e.g., line color, style */ }
            },
            {
              "type": "PlotNode",
              "name": "Plot 2",
              "geometry": { "x": 0.5, "y": 0.0, "width": 0.5, "height": 0.5 },
              "plot_properties": { /* default properties */ }
            },
            {
              "type": "PlotNode",
              "name": "Plot 3",
              "geometry": { "x": 0.0, "y": 0.5, "width": 0.5, "height": 0.5 },
              "plot_properties": { /* default properties */ }
            },
            {
              "type": "PlotNode",
              "name": "Plot 4",
              "geometry": { "x": 0.5, "y": 0.5, "width": 0.5, "height": 0.5 },
              "plot_properties": { /* default properties */ }
            }
          ]
        }
        ```
    *   **Task:** Ensure the `plot_properties` within the template are suitable defaults or placeholders.

2.  **Modify `src/controllers/main_controller.py`:**
    *   **Task:** Update `__init__` to accept the `ConfigService` instance.
    *   **Task:** Store `ConfigService` as a member variable `self._config_service`.
    *   **Task:** Refactor `create_new_layout()`:
        *   Get the `default_template` path from `self._config_service.get("layout.default_template")`.
        *   Construct the full path to the template file using `pathlib` and `self._config_service.get("paths.layout_templates_dir")`.
        *   Load and parse the JSON file.
        *   Use `scene_node.node_factory(template_data)` (from `src/models/nodes/scene_node.py`) to deserialize the JSON into a `GroupNode`.
        *   Clear the existing `self._model.scene_root` and replace it with the loaded `GroupNode` (or append the children of the loaded `GroupNode` to the existing root).
        *   Emit `self._model.modelChanged.emit()`.
    *   **Task:** (Future consideration) Add a method `create_layout_from_template(template_name: str)` that takes a template name, loads the corresponding file, and applies it. This would be called from the "New figure from template" menu item.

3.  **Modify `src/application_assembler.py`:**
    *   **Task:** Pass the `ConfigService` instance to the `MainController` constructor.

**Testing Plan:**
*   **Unit Tests for `main_controller` (`tests/controllers/test_main_controller.py`):**
    *   Mock `ConfigService` to return specific template paths and data.
    *   Test `create_new_layout` to ensure it loads the correct template, deserializes it into `SceneNode` objects, and updates the `ApplicationModel`'s `scene_root` correctly.
    *   Verify `modelChanged` signal is emitted.
*   **Integration Tests:**
    *   Launch the application, create a new layout, and visually verify that the 2x2 layout (or whatever is in `2x2_default.json`) is correctly displayed.
    *   Modify `2x2_default.json` and verify the changes are reflected when a new layout is created.

**Risks & Mitigations:**
*   **Risk:** Errors in parsing JSON layout files or schema mismatches with `node_factory`.
*   **Mitigation:** Add robust error handling during JSON loading and deserialization. Use schema validation for layout JSONs if they become complex.
*   **Risk:** `plot_properties` within the template might be incomplete or conflict with application defaults.
*   **Mitigation:** Ensure `plot_properties` in templates define clear base states. The `PlotNode` constructor should merge these with its own defaults.

### Feature: Clean up "Magic Strings" (Refactor `src/constants.py`)
**Description:** Systematically replace hardcoded literal values (e.g., icon paths, tool names) across the codebase with references to configuration values provided by the `ConfigService`.

**Planned Implementation:**

1.  **Modify `src/constants.py`:**
    *   **Task:** Update `IconPath` and `ToolName` to dynamically fetch values from the `ConfigService`. This might involve changing them from simple enums to classes or functions that query the config.
    *   **Task:** Ensure `ConfigService` is accessible (e.g., passed to `constants.py` via a setter function or globally accessible if `ConfigService` is a singleton).
    *   **Task:** Remove any hardcoded strings or values that are now in `default_config.yaml`.

2.  **Iterate and Replace:**
    *   **Task:** Perform a project-wide search for hardcoded strings and values (e.g., "Selection", "Direct_Select", various paths).
    *   **Task:** Replace these with calls to `ConfigService.get()` where appropriate.
    *   **Task:** Focus initially on constants identified in the `default_config.yaml` example (e.g., `default_margin`, `default_gutter`, tool names, icon paths).

3.  **Modify other files as necessary:**
    *   **Task:** Update any file that directly uses the removed constants from `src/constants.py` to now access values via `ConfigService`.

**Testing Plan:**
*   **Regression Tests:**
    *   Run all existing unit and integration tests after each set of "magic string" replacements to ensure no functionality is broken.
*   **Manual Verification:**
    *   Visually inspect the UI to ensure icons are loading correctly, tool names are displayed as expected, and default layout behaviors match the config.

**Risks & Mitigations:**
*   **Risk:** Missing some "magic strings" or introducing typos in key paths.
*   **Mitigation:** A systematic search (e.g., using `grep` or IDE search) for literals and careful review. Unit tests for `ConfigService` will catch key path errors.
*   **Risk:** Refactoring `src/constants.py` might break many existing references.
*   **Mitigation:** Change `constants.py` incrementally, or provide backward compatibility (e.g., old constants redirect to `ConfigService` values) if the migration is too disruptive.

### Feature: Externalized Content Layouts (Project-Level Templates)
**Description:** Replace the hardcoded logic for creating layouts (e.g., the "2x2 layout") with a system that loads predefined layout templates from external JSON files. This allows for flexible and extensible canvas content arrangements. When a new layout is applied, existing plots are intelligently redistributed onto the new layout slots, preserving data where possible.

**Planned Implementation:**

1.  **Create `configs/layouts` Directory and Default Layout Template:**
    *   **Task:** Create a new directory `configs/layouts` in the project root.
    *   **Task:** Create `2x2_default.json` within `configs/layouts`.
    *   **Task:** Populate `2x2_default.json` with a serialized `GroupNode` structure, defining 4 `PlotNode` children with `geometry` and placeholder `plot_properties`. Example content:
        ```json
        {
          "type": "GroupNode",
          "name": "2x2 Layout",
          "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
          "children": [
            {
              "type": "PlotNode",
              "name": "Plot 1",
              "geometry": { "x": 0.02, "y": 0.52, "width": 0.46, "height": 0.46 },
              "plot_properties": { "plot_type": "LINE", "title": "Top-Left" }
            },
            {
              "type": "PlotNode",
              "name": "Plot 2",
              "geometry": { "x": 0.52, "y": 0.52, "width": 0.46, "height": 0.46 },
              "plot_properties": { "plot_type": "LINE", "title": "Top-Right" }
            },
            {
              "type": "PlotNode",
              "name": "Plot 3",
              "geometry": { "x": 0.02, "y": 0.02, "width": 0.46, "height": 0.46 },
              "plot_properties": { "plot_type": "SCATTER", "title": "Bottom-Left" }
            },
            {
              "type": "PlotNode",
              "name": "Plot 4",
              "geometry": { "x": 0.52, "y": 0.02, "width": 0.46, "height": 0.46 },
              "plot_properties": { "plot_type": "LINE", "title": "Bottom-Right" }
            }
          ]
        }
        ```
    *   **Task:** Ensure `plot_properties` includes suitable defaults or placeholders for new plots.

2.  **Modify `PlotProperties` and `PlotNode` for `update_from_dict`:**
    *   **Task:** In `src/models/nodes/plot_properties.py`, add a method `update_from_dict(self, data: dict, exclude_geometry: bool = False)` to `BasePlotProperties`. This method should iterate through the `data` dictionary and update the corresponding attributes of the `PlotProperties` instance. The `exclude_geometry` flag is for when we only want to update non-geometry properties during redistribution.
    *   **Task:** In `src/models/nodes/plot_node.py`, update `to_dict` to accept `exclude_geometry: bool = False` argument. This ensures that when extracting plot state, geometry can be optionally omitted.

3.  **Refactor `src/controllers/main_controller.py`:**
    *   **Task:** Modify `create_new_layout()` method:
        *   Extract existing plot data and properties (data, `PlotProperties` excluding `geometry`) from `self.model.scene_root.all_descendants()`.
        *   Clear `self.model.scene_root`'s children.
        *   Get the `default_template` name from `self._config_service.get("layout.default_template")`.
        *   Construct the full path to the template file using `pathlib` and `self._config_service.get("paths.layout_templates_dir")`.
        *   Load and parse the JSON file using `json.load()`.
        *   Use `scene_node.node_factory(template_data)` to deserialize the JSON into a `GroupNode` hierarchy (this will be the `new_layout_root_node`).
        *   Iterate through the `PlotNode`s within `new_layout_root_node`. For each new slot, try to assign an extracted plot state from the previous step (simple first-come, first-served matching).
            *   If an extracted plot state is assigned, update the `new_slot_node`'s `data` and call `new_slot_node.plot_properties.update_from_dict()` (preserving the new slot's geometry).
        *   Add `new_layout_root_node` (or its children) to `self.model.scene_root`.
        *   Emit `self.model.modelChanged.emit()`.
    *   **Task:** (Future consideration): Add a method `load_layout_template(template_name: str)` to encapsulate the loading and processing logic, to be reused by a template selection UI.

**Testing Plan:**
*   **Unit Tests (`tests/models/test_plot_properties.py`, `tests/models/nodes/test_plot_node.py`):**
    *   Verify `PlotProperties.update_from_dict` correctly updates properties and respects `exclude_geometry`.
    *   Verify `PlotNode.to_dict` correctly omits geometry when `exclude_geometry=True`.
*   **Unit Tests (`tests/controllers/test_main_controller.py`):**
    *   Mock `ConfigService` to return specific template paths and data.
    *   Mock `node_factory` to return predefined `SceneNode` hierarchies.
    *   Test `create_new_layout` to ensure:
        *   It extracts existing plot data/properties before clearing.
        *   It loads the correct template.
        *   It deserializes the template into `SceneNode` objects.
        *   It intelligently redistributes existing plot data/properties onto new slots (e.g., first N plots are assigned).
        *   It updates the `ApplicationModel`'s `scene_root` correctly.
        *   `modelChanged` signal is emitted.
        *   Handles scenarios where new layout has more/fewer slots than existing plots.
*   **Integration Tests:**
    *   Launch the application, load some data into plots, then trigger `create_new_layout`. Visually verify data is preserved and redistributed on the new 2x2 layout.
    *   Change `2x2_default.json` and verify changes are reflected.

**Risks & Mitigations:**
*   **Risk:** Errors in parsing JSON layout files or schema mismatches with `node_factory`.
*   **Mitigation:** Add robust error handling during JSON loading and deserialization. Use schema validation for layout JSONs if they become complex.
*   **Risk:** `plot_properties` within the template might be incomplete or conflict with existing plot properties.
*   **Mitigation:** Ensure `PlotProperties.update_from_dict` handles missing keys gracefully. The `PlotNode` constructor should merge template properties with its own defaults.
*   **Risk:** Complexities in correctly handling `GroupNode` vs `PlotNode` hierarchy during redistribution, especially when `all_descendants()` is used.
*   **Mitigation:** Thorough unit tests for `all_descendants()` and the redistribution logic. Ensure `node_factory` correctly rebuilds the hierarchy.


## Epic: Layout Management System


  This epic focuses on implementing a flexible, extensible, and user-friendly layout management system. It allows users to arrange plots on the canvas
  through either a structured, adaptive grid or a free-form manual mode, with dynamic UI adaptation and full undo/redo support.

  ### Feature 1: Core Layout Engine Architecture


  Description: Establish the foundational abstract LayoutEngine, concrete FreeLayoutEngine, GridLayoutEngine, the orchestrating LayoutManager, and the
  initial LayoutConfig hierarchy. This feature focuses on the underlying logic and structure, not the UI integration yet.

  Planned Implementation:


   1. Define `LayoutMode` Enum:
       * Task: Add LayoutMode(Enum) to src/constants.py with members FREE_FORM and GRID.
       * Test Consideration: N/A (Enum definition).


   2. Define Abstract `LayoutConfig` and Concrete Implementations:
       * Task: Define src/models/layout_config.py (new file) with LayoutConfig(abc.ABC) as an abstract base class. It should have an abstract property mode:
         LayoutMode.
       * Task: Implement FreeConfig(LayoutConfig) in the same file: A simple class with mode = LayoutMode.FREE_FORM.
       * Task: Implement GridConfig(LayoutConfig) in the same file:
           * Properties: rows: int = field(default=2), cols: int = field(default=2), row_ratios: List[float] = field(default_factory=list), col_ratios:
             List[float] = field(default_factory=list), margin: float = field(default=0.05), gutter: float = field(default=0.05). Use dataclasses.
           * mode = LayoutMode.GRID.
       * Test Consideration (`tests/models/test_layout_config.py` - new file):
           * Unit test: test_free_config_mode: Verify FreeConfig().mode is LayoutMode.FREE_FORM.
           * Unit test: test_grid_config_init_defaults: Verify GridConfig initializes with specified defaults.
           * Unit test: test_grid_config_init_custom: Verify GridConfig initializes with custom provided values.
           * Unit test: test_grid_config_mode: Verify GridConfig().mode is LayoutMode.GRID.


   3. Create Abstract `LayoutEngine`:
       * Task: Create src/layout_engine.py.
       * Task: Define LayoutEngine as an abc.ABC with an abstract method:



    1         from abc import ABC, abstractmethod
    2         from typing import Dict, List, Tuple, Any
    3
    4         from src.models.nodes import PlotNode
    5         from src.models.layout_config import LayoutConfig # Assuming this file now exists
    6
    7         class LayoutEngine(ABC):
    8             @abstractmethod
    9             def calculate_geometries(self, plots: List[PlotNode], layout_config: LayoutConfig) -> Dict[PlotNode, Tuple[float, float, float, float]]:
   10                 """
   11                 Calculates and returns the target (left, bottom, width, height) geometry for each PlotNode.
   12                 This method is stateless; all necessary parameters are passed via layout_config.
   13                 """
       * Test Consideration: N/A (Abstract class).


   4. Implement `FreeLayoutEngine`:
       * Task: In src/layout_engine.py, create FreeLayoutEngine inheriting from LayoutEngine.
       * Task: Implement calculate_geometries: For FreeConfig, it will simply return a dictionary mapping each PlotNode to its current plot_node.geometry
         attribute. It will act as a pass-through when layout_config is FreeConfig.
       * Task: Add public methods perform_align(nodes: List[PlotNode], edge: str) -> Dict[PlotNode, Tuple[float, float, float, float]] and
         perform_distribute(nodes: List[PlotNode], axis: str) -> Dict[PlotNode, Tuple[float, float, float, float]]. These methods will perform the geometric
         calculations for alignment and distribution, and return the new geometries. These methods will not be part of the abstract LayoutEngine interface,
         but will be exposed by FreeLayoutEngine for LayoutManager to call when in Free-Form mode.
       * Test Consideration (`tests/test_layout_engine.py` - modify/new file):
           * Unit test: test_free_layout_engine_calculate_geometries_pass_through: Verify it returns input plot geometries unmodified.
           * Unit test: test_free_layout_engine_align_left: Test with 2-3 plots, verify left edges align and other coordinates are preserved.
           * Unit test: test_free_layout_engine_distribute_horizontal: Test with 3 plots, verify even horizontal spacing.
           * Edge case: align/distribute with empty nodes list.


   5. Implement `GridLayoutEngine`:
       * Task: In src/layout_engine.py, create GridLayoutEngine inheriting from LayoutEngine.
       * Task: In __init__, accept config_service: ConfigService.
       * Task: Implement calculate_geometries:
           * It will expect GridConfig as layout_config.
           * It will determine the (rows, cols) from layout_config.
           * It will calculate the new (l, b, w, h) for each PlotNode based on GridConfig parameters (rows, cols, ratios, margins, gutters).
           * It should assign plots to grid cells based on some ordering heuristic (e.g., iterating through plot_nodes and assigning them to (0,0), (0,1),
             ..., (1,0), (1,1), ... grid cells).
           * Return the Dict[PlotNode, Rect].
       * Task: Add a public method snap_plots_to_grid(plots: List[PlotNode], current_grid_config: GridConfig) -> GridConfig: This method embodies the "Smart
         Re-Gridding with Heuristics" logic discussed. It will analyze plots' current positions, determine an appropriate rows/cols, and return an updated
         GridConfig object (with initial row_ratios/col_ratios derived from basic even distribution and potentially refined by analyzing clusterings in
         plots).
       * Test Consideration (`tests/test_layout_engine.py` - modify/new file):
           * Unit test: test_grid_layout_engine_calculate_geometries_2x2: Test with 4 plots, verify correct, non-overlapping (l,b,w,h) for a 2x2 grid.
           * Unit test: test_grid_layout_engine_calculate_geometries_1x3: Test with 3 plots, verify correct layout.
           * Unit test: test_grid_layout_engine_calculate_geometries_with_ratios: Test with custom row_ratios/col_ratios, verify correct proportional
             sizing.
           * Unit test: test_grid_layout_engine_snap_plots_to_grid_simple: Test with a few scattered plots, verify it returns a sensible GridConfig (e.g.,
             2x2 for 4 plots).
           * Unit test: test_grid_layout_engine_snap_plots_to_grid_already_grid_like: Test with plots already in a grid, verify it infers the correct
             GridConfig and approximate ratios.
           * Edge case: snap_plots_to_grid with empty plots list.


   6. Create `LayoutManager` Service:
       * Task: Create src/layout_manager.py.
       * Task: In __init__, accept application_model: ApplicationModel, free_engine: FreeLayoutEngine, grid_engine: GridLayoutEngine, config_service:
         ConfigService.
       * Task: Store references. Initialize self._application_model.current_layout_config (using FreeConfig or GridConfig based on a default from
         ConfigService).
       * Task: Implement get_active_engine() -> LayoutEngine: Returns _free_engine or _grid_engine based on application_model.current_layout_config.mode.
       * Task: Implement public methods that the MainController will call:
           * set_layout_mode(mode: LayoutMode): Updates application_model.current_layout_config.mode. If switching to GRID from FREE_FORM, it calls
             _snap_plots_to_grid.
           * perform_align(plots: List[PlotNode], edge: str) -> Dict[PlotNode, Rect]: Delegates to _free_engine.perform_align. Raises error if not in
             Free-Form mode.
           * perform_distribute(plots: List[PlotNode], axis: str) -> Dict[PlotNode, Rect]: Delegates to _free_engine.perform_distribute. Raises error if not
             in Free-Form mode.
           * apply_grid_layout_by_config(grid_config: GridConfig) -> Dict[PlotNode, Rect]: Updates application_model.current_layout_config to grid_config,
             then calls _grid_engine.calculate_geometries.
           * adjust_current_grid(rows: int | None = None, cols: int | None = None, row_ratios: List[float] | None = None, col_ratios: List[float] | None =
             None) -> Dict[PlotNode, Rect]: Updates application_model.current_layout_config (must be GridConfig) and calls
             _grid_engine.calculate_geometries.
           * get_current_layout_geometries(plots: List[PlotNode]) -> Dict[PlotNode, Rect]: Calls self.get_active_engine().calculate_geometries(plots,
             self._application_model.current_layout_config).
       * Task: Implement _snap_plots_to_grid(plots: List[PlotNode]): Calls _grid_engine.snap_plots_to_grid and updates
         application_model.current_layout_config with the returned GridConfig.
       * Test Consideration (`tests/test_layout_manager.py` - new file):
           * Unit test: test_layout_manager_init: Verify correct engine/model injection and initial config.
           * Unit test: test_set_layout_mode_free_to_grid_snaps: Mock plots, verify _snap_plots_to_grid is called and GridConfig is set.
           * Unit test: test_set_layout_mode_grid_to_free: Verify FreeConfig is set.
           * Unit test: test_perform_align_in_free_mode: Mock FreeLayoutEngine, verify delegation.
           * Unit test: test_perform_align_in_grid_mode_raises_error: Verify appropriate error/warning.
           * Unit test: test_get_current_layout_geometries_delegation: Verify calls to correct active engine.

  Risks & Mitigations (Feature 1):


   * Risk: snap_plots_to_grid heuristic is not "smart enough" and produces visually unappealing results, frustrating users during Free -> Grid transitions.
   * Mitigation: Iterative refinement of the sorting and assignment logic within snap_plots_to_grid. Provide user preference for sorting criteria (e.g., "by
     position," "by ID"). Communicate this behavior clearly in the UI. Initial implementation can be simple (e.g., sort by (x,y)) and improved later.
   * Risk: Deep nesting of calculate_geometries calls (e.g., LayoutManager calls get_active_engine which calls calculate_geometries).
   * Mitigation: This is the nature of the Strategy pattern and is acceptable. Ensure LayoutEngine.calculate_geometries is stateless and fast.
   * Risk: Overlap in responsibilities between LayoutManager and ApplicationModel regarding LayoutConfig.
   * Mitigation: ApplicationModel owns LayoutConfig (state). LayoutManager manipulates that state (logic) and triggers recalculation. This separation is
     crucial.

  ---

  ### Feature 2: Integrating Layout State & Engine with Application Model and Renderer


  Description: Update the ApplicationModel to manage LayoutConfig, and simplify the Renderer to solely draw based on plot geometries provided by the
  LayoutManager.

  Planned Implementation:


   1. Modify `ApplicationModel`:
       * Task: In src/models/application_model.py, change the _auto_layout_enabled property to _current_layout_config: LayoutConfig.
       * Task: In __init__, initialize _current_layout_config to FreeConfig() (default to free-form initially, or based on a new config default
         ui.default_layout_mode).
       * Task: Remove self._figure_subplot_params and all related tight_layout() calls from set_auto_layout_enabled.
       * Task: The set_auto_layout_enabled(self, enabled: bool) method on ApplicationModel will be removed. The layout mode will now be explicitly
         controlled by LayoutManager.set_layout_mode().
       * Task: The autoLayoutChanged = Signal(bool) signal will be replaced by layoutConfigChanged = Signal(), emitted whenever self._current_layout_config
         is set or one of its mutable properties changes (if GridConfig is mutable).
       * Task: Update to_dict() and load_from_dict() to serialize/deserialize the current_layout_config. LayoutConfig objects will need a to_dict() and
         from_dict() method, possibly using node_factory-like approach for polymorphism.
       * Test Consideration (`tests/models/test_application_model.py`):
           * Unit test: test_application_model_initial_layout_config: Verify _current_layout_config is correctly initialized.
           * Unit test: test_application_model_layout_config_serialization: Verify to_dict() and load_from_dict() correctly handle current_layout_config.


   2. Modify `Renderer`:
       * Task: Update Renderer.__init__ to accept layout_manager: LayoutManager (and remove application_model as a direct dependency for layout decisions).
       * Task: Store self._layout_manager and self._application_model (still needed for scene root, selection).
       * Task: Modify render method:
           * Always call figure.clear().
           * Get all PlotNodes from self._application_model.scene_root.all_descendants(type=PlotNode).
           * Call calculated_geometries = self._layout_manager.get_current_layout_geometries(list_of_plot_nodes).
           * Iterate plot_node and geometry from calculated_geometries.items():
               * Create ax = figure.add_axes(geometry).
               * Update plot_node.axes = ax.
               * Plot data (if plot_node.data exists) and apply plot properties to ax.
           * Crucial: If self._application_model.current_layout_config.mode == LayoutMode.GRID: call figure.set_constrained_layout(True).
           * (Optional Polishing Step): If self._application_model.current_layout_config.mode == LayoutMode.FREE_FORM and a "tighten layout" action is
             invoked, then figure.tight_layout() can be called. (This is a manual action, not part of automatic rendering by Renderer.)
       * Test Consideration (`tests/views/test_renderer.py`):
           * Unit test: test_renderer_render_free_mode: Mock LayoutManager to return explicit geometries, verify add_axes calls with correct rects.
           * Unit test: test_renderer_render_grid_mode: Mock LayoutManager to return grid-aligned geometries, verify add_axes calls and
             figure.set_constrained_layout(True) is called.
           * Unit test: test_renderer_render_no_plots: Verify graceful handling of empty plot list.


  Risks & Mitigations (Feature 2):


   * Risk: Circular dependencies during initialization (ApplicationModel needs LayoutManager for set_layout_mode if its setter calls it, LayoutManager needs
     ApplicationModel).
   * Mitigation: Refactor ApplicationModel.set_layout_mode to be called externally by MainController or LayoutManager after full assembly. The initial
     _current_layout_config is set directly in ApplicationModel.__init__. The LayoutManager should observe ApplicationModel.layoutConfigChanged and adjust
     its internal engine usage, rather than ApplicationModel calling LayoutManager.
   * Risk: Data re-plotting on every redraw causes flicker/performance issues.
   * Mitigation: This is an accepted trade-off for the dynamic nature. Performance optimizations (e.g., only updating changed axes, using Matplotlib's
     set_position) could be considered in a later iteration if profiling indicates a problem. For now, rely on figure.clear() and add_axes.

  ---

  ### Feature 3: UI Integration and User Interaction


  Description: Build the user interface elements (menus, actions) that allow users to control layout modes and perform layout operations. This leverages
  LayoutUIFactory for dynamic UI adaptation.

  Planned Implementation:


   1. Modify `default_config.yaml`:
       * Task: In the figure section, rename auto_layout_enabled_default to default_layout_mode: "FREE_FORM" or "GRID".
       * Task: In the layout section, add default_grid_rows: 2, default_grid_cols: 2, grid_margin: 0.05, grid_gutter: 0.05.
       * Task: Add a new free_form_layout section with snap_grid_unit_x: 0.01, snap_grid_unit_y: 0.01, align_offset: 0.01, distribute_spacing: 0.01.
       * Test Consideration: N/A (Config definition).


   2. Create `LayoutUIFactory`:
       * Task: Create src/views/layout_ui_factory.py.
       * Task: Implement LayoutUIFactory with a constructor taking config_service: ConfigService.
       * Task: Implement build_layout_controls(layout_mode: LayoutMode, main_controller: MainController, parent: QObject) -> List[QAction | QMenu]:
           * This method will internally use different private builder methods (_build_free_form_controls, _build_grid_layout_controls) based on
             layout_mode.
           * It will return a list of UI elements (QActions, menus) that are connected to MainController slots.
       * Task: Implement _build_free_form_controls(main_controller, parent):
           * Creates QActions for "Align Left", "Align Center", "Align Right", "Align Top", "Align Middle", "Align Bottom", "Distribute Horizontal",
             "Distribute Vertical".
           * Connects these actions to corresponding MainController slots (e.g., main_controller.align_selected_plots('left')).
           * Can optionally add a "Snap to Grid" option/dialog in this mode, linked to main_controller.snap_free_plots_to_grid().
       * Task: Implement _build_grid_layout_controls(main_controller, parent):
           * Creates QActions/sub-menus for "Set Grid Size" (e.g., 1x1, 1x2, 2x2, Custom), "Adjust Ratios".
           * Connects these actions to corresponding MainController slots (e.g., main_controller.apply_grid_layout(2,2)).
       * Test Consideration (`tests/views/test_layout_ui_factory.py` - new file):
           * Unit test: test_layout_ui_factory_build_free_form: Verify correct QActions are returned and connected.
           * Unit test: test_layout_ui_factory_build_grid_layout: Verify correct QActions/menus are returned and connected.


   3. Modify `MainController` for Layout Actions:
       * Task: Update MainController.__init__ to accept layout_manager: LayoutManager.
       * Task: Add methods for specific layout actions, delegating to layout_manager and executing BatchChangePlotGeometryCommand:
           * set_layout_mode(mode: LayoutMode): Calls layout_manager.set_layout_mode(mode).
           * align_selected_plots(edge: str): Calls layout_manager.perform_align(selected_plots, edge).
           * distribute_selected_plots(axis: str): Calls layout_manager.perform_distribute(selected_plots, axis).
           * apply_grid_layout_from_ui(rows: int, cols: int): Calls layout_manager.apply_grid_layout(...).
           * snap_free_plots_to_grid_action(): Calls layout_manager.snap_free_plots_to_grid().
           * All these methods will take the returned Dict[PlotNode, Rect] and wrap them in a BatchChangePlotGeometryCommand, executing it via
             CommandManager.
       * Test Consideration (`tests/controllers/test_main_controller.py`):
           * Unit test: test_main_controller_set_layout_mode_delegation.
           * Unit test: test_main_controller_align_delegation_command_execution.


   4. Modify `MainWindow` and Menu Builders for Dynamic Layout UI:
       * Task: In src/views/main_window.py, remove any existing QAction for "Enable Auto Layout".
       * Task: Update MainWindow.__init__ to accept layout_ui_factory: LayoutUIFactory.
       * Task: Add a QMenu for "Layout" to the MainWindow's menu bar (e.g., after "Plot" menu).
       * Task: Implement a slot _update_layout_menu(layout_mode: LayoutMode) in MainWindow.
           * This slot will clear the existing "Layout" menu.
           * It will call self._layout_ui_factory.build_layout_controls(layout_mode, self._main_controller, self) to get the new QActions/QMenus.
           * It will add these dynamically generated controls to the "Layout" menu.
       * Task: Connect layout_manager.layoutModeChanged signal to _update_layout_menu slot.
       * Task: Trigger _update_layout_menu initially in MainWindow.__init__ with the initial layout mode from ApplicationModel.
       * Test Consideration (`tests/views/test_main_window.py`):
           * Integration test: Mock LayoutManager to emit different LayoutModes. Verify MainWindow's "Layout" menu content changes dynamically.
           * Test initial menu state.

  Risks & Mitigations (Feature 3):


   * Risk: LayoutUIFactory logic becoming overly complex if too many unique UI elements per engine type.
   * Mitigation: Keep builder functions focused on creating basic Qt widgets/actions. Complex dialogs (e.g., "Custom Grid Size") could be separate, reusable
     components.
   * Risk: Ensuring QAction connections remain valid if menus are rebuilt frequently.
   * Mitigation: QActions are objects managed by Qt; as long as parent is correctly set, connections should hold. Ensure MainController methods are robust.
   * Risk: User confusion when UI elements change based on mode.
   * Mitigation: Clear visual indicators of the active layout mode (e.g., status bar, highlighted status for the "Layout Mode" toggle).

  ---

  ### Feature 4: Refactoring Application Assembler & Data Loading

  Description: Integrate the new layout architecture into the ApplicationAssembler and ensure data loading correctly triggers redraws within the new layout
  paradigm.

  Planned Implementation:


   1. Update `ApplicationAssembler`:
       * Task: In _assemble_core_components:
           * Instantiate ApplicationModel(figure, config_service).
           * Instantiate FreeLayoutEngine(config_service).
           * Instantiate GridLayoutEngine(config_service).
           * Instantiate LayoutManager(application_model, free_layout_engine, grid_layout_engine, config_service).
           * Instantiate LayoutUIFactory(config_service).
           * Instantiate Renderer(layout_manager, application_model) (note change from previous plans where it directly took app_model; now it primarily
             uses layout_manager for geometries).
       * Task: Pass LayoutManager to MainController and Renderer.
       * Task: Pass LayoutUIFactory to MainWindow.
       * Task: Adjust ApplicationComponents to include LayoutManager and LayoutUIFactory.
       * Test Consideration (`tests/test_application_assembler.py`):
           * Integration test: Verify ApplicationAssembler successfully instantiates and wires up all new layout components (LayoutManager,
             FreeLayoutEngine, GridLayoutEngine, LayoutUIFactory) with correct dependencies.
           * Test that the initial layout mode is correctly set (Free-Form or Grid) and the UI reflects this (if MainWindow's initial update slot is
             called).


   2. Refactor `CanvasController` `on_data_ready`:
       * Task: Update CanvasController.__init__ to accept layout_manager: LayoutManager.
       * Task: In on_data_ready: After node.data and node.plot_properties are set, check self._application_model.current_layout_config.mode.
       * Task: If LayoutMode.GRID is active, call self._main_controller.apply_default_grid_layout() to ensure the newly added plot is integrated into the
         grid. (This implicitly assumes MainController's method applies a default grid to all plots).
       * Test Consideration (`tests/controllers/test_canvas_controller.py`):
           * Integration test: Drag-and-drop a file in FREE_FORM mode, verify plot appears at drop location.
           * Integration test: Drag-and-drop a file in GRID mode, verify plot appears in the next available grid cell and the layout re-adjusts.


  Risks & Mitigations (Feature 4):


   * Risk: ApplicationAssembler becoming excessively large and hard to read.
   * Mitigation: Group component assembly into smaller, private helper methods within ApplicationAssembler (e.g., _assemble_layout_components()).
   * Risk: Subtle bugs due to complex initialization order and inter-component dependencies.
   * Mitigation: Extensive unit and integration tests covering component wiring and initial state. Logging at DEBUG level for all component initializations.
   * Risk: Performance overhead of layout recalculations during data loading.
   * Mitigation: The BatchChangePlotGeometryCommand will help. If profiling shows issues, consider optimizing calculate_geometries or deferring
     recalculation until interactive operations cease.


# Technical Design Document - Phase 2 Refactoring Roadmap

## Epic: Decouple Controllers and Refactor "God Objects"

**Overarching Goal:** To refactor the monolithic `MainController` and the "smart" `PropertiesPanel` into a set of smaller, cohesive controllers (`ProjectController`, `LayoutController`, `NodeController`) that adhere to the Single Responsibility Principle. This will improve architectural clarity, testability, and maintainability.

---

### Feature 1: Create New Controllers and Move Logic (Decoupling Phase)
**Description:** Create the new controller classes and move the existing business and controller logic out of `MainController` and `PropertiesPanel`. In this initial phase, the old classes will temporarily delegate calls to the new ones, ensuring the UI remains functional and allowing for isolated testing of the moved logic.

**Planned Implementation:**

1.  **Create New Controller Skeletons:**
    *   **Task:** Create `src/controllers/project_controller.py`. Define `ProjectController(QObject)` class. Ensure `QObject` is imported from `PySide6.QtCore`. Update its `__init__` to accept `model: ApplicationModel`, `command_manager: CommandManager`, `config_service: ConfigService`.
    *   **Task:** Create `src/controllers/layout_controller.py`. Define `LayoutController(QObject)` class. Ensure `QObject` is imported from `PySide6.QtCore`. Update its `__init__` to accept `model: ApplicationModel`, `command_manager: CommandManager`, `layout_manager: LayoutManager`.
    *   **Task:** Create `src/controllers/node_controller.py`. Define `NodeController(QObject)` class. Ensure `QObject` is imported from `PySide6.QtCore`. Update its `__init__` to accept `model: ApplicationModel`, `command_manager: CommandManager`.

2.  **Move Logic from `MainController`:**
    *   **Task:** Cut all project/file-related methods (`save_project`, `open_project`, `create_new_layout`, `get_recent_files`, `_add_to_recent_files`) from `src/controllers/main_controller.py` and paste them into `src/controllers/project_controller.py`.
    *   **Task:** Cut all layout-related methods (`set_layout_mode`, `toggle_layout_mode`, `align_selected_plots`, `distribute_selected_plots`, `apply_grid_layout_from_ui`, `snap_free_plots_to_grid_action`, `update_grid_parameters`, `apply_default_grid_layout`) from `src/controllers/main_controller.py` and paste them into `src/controllers/layout_controller.py`.
    *   **Task:** Update the `__init__` methods of the new controllers to accept their required dependencies (e.g., `model`, `command_manager`, `layout_manager`, `config_service`). Ensure all necessary imports are added to the new controller files.

3.  **Move Logic from `PropertiesPanel`:**
    *   **Task:** Cut all property-handling methods (`_on_plot_type_changed`, `_on_property_changed`, `_on_limit_editing_finished`, `_on_column_mapping_changed`) from `src/ui/panels/properties_panel.py` and paste them into `src/controllers/node_controller.py`.
    *   **Task:** Rename them to be public methods (e.g., `on_plot_type_changed`, `on_property_changed`). Adjust their signatures to accept the necessary parameters (e.g., `node`, `new_value`, `widget`). Ensure all necessary imports are added to the new controller file.

4.  **Create Temporary Delegations (Shim/Facade Pattern):**
    *   **Task:** In `src/controllers/main_controller.py`, keep the method signatures but change their implementation to simply instantiate the new controllers and delegate the calls to the corresponding method in `ProjectController` or `LayoutController`. The `MainController` will temporarily need to hold instances of these new controllers.
    *   **Task:** In `src/ui/panels/properties_panel.py`, keep the `_on_*` methods as private slots, but have them delegate their calls to the public methods on the new `NodeController` instance (which will be passed in during a later phase).

**Testing Plan (Feature 1):**
*   **Unit Tests:** Create new test files (`tests/controllers/test_project_controller.py`, `tests/controllers/test_layout_controller.py`, `tests/controllers/test_node_controller.py`). Adapt the relevant existing unit tests from `tests/controllers/test_main_controller.py` and `tests/ui/panels/test_properties_panel.py` to verify the logic in its new, isolated location. Mock their dependencies as needed.
*   **Regression Tests:** Run all existing integration and end-to-end tests. They should **all still pass** because the UI wiring has not changed yet, and the `MainController`/`PropertiesPanel` are just forwarding calls.

---

#### **Feature 2: Re-wire Application Dependencies in `CompositionRoot`**
**Description:** Update the `CompositionRoot` to create and inject the new, specialized controllers directly into the components that need them, bypassing and ultimately removing the monolithic `MainController`.

**Planned Implementation:**

1.  **Modify `CompositionRoot` (`src/core/composition_root.py`):**
    *   **Task:** In `_assemble_core_components` (or a new `_assemble_controllers` method), instantiate `ProjectController`, `LayoutController`, and `NodeController`, providing them with their necessary dependencies (which `CompositionRoot` already has, like `model`, `command_manager`, `config_service`, `layout_manager`).
    *   **Task:** Remove the instantiation of `MainController`.
    *   **Task:** Update the `ApplicationComponents` dataclass (in `src/core/application_components.py`) to hold references to the new controllers instead of `main_controller`.
    *   **Task:** Update the instantiation of other components (`MenuBarBuilder`, `MainWindow`, `PropertiesPanel`, `CanvasController`) to inject the new, more specific controllers instead of `main_controller`. For example:
        *   `MenuBarBuilder` will now receive `project_controller` and `layout_controller`.
        *   `MainWindow` will receive `project_controller`, `layout_controller`, and `node_controller`.
        *   `PropertiesPanel` will receive `node_controller` and `layout_controller`.
        *   `CanvasController` will receive `layout_controller`.

2.  **Modify `_connect_signals` in `CompositionRoot`:**
    *   **Task:** Update all signal connections that previously pointed to `main_controller` to now point to the correct method on the new controllers.
        *   Example: `self._view.save_project_action.triggered.connect(...)` will now connect to `self._project_controller.save_project`.
        *   Example: Connections from `PropertiesPanel` or `MainWindow` UI elements related to layout will go to `layout_controller`.

**Testing Plan (Feature 2):**
-   **Unit Tests:** Update unit tests for `CompositionRoot` to verify it correctly instantiates and injects the new controllers.
-   **Regression Tests:** Run all existing integration and end-to-end tests. They should **all still pass**, as the application should be functionally identical, just with better internal wiring.

---

#### **Feature 3: Simplify UI Components (Final Cleanup)**
**Description:** Remove the temporary delegation logic from `PropertiesPanel` and delete the `MainController` file, completing the refactor and leaving the UI components as true "views" that are driven by their respective controllers.

**Planned Implementation:**

1.  **Refactor `PropertiesPanel` (`src/ui/panels/properties_panel.py`):**
    *   **Task:** Remove the now-redundant `_on_*` delegation methods.
    *   **Task:** The `PropertiesUIFactory` (and its builder functions) will be modified to return widgets that emit semantic signals (e.g., `titleChanged(str)`). The `NodeController` (or its UI Builder, if applicable) will be responsible for creating the UI elements via the factory, and then *connecting those signals directly* to its own slots (e.g., `node_controller.on_title_changed`).
    *   **Task:** Simplify the `PropertiesPanel.__init__` method. It will receive `node_controller`, `layout_controller`, `properties_ui_factory`, and `layout_ui_factory` as dependencies, but will no longer contain direct controller logic itself. Its `_update_content` method will delegate UI construction directly to the factories, passing the appropriate controllers as context for wiring signals.

2.  **Delete `MainController`:**
    *   **Task:** Delete the file `src/controllers/main_controller.py`.

**Testing Plan (Phase 3):**
-   **Unit Tests:** Update unit tests for `PropertiesPanel` to reflect its new, simpler role as a UI container. Update tests for `PropertiesUIFactory` to ensure it returns widgets with appropriate signals.
-   **Regression Tests:** Run all integration and end-to-end tests again to ensure no functionality was broken during the final cleanup and re-wiring.

---

## Epic: Dynamic Layout UI & Enhanced Grid Interaction

**Overarching Goal:** To enhance the user experience of the Layout Management System by integrating dynamic layout controls directly into the properties panel, providing clearer mode indication, and improving the "snap to grid" functionality.

---

### Feature 1: Dynamic Properties Panel Content
**Description:** Refactor the properties panel (`PropertiesView`) to dynamically display either layout-specific controls (by default) or plot-specific properties (when a plot with data is selected).

**Planned Implementation:**
1.  **Modify `src/ui/panels/properties_panel.py`:**
    *   **Task:** Update `PropertiesPanel.__init__` to accept `layout_ui_factory: LayoutUIFactory`, `layout_manager: LayoutManager`, and `layout_controller: LayoutController`. Store these as instance variables.
    *   **Task:** Implement a slot (e.g., `_update_content(self)`) that responds to changes in `ApplicationModel.selectionChanged` and `LayoutManager.layoutModeChanged`. This method will be responsible for clearing the current content and rebuilding it based on the current state.
    *   **Task:** Within `_update_content`:
        *   Clear any existing UI elements from the properties panel.
        *   **Condition 1: Single PlotNode with Data Selected:** If `self.model.selection` contains exactly one item which is a `PlotNode` and `plot_node.data` is not `None`:
            *   Call `self.properties_ui_factory.build_properties_ui(plot_node)` to get the plot-specific controls.
            *   Add these controls to the properties panel's layout.
        *   **Condition 2: Otherwise (Default/Layout Controls):**
            *   Call `self.layout_ui_factory.build_layout_controls(self.layout_manager.layout_mode, self.layout_controller, self)` to get the layout-specific controls.
            *   Add these controls to the properties panel's layout.
    *   **Task:** In `PropertiesPanel.__init__`, connect `self.model.selectionChanged` to `self._update_content` and `self.layout_manager.layoutModeChanged` to `self._update_content`.
    *   **Task:** Trigger `self._update_content()` once at the end of `PropertiesPanel.__init__` to set the initial state.
2.  **Modify `src/core/composition_root.py`:**
    *   **Task:** When instantiating `PropertiesPanel` in `_assemble_main_window` or `_create_properties_dock` (if applicable), pass the new dependencies: `layout_ui_factory`, `layout_manager`, and `layout_controller`.
3.  **Refine `src/ui/windows/main_window.py`:**
    *   **Task:** The separate `self.layout_menu` and its associated `_update_layout_menu` slot and connections can now be removed or significantly simplified, as the primary layout controls are moving to the properties panel. The "Layout" menu might still exist in the main menu for global layout actions, but not for dynamic controls.

**Testing Plan (Feature 1):**
*   **Unit Tests (`tests/ui/panels/test_properties_panel.py`):**
    *   `test_properties_panel_displays_layout_controls_by_default`: Verify that on initialization, the `PropertiesPanel` calls `layout_ui_factory.build_layout_controls`.
    *   `test_properties_panel_displays_plot_properties_on_single_plot_selection_with_data`: Mock a selection of a single `PlotNode` with data, verify `properties_ui_factory.build_properties_ui` is called.
    *   `test_properties_panel_displays_layout_controls_on_multiple_selection`: Mock multiple `PlotNode`s selected, verify `layout_ui_factory.build_layout_controls` is called.
    *   `test_properties_panel_displays_layout_controls_on_single_plot_selection_no_data`: Mock a single `PlotNode` without data selected, verify `layout_ui_factory.build_layout_controls` is called.
    *   `test_properties_panel_updates_on_layout_mode_change`: Mock a layout mode change, verify `layout_ui_factory.build_layout_controls` is called with the new mode.

---

### Feature 2: Clearer Layout Mode Toggle & SVG Icon Integration
**Description:** Implement a more intuitive "Free Form / Grid Layout" toggle in the UI (likely in `MainWindow`'s menu bar or toolbar) and ensure all layout actions generated by `LayoutUIFactory` use SVG icons.

**Planned Implementation:**
1.  **Modify `src/ui/windows/main_window.py`:**
    *   **Task:** In `MainWindow.__init__`, create a new `QAction` (e.g., `layout_mode_toggle_action`) for toggling between Free Form and Grid layout modes. Set `checkable=True` for this action.
    *   **Task:** Set its initial `checked` state based on `self._layout_manager.layout_mode == LayoutMode.GRID`.
    *   **Task:** Connect `layout_mode_toggle_action.toggled` signal to a new slot in `layout_controller` (e.g., `layout_controller.toggle_layout_mode(checked)`).
    *   **Task:** Connect `self._layout_manager.layoutModeChanged` signal to a slot in `MainWindow` (e.g., `_update_layout_mode_toggle_ui`) that updates the `layout_mode_toggle_action`'s text and checked state.
    *   **Task:** Add this action to a suitable menu (e.g., a "View" menu, or a simplified "Layout" menu that only contains this toggle).
2.  **Modify `src/controllers/layout_controller.py`:**
    *   **Task:** Add a new method `toggle_layout_mode(self, checked: bool)`:
        *   If `checked` is `True`, call `self._layout_manager.set_layout_mode(LayoutMode.GRID)`.
        *   If `checked` is `False`, call `self._layout_manager.set_layout_mode(LayoutMode.FREE_FORM)`.
3.  **Modify `src/ui/factories/layout_ui_factory.py`:**
    *   **Task:** Update `_build_free_form_controls` and `_build_grid_layout_controls` methods to ensure all `QAction`s use SVG icons (loaded via `IconPath` from `ConfigService`) instead of plain text where appropriate. This means updating `QAction` constructors to accept `QIcon`.
    *   **Task:** Remove the "Switch to Grid Mode" and "Switch to Free-Form Mode" actions, as these are now handled by the main toggle.
4.  **Modify `src/shared/constants.py`:**
    *   **Task:** Add new constants in `IconPath` (if not already present) for all layout-related actions that will now have SVG icons (e.g., align_left, distribute_horizontal, grid_layout_on, free_layout_off).
5.  **Modify `configs/default_config.yaml`:**
    *   **Task:** Add corresponding entries for the new SVG icon paths under `paths.icon_base_dir` and `tool_icons` or a new `layout_icons` section.

**Testing Plan (Feature 2):**
*   **Unit Tests (`tests/ui/windows/test_main_window.py`):**
    *   `test_layout_mode_toggle_action_exists`: Verify the new action is created and checkable.
    *   `test_layout_mode_toggle_action_updates_layout_controller`: Verify its `toggled` signal connects to `layout_controller.toggle_layout_mode`.
    *   `test_layout_mode_toggle_action_reflects_manager_state`: Verify `_update_layout_mode_toggle_ui` correctly updates the action's checked state and text.
*   **Unit Tests (`tests/controllers/test_layout_controller.py`):**
    *   `test_toggle_layout_mode_sets_layout_manager_mode`: Verify `toggle_layout_mode` correctly calls `layout_manager.set_layout_mode`.
*   **Unit Tests (`tests/ui/factories/test_layout_ui_factory.py`):**
    *   `test_build_free_form_controls_uses_svg_icons`: Verify actions have `QIcon` objects set.
    *   `test_build_grid_layout_controls_uses_svg_icons`: Verify actions have `QIcon` objects set.

---

### Feature 3: Enhanced "Snap to Grid" Functionality
**Description:** When transitioning from free-form to grid mode, the system will automatically infer suitable grid dimensions (rows/columns) and assign existing plots to these cells.

**Planned Implementation:**
1.  **Modify `src/services/layout_manager.py`:**
    *   **Task:** In `set_layout_mode`, ensure that when transitioning from `FREE_FORM` to `GRID`, `self._grid_engine.snap_plots_to_grid(all_plots, self._create_default_grid_config())` is called. The `_create_default_grid_config()` provides base margin/gutter, but the `snap_plots_to_grid` should infer rows/cols/ratios.
    *   **Task:** Update `_application_model.current_layout_config` with the `GridConfig` returned by `snap_plots_to_grid`.
2.  **Modify `src/models/layout/layout_engines.py`:**
    *   **Task:** Refine `GridLayoutEngine.snap_plots_to_grid(self, plots: List[PlotNode], current_grid_config: GridConfig) -> GridConfig`:
        *   **Heuristic 1: Determine Rows/Cols:**
            *   Calculate `num_plots = len(plots)`.
            *   Implement a heuristic to determine `inferred_rows` and `inferred_cols`. A simple approach is `inferred_rows = max(1, round(num_plots**0.5))` and `inferred_cols = (num_plots + inferred_rows - 1) // inferred_rows`.
            *   Ensure `inferred_rows` and `inferred_cols` are at least 1.
        *   **Heuristic 2: Sort Plots for Assignment:**
            *   Sort `plots` based on their current (x,y) positions. A common stable sort is by y-coordinate (descending for top-to-bottom) then x-coordinate (ascending for left-to-right): `sorted_plots = sorted(plots, key=lambda p: (-p.geometry[1], p.geometry[0]))`.
        *   **Heuristic 3: Infer Ratios:**
            *   For initial implementation, `inferred_row_ratios = [1.0 / inferred_rows] * inferred_rows` and `inferred_col_ratios = [1.0 / inferred_cols] * inferred_cols`.
        *   **Task:** Create and return a new `GridConfig` with these `inferred_rows`, `inferred_cols`, `inferred_row_ratios`, `inferred_col_ratios`, and existing `margin`/`gutter` from `current_grid_config`.
3.  **Add Test Stubs (Feature 3):**
    *   **Unit Tests (`tests/services/test_layout_manager.py`):**
        *   `test_set_layout_mode_free_to_grid_calls_snap_and_updates_config`: Verify `_grid_engine.snap_plots_to_grid` is called and `application_model.current_layout_config` is updated to the inferred `GridConfig`.
    *   **Unit Tests (`tests/models/layout/test_layout_engines.py`):**
        *   `test_grid_layout_engine_snap_plots_to_grid_basic_inference`: Test with varying numbers of plots (0, 1, 4, 5, 6, 9) to ensure correct `rows` and `cols` are inferred.
        *   `test_grid_layout_engine_snap_plots_to_grid_sorts_plots`: Test with plots at various positions to verify correct sorting before assignment.

---

### Feature 4: Live Update Performance & Command Wrappers for Grid Parameters
**Description:** Implement smooth, interactive adjustment of grid parameters (rows, columns, margins, gutters) in the properties panel, ensuring updates are debounced and changes are undoable.

**Planned Implementation:**
1.  **Modify `src/ui/factories/layout_ui_factory.py`:**
    *   **Task:** In `_build_grid_layout_controls`, for each grid parameter UI element (e.g., `QSpinBox` for rows/cols, `QDoubleSpinBox` for margin/gutter):
        *   Connect its relevant signal (e.g., `valueChanged`, `editingFinished`) to a *single debounced slot* in `layout_controller` (e.g., `layout_controller.on_grid_parameter_changed`).
        *   The debouncing mechanism should be implemented using `QTimer.singleShot` or similar.
    *   **Task:** The debounced slot will gather the *current values of all grid parameters* from the UI controls before calling `layout_controller.adjust_grid_parameters()`.
2.  **Modify `src/controllers/layout_controller.py`:**
    *   **Task:** Add a new method `on_grid_parameter_changed(self)` (the debounced slot). This will collect the values from the UI elements (passed as a dictionary or tuple) and call `adjust_grid_parameters`.
    *   **Task:** Add or refine `adjust_grid_parameters(self, rows: int, cols: int, margin: float, gutter: float, row_ratios: List[float] | None = None, col_ratios: List[float] | None = None)`:
        *   This method will construct a new `GridConfig` with the provided parameters.
        *   It will create a new `ChangeGridParametersCommand` (see below) passing the old and new `GridConfig`.
        *   Execute the command via `self.command_manager.execute_command()`.
3.  **Create `src/services/commands/change_grid_parameters_command.py`:**
    *   **Task:** Implement `ChangeGridParametersCommand(BaseCommand)`:
        *   `__init__(self, model: ApplicationModel, old_grid_config: GridConfig, new_grid_config: GridConfig, description: str)`: Stores the model, old config, and new config.
        *   `execute(self)`: Sets `model.current_layout_config = self._new_grid_config`.
        *   `undo(self)`: Sets `model.current_layout_config = self._old_grid_config`.
4.  **Add Test Stubs (Feature 4):**
    *   **Unit Tests (`tests/ui/factories/test_layout_ui_factory.py`):**
        *   `test_grid_parameter_controls_connected_to_debounced_slot`: Verify grid parameter UI elements connect to the debounced slot in `layout_controller`.
    *   **Unit Tests (`tests/controllers/test_layout_controller.py`):**
        *   `test_adjust_grid_parameters_executes_command`: Verify `adjust_grid_parameters` creates and executes a `ChangeGridParametersCommand`.
        *   `test_on_grid_parameter_changed_debounces_calls`: Mock `QTimer.singleShot` to verify debouncing behavior.
    *   **Unit Tests (`tests/services/commands/test_change_grid_parameters_command.py`):**
        *   `test_execute_change_grid_parameters_command`: Verify `execute` correctly updates `model.current_layout_config`.
        *   `test_undo_change_grid_parameters_command`: Verify `undo` correctly restores `model.current_layout_config`.

### General Refinements/Considerations for the Epic:

*   **Error Handling and User Feedback:** Implement robust validation for user input in grid parameter fields (e.g., non-negative numbers, valid ratios). Provide clear visual feedback (e.g., invalid input highlighting, status bar messages).
*   **Default Configuration:** Add new configuration keys to `configs/default_config.yaml` for default grid parameter values (if different from existing ones) and all new icon paths.
*   **Documentation:** Update `docs/technical-design-document.md` to include this new Epic and its features. Update any other relevant documentation (`README.md`, `backlog.md`).


[ ] Extract ProjectController from Main Controller for all file-related operations (save, open, recent files).                                                    
[ ] Extract LayoutController from Main Controller and PropertiesView for managing layout modes, alignment, distribution, and grid configurations.                                     
[ ] Extract NodeController from PropertiesView managing the intrinsic attributes of selected SceneNodes. 

Implement a properties controller


* Methods become bloated, e.g. in Renderer, separation of concerns is not fully clear anymore, Single Responsibility is frequently broken --> Check code part by part for whether we adhere to the SOLID design principles, also coupling starts to be very strong
* Update the docs to give a clear view of the core classes: The MainController, the CanvasController, the ToolManager, the ApplicationModel, the DataLoader, the LayoutEngine, the MainWindow, the Renderer, the CommandManager and the ConfigService



##  Epic: Dynamic Grid Layout with constrained_layout Integration


  Description: This epic aims to enhance the application's grid layout capabilities by introducing granular control over margins and gutters, leveraging
  Matplotlib's constrained_layout for intelligent automatic spacing, and adapting the UI to expose these new controls to the user. This will lead to more
  flexible and visually appealing plot arrangements.

  ---


  Feature 1: Granular Layout Configuration Model

  Description: Extend the existing GridConfig to store individual top, bottom, left, and right margins, and to support list-based horizontal and vertical
  spacing (gutters) to align with Matplotlib's GridSpec and constrained_layout functionality.


  Planned Implementation:


   1. Modify `src/shared/types.py`:
       * Task: Update the Gutters dataclass:
           * Change hspace: float to hspace: List[float] = field(default_factory=list).
           * Change wspace: float to wspace: List[float] = field(default_factory=list).
           * Ensure to_dict() and from_dict() methods correctly handle lists.
           * Reason: To accurately represent Matplotlib's ability to define varying spacing between different rows/columns.
       * Task: Add List to import from typing.


   2. Modify `src/models/layout/layout_config.py`:
       * Task: Update the GridConfig dataclass:
           * Remove margin: float and gutter: float.
           * Add margins: Margins = field(default_factory=Margins) (using the existing Margins dataclass, which already supports top, bottom, left, right).
           * Add gutters: Gutters = field(default_factory=Gutters) (using the now-modified Gutters dataclass).
           * Reason: To directly store granular layout parameters.
       * Task: Update GridConfig.to_dict():
           * Replace margin and gutter serialization with self.margins.to_dict() and self.gutters.to_dict().
           * Reason: To serialize the new nested dataclass structure.
       * Task: Update GridConfig.from_dict():
           * Replace margin and gutter deserialization with Margins.from_dict(data.get("margins", {})) and Gutters.from_dict(data.get("gutters", {})).
           * Reason: To deserialize the new nested dataclass structure.
       * Task: Add List to import from typing.

  Testing Plan:


   * Unit Tests (`tests/shared/test_types.py`):
       * test_gutters_list_serialization: Verify Gutters.to_dict() correctly serializes lists for hspace and wspace.
       * test_gutters_list_deserialization: Verify Gutters.from_dict() correctly deserializes lists for hspace and wspace.
       * test_gutters_default_empty_lists: Verify default Gutters object has empty lists for hspace and wspace.
   * Unit Tests (`tests/models/layout/test_layout_config.py`):
       * test_gridconfig_granular_params_init: Verify GridConfig initializes with Margins and Gutters objects.
       * test_gridconfig_granular_params_to_dict: Verify GridConfig.to_dict() correctly serializes nested Margins and Gutters dictionaries.
       * test_gridconfig_granular_params_from_dict: Verify GridConfig.from_dict() correctly deserializes nested Margins and Gutters.
       * test_gridconfig_from_dict_partial_data: Verify from_dict handles missing 'margins' or 'gutters' keys gracefully, falling back to defaults.

  Risks & Mitigations:


   * Risk: Backward compatibility issues if old GridConfig JSONs/YAMLs are loaded without the new 'margins' and 'gutters' keys.
   * Mitigation: from_dict methods for Margins and Gutters use .get() with default values, ensuring older configurations can still be loaded without
     crashing (though they will revert to new defaults for margins/gutters). Documentation should highlight this change.

  ---

  Feature 2: Matplotlib constrained_layout Integration for Grid Layout


  Description: Modify GridLayoutEngine to use Matplotlib's constrained_layout for calculating plot geometries, respecting the granular margin and gutter
  configurations. This includes creating Matplotlib Axes based on GridSpec, applying the layout, and extracting the final calculated positions and spacings.

  Planned Implementation:


   1. Modify `src/models/layout/layout_engine.py`:
       * Task: Update imports: Add import matplotlib.pyplot as plt, import matplotlib.gridspec as gridspec, from matplotlib.figure import Figure, from
         matplotlib.axes import Axes, from matplotlib.transforms import Bbox.
       * Task: Refactor GridLayoutEngine.calculate_geometries():
           * Decision: This method will be deprecated or refactored to simply call apply_matplotlib_grid_layout to get the final Rect values from
             Matplotlib. It's inconsistent to have a separate calculation when Matplotlib is the renderer. For this feature, we will update it to call
             apply_matplotlib_grid_layout on a temporary figure to get the geometries.
           * Reason: To ensure all grid geometry calculations leverage Matplotlib for consistency.
       * Task: Update GridLayoutEngine.apply_matplotlib_grid_layout(self, figure: Figure, plot_nodes: List[PlotNode], grid_config: GridConfig) ->
         tuple[dict[PlotID, Axes], dict[PlotID, Rect], Margins, Gutters]:
           * Grid Dimension Calculation: Keep logic for inferring rows and cols if grid_config.rows or grid_config.cols are 0.
           * `GridSpec` Creation: Pass grid_config.gutters.hspace and grid_config.gutters.wspace directly to the gridspec.GridSpec constructor. Normalize
             row_ratios and col_ratios if they are empty or don't match dimensions.
           * Clear Figure: Add figure.clear() to ensure previous axes are removed when applying a new layout.
           * Add `Axes`: Iterate through plot_nodes (sorted by approximate current position) and add Axes to the figure using gs[r_idx, c_idx]. Store PlotID
             to Axes mapping.
           * Configure `constrained_layout`:
               * Convert grid_config.margins (figure fractions) to "inches" for figure.set_constrained_layout_pads(). For instance, w_pad_left =
                 grid_config.margins.left * figure.get_figwidth(). set_constrained_layout_pads requires w_pad, h_pad, w_space, h_space parameters, which are
                 global. The GridSpec's list-based hspace/wspace will guide internal spacing.
               * Set figure.set_layout_engine('constrained').
           * Retrieve Final Geometries: Iterate through the created Axes and get their final positions using ax.get_position(), converting Bbox to Rect.
           * Retrieve Effective Margins: Calculate effective_margin_top/bottom/left/right by finding the union bounding box of all Axes and comparing it to
             the figure's extent. Return as a Margins object.
           * Retrieve Effective Gutters: This is complex. constrained_layout does not directly expose per-row/per-column effective gutters.
               * Initial Approach: For hspace and wspace, return the target lists provided to GridSpec if they were provided and valid. If not, return
                 default (e.g., empty lists or averaged single values).
               * Refined Approach (Future): Implement logic to explicitly measure the distances between adjacent Axes in each row/column to calculate the
                 actual effective list of hspace and wspace. This would involve iterating gs.get_subplot_positions(figure) and analyzing the resulting Bbox
                 objects. For the initial implementation, relying on the target GridSpec values for Gutters will be sufficient, as constrained_layout
                 respects them.
           * Return Value: Return the mpl_axes_map, final_plot_geometries, calculated_margins, and calculated_gutters.

  Testing Plan:


   * Unit Tests (`tests/models/layout/test_layout_engine.py`):
       * test_apply_matplotlib_grid_layout_basic_grid: Test with a simple GridConfig (e.g., 2x2, default margins/gutters) to ensure correct Axes creation,
         and that returned Rects are sensible.
       * test_apply_matplotlib_grid_layout_with_ratios: Test with row_ratios and col_ratios to verify Axes dimensions reflect ratios.
       * test_apply_matplotlib_grid_layout_granular_margins: Test with custom Margins (e.g., large left margin) and verify calculated_margins reflect this,
         and Axes positions are adjusted.
       * test_apply_matplotlib_grid_layout_list_gutters: Test with GridConfig.gutters providing list values for hspace/wspace and verify GridSpec is created
         correctly and calculated_gutters reflect the target values. (If direct measurement is implemented, verify actual measured values).
       * test_apply_matplotlib_grid_layout_empty_plot_nodes: Verify handling of no PlotNodes.
       * test_apply_matplotlib_grid_layout_figure_clears_axes: Verify figure.clear() is called and new axes are added.
       * test_calculate_geometries_calls_apply_matplotlib_grid_layout: Verify the refactored calculate_geometries correctly delegates to
         apply_matplotlib_grid_layout on a temporary figure.

  Risks & Mitigations:


   * Risk: Accurate conversion of GridConfig's relative Margins and Gutters to constrained_layout's specific units (inches, fractions of font size).
   * Mitigation: Thorough testing with various GridConfig values and visual inspection of generated plots. Document any limitations or non-intuitive
     behaviors. Provide clear comments in code regarding unit conversions.
   * Risk: constrained_layout can sometimes fail or produce unexpected results with very complex GridSpec definitions or when many elements are present.
   * Mitigation: Implement robust error handling around figure.set_layout_engine(). Log warnings/errors gracefully. Consider providing a "reset layout" or
     "fallback to simple layout" option in the UI.
   * Risk: Calculating effective list-based hspace/wspace accurately after constrained_layout runs might be complex without direct Matplotlib API support.
   * Mitigation: Start with returning the target values if valid. If user feedback demands more precision, invest in measuring actual distances between Axes
     bounding boxes.

  ---


  Feature 3: UI for Granular Layout Controls

  Description: Adapt the Layout section of the Properties Panel to expose granular controls for top/bottom/left/right margins and list-based
  horizontal/vertical gutters, allowing users to fine-tune layout appearance.

  Planned Implementation:


   1. Modify `src/ui/factories/layout_ui_factory.py`:
       * Task: Update _build_grid_layout_controls(self, current_grid_config: GridConfig, layout_controller: LayoutController, parent: QWidget) -> QWidget
         (assuming this method builds the grid layout specific UI).
       * Task: Replace the single 'margin' input with four QDoubleSpinBoxes for margins.top, margins.bottom, margins.left, margins.right.
           * Reason: To enable granular control.
       * Task: Replace the single 'gutter' input with two QLineEdits for gutters.hspace and gutters.wspace.
           * Reason: To allow input of comma-separated lists for per-row/per-column spacing.
           * Input Handling: Connect editingFinished signal to controller methods, which will parse the comma-separated string into List[float].
       * Task: Connect the valueChanged (for QDoubleSpinBox) and editingFinished (for QLineEdit) signals of these new widgets to a unified debounced slot in
         layout_controller (e.g., layout_controller.on_grid_param_changed).
       * Task: Initialize each widget with values from current_grid_config.margins and current_grid_config.gutters.


   2. Modify `src/controllers/layout_controller.py`:
       * Task: Update on_grid_param_changed(self, param_name: str, value: Any):
           * When param_name is "margin_top", "margin_bottom", "margin_left", "margin_right", update the corresponding field in a temporary Margins object.
           * When param_name is "hspace" or "wspace":
               * Parse the value (string) into a List[float]. Implement robust error handling for invalid input (e.g., non-numeric values, incorrect
                 format).
               * Update the corresponding field in a temporary Gutters object.
           * After collecting all changes (perhaps after a debounce period), construct a new GridConfig and execute a ChangeGridParametersCommand (as
             outlined in the TDD's Feature 4).
       * Task: Ensure the ChangeGridParametersCommand accepts the new GridConfig structure.

  Testing Plan:


   * Unit Tests (`tests/ui/factories/test_layout_ui_factory.py`):
       * test_build_grid_layout_controls_has_granular_margin_inputs: Verify 4 QDoubleSpinBoxes for margins are present and correctly initialized.
       * test_build_grid_layout_controls_has_list_gutter_inputs: Verify 2 QLineEdits for hspace and wspace are present and correctly initialized.
       * test_grid_param_inputs_connect_to_controller: Verify all new input widgets connect their signals to layout_controller.on_grid_param_changed.
   * Unit Tests (`tests/controllers/test_layout_controller.py`):
       * test_on_grid_param_changed_updates_margins: Mock UI input for margins and verify ChangeGridParametersCommand is created with correct Margins.
       * test_on_grid_param_changed_parses_hspace_wspace_lists: Mock UI input for comma-separated hspace/wspace strings and verify
         ChangeGridParametersCommand is created with correct Gutters lists.
       * test_on_grid_param_changed_invalid_gutter_input_handled: Verify error handling for non-numeric or malformed list input.

  Risks & Mitigations:


   * Risk: Complex UI for list-based input might be cumbersome for users. Input validation and parsing of comma-separated strings can be error-prone.
   * Mitigation: Provide clear input instructions in the UI (e.g., tooltips, placeholder text). Implement robust parsing logic with clear user feedback for
     invalid input. Consider an alternative UI (e.g., a custom widget with dynamically added spinboxes) if the list input proves too difficult for users.
   * Risk: Increased number of UI controls could clutter the Properties Panel.
   * Mitigation: Group related controls visually (e.g., "Margins" group box, "Gutters" group box). Use sensible default values to minimize initial user
     configuration.

  ---

  Feature 4: Enhanced "Snap to Grid" with constrained_layout


  Description: The "Snap to Grid" functionality will be improved to use Matplotlib's constrained_layout during its inference process, intelligently
  determining optimal Margins and Gutters for the inferred grid.

  Planned Implementation:


   1. Modify `src/models/layout/layout_engine.py`:
       * Task: Update GridLayoutEngine.snap_plots_to_grid(self, plots: List[PlotNode], current_grid_config: GridConfig) -> GridConfig:
           * Initial Grid Inference: Keep existing logic for inferring rows and cols based on num_plots.
           * Initial Ratios: Keep logic for inferred_row_ratios and inferred_col_ratios.
           * Ephemeral Matplotlib Figure: Create a temporary matplotlib.pyplot.figure() for the dry run. Ensure it's closed in a try...finally block.
           * Temporary `GridConfig` for Dry Run: Create a temp_grid_config_for_dry_run using the inferred rows, cols, row_ratios, col_ratios. For margins
             and gutters in this temporary config, use the current_grid_config.margins and current_grid_config.gutters as initial suggestions for
             constrained_layout.
           * Call `apply_matplotlib_grid_layout`: Call self.apply_matplotlib_grid_layout(temp_fig, plots, temp_grid_config_for_dry_run).
           * Retrieve `calculated_margins` and `calculated_gutters`: Directly use the Margins and Gutters objects returned by apply_matplotlib_grid_layout.
           * Construct New `GridConfig`: Create and return a new_grid_config using the inferred rows, cols, row_ratios, col_ratios, and the
             calculated_margins/calculated_gutters. No more averaging or max() calls are needed for these specific attributes.
           * Reason: To intelligently leverage constrained_layout's optimization for spacing when snapping to a grid.

  Testing Plan:


   * Unit Tests (`tests/models/layout/test_layout_engine.py`):
       * test_snap_plots_to_grid_uses_ephemeral_figure: Verify a temporary Matplotlib figure is created and closed.
       * test_snap_plots_to_grid_calls_apply_matplotlib_grid_layout: Verify apply_matplotlib_grid_layout is called during the dry run.
       * test_snap_plots_to_grid_inferred_margins_match_constrained_layout_output: Test with various plot arrangements (e.g., plots with long titles/labels)
         and verify the margins in the returned GridConfig are consistent with what constrained_layout would produce.
       * test_snap_plots_to_grid_inferred_gutters_match_constrained_layout_output: Test with multiple plots and verify the gutters (lists) in the returned
         GridConfig are consistent with constrained_layout's spacing decisions.
       * test_snap_plots_to_grid_handles_empty_plots: Verify it returns the current config if no plots are present.
       * test_snap_plots_to_grid_error_handling: Verify graceful handling if apply_matplotlib_grid_layout encounters an error during the dry run.


  Risks & Mitigations:


   * Risk: constrained_layout's "intelligent" determination of margins/gutters might not always align with user expectations, especially when going from
     free-form to grid.
   * Mitigation: Document the behavior clearly. Provide UI controls (Feature 3) for manual adjustment after snapping. Allow the user to "undo" the snap
     operation.
   * Risk: Performance overhead of creating a temporary Matplotlib figure and running layout solver for each "snap" operation, especially with many plots.
   * Mitigation: Profile the snap_plots_to_grid method. If performance is an issue, consider debouncing snap requests or caching results for frequently
     snapped configurations.

# Session Summary - Backlog of Achievements

This document summarizes the key achievements and resolved issues during the current development session, presented as a backlog.

## Resolved Items

### Architecture & State Management

-   **Implemented `ui_selected_layout_mode`:** Introduced a new property (`_ui_selected_layout_mode`) and signal (`uiLayoutModeChanged`) in `LayoutManager` to explicitly separate the UI's selected layout mode from the application's active layout mode. This ensures UI changes do not prematurely alter the active application state.
    *   **Related TODOs Completed:** 1, 2, 3
-   **Refactored `LayoutManager.__init__`:** Modified initialization to correctly set `_ui_selected_layout_mode` and `_application_model.current_layout_config` based on `default_mode` without calling `set_layout_mode`. Explicitly creates a minimal `GridConfig` if the default is `GRID`.
    *   **Related TODOs Completed:** 5
-   **Re-purposed `LayoutManager.set_layout_mode`:** This method now solely controls the *active* layout (`_application_model.current_layout_config`), ensuring `_last_grid_config` is initialized (if `GRID` mode is activated) and storing previous configurations. It no longer affects the UI's selected mode directly.
    *   **Related TODOs Completed:** 4

### Feature Enhancements & Bug Fixes

-   **Optimized Layout Actions (`infer_grid_parameters`, `optimize_layout_action`, `update_grid_layout_parameters`):** These methods now explicitly call `LayoutManager.set_layout_mode(LayoutMode.GRID)` to ensure the active layout is `GRID` before proceeding with calculations. Redundant `None` checks for `_last_grid_config` were removed.
    *   **Related TODOs Completed:** 6, 7, 8
-   **Corrected `GridLayoutEngine` Initialization:** Fixed `TypeError` in `GridLayoutEngine.calculate_geometries` and its helper `_apply_constrained_layout` by ensuring `Margins` and `Gutters` are always instantiated with required arguments.
    *   **Related TODOs Completed:** (Partially 12, manual fix for `_apply_constrained_layout` was implied)
-   **Synchronized UI Panel Building:** Updated `LayoutUIFactory.build_layout_controls()` to use the new `ui_selected_layout_mode` for determining which UI panel to build, aligning with the separation of concerns.
    *   **Related TODOs Completed:** 10
-   **Adapted `LayoutController` for UI Selection:** Modified `LayoutController.set_layout_mode` to now set `LayoutManager.ui_selected_layout_mode` (UI-only state), disentangling it from active layout changes.
    *   **Related TODOs Completed:** 9

### UI Responsiveness & Data Flow

-   **Enhanced `PropertiesPanel` Updates:** Ensured the `PropertiesPanel` correctly responds to changes in the UI's selected layout mode and the active layout configuration parameters.
    *   Connected `PropertiesPanel._update_content` to `LayoutManager.uiLayoutModeChanged` to rebuild controls when the UI's mode selection changes.
    *   Connected `PropertiesPanel._update_content` to `ApplicationModel.layoutConfigChanged` to ensure UI fields update when active layout parameters (like optimized margins/gutters) change.
    *   **Related TODOs Completed:** (Partially 10, manual fix for `PropertiesPanel` connection)

### Test Updates

-   **Updated `ApplicationModel.current_layout_config` setter:** Reverted type hint to `LayoutConfig` and removed `None` handling as the model should always hold a valid config object.
    *   **Related TODOs Completed:** 11
-   **Refactored Tests for LayoutManager and LayoutUIFactory:** Updated relevant unit tests to validate the new `ui_selected_layout_mode` behavior and the revised signal emission patterns.
    *   **Related TODOs Completed:** 13, 14 (partial, due to ongoing debugging of `optimize_layout`)

## Outstanding Items / Next Steps (from current debugging context)

-   Investigate why `optimize_layout` view/values are not updating (despite connections).
    *   **Initial Diagnosis:** The `GridLayoutEngine._apply_constrained_layout` method still has a `Margins()` call without arguments. (This was manually fixed, but the logs still showed it, implying a synchronization issue.)
    *   **Current status:** Logs still indicate a `TypeError` in `_apply_constrained_layout`. Need to re-verify `GridLayoutEngine._apply_constrained_layout` and ensure `calculated_margins = Margins()` is replaced with `calculated_margins = Margins(0.0, 0.0, 0.0, 0.0)`.
    *   **Further investigation needed:** Correctly extract calculated gutters from `constrained_layout` to ensure `calculated_gutters` reflect true optimized values, not just input values.

This backlog reflects a shift towards a more robust and decoupled UI/logic architecture for layout management, with ongoing refinement of the optimization feedback loop.


* Add a to_str method to handle data validation from user or config file input instead of insisting on lower or upper case input, maybe write a general parser that can also analyze lists etc.

* Clean up imports, unnecessary comments, lint the document, and make it type safe, e.g. by adding more custom types (axis string in layout manager)
* Fix how properties_view doesn't treat layout_ui_factory and properties_ui_factory on equal ground.
* Try and see if we can increase code reusability in any way



   1. `PlotPropertiesUIFactory`:
       * test_build_column_selectors_signal_blocking_prevents_recursion
       * test_build_limit_selectors_passes_line_edit_references
       * test_build_dynamic_properties_handles_data_column_errors_gracefully


   2. `NodeController`:
       * test_on_limit_editing_finished_reads_current_line_edit_values
       * test_on_plot_type_changed_updates_plot_type_property


   3. `LayoutManager`:
       * test_infer_grid_parameters_updates_last_grid_config_only
       * test_infer_grid_parameters_emits_gridConfigParametersChanged
       * test_infer_grid_config_from_plots_gutter_calculation_accuracy


   4. `GridLayoutEngine`:
       * test_apply_fixed_layout_direct_gutter_usage
       * test_apply_fixed_layout_with_single_gutter_value
       * test_apply_fixed_layout_with_multiple_gutter_values
       * test_apply_fixed_layout_with_none_or_empty_gutters

  Integration Test Cases:


   1. UI Interaction:
       * test_plot_type_change_ui_integrity
       * test_infer_grid_no_plot_change_and_ui_update
       * test_infer_and_apply_grid_consistency
       * test_limit_editing_persists_across_selections
       * test_column_selector_stability_on_rebuild

  Unit Tests


   * `tests/unit/ui/panels/test_side_panel.py` (NEW): test_initialization_of_tabs_and_qtabwidget,
     test_tab_switching_by_name, test_on_selection_changed_switches_to_properties_tab_for_plotnode,
     test_on_selection_changed_does_not_switch_for_non_plotnode,
     test_on_selection_changed_does_not_switch_for_multiple_selection.
   * `tests/unit/ui/panels/test_properties_tab.py` (NEW): test_initialization_and_content_display,
     test_update_content_on_selection_change, test_subplot_combobox_interaction_calls_controller,
     test_select_file_button_calls_controller, test_apply_button_calls_controller,
     test_plot_type_combobox_interaction_calls_controller, test_plot_type_change_rebuilds_dynamic_ui,
     test_dynamic_properties_section_cleared_on_no_selection.
   * `tests/unit/ui/panels/test_layout_tab.py` (NEW): test_initialization_of_toggle_button_and_controls,
     test_toggle_button_interaction_calls_controller, test_update_content_on_ui_layout_mode_changed,
     test_toggle_button_text_updates_correctly.
   * `tests/unit/ui/panels/test_layers_tab.py` (NEW): test_initialization_and_content_display_with_hierarchy,
     test_visibility_toggle_calls_node_controller, test_lock_toggle_calls_node_controller,
     test_in_place_renaming_calls_node_controller, test_drag_and_drop_reordering_calls_node_controller,
     test_grouping_calls_node_controller, test_ungrouping_calls_node_controller,
     test_model_changed_rebuilds_tree_widget.
   * `tests/unit/ui/widgets/test_canvas_widget.py` (NEW): test_double_click_on_plotnode_updates_model_selection,
     test_double_click_on_empty_space_clears_model_selection, test_double_click_on_non_plotnode_does_not_select.
   * `tests/unit/controllers/test_node_controller.py` (EXISTING):
     test_on_subplot_selection_changed_updates_selection_model, test_on_select_file_clicked_opens_file_dialog,
     test_on_apply_data_clicked_success_executes_command, test_on_apply_data_clicked_failure_handles_error,
     test_set_node_visibility_executes_command, test_set_node_locked_executes_command,
     test_reorder_nodes_executes_command, test_group_nodes_executes_command, test_ungroup_node_executes_command,
     test_rename_node_executes_command, test_on_limit_editing_finished_reads_current_line_edit_values,
     test_on_plot_type_changed_updates_plot_type_property.
   * `tests/unit/models/test_plot_node.py` (EXISTING): test_plotnode_serialization_deserialization_with_data_file_path.
   * `tests/unit/models/test_scene_node.py` (EXISTING):
     test_scenenode_serialization_deserialization_with_visible_locked.
   * `tests/unit/ui/factories/test_plot_properties_ui_factory.py` (NEW):
     test_build_widgets_for_line_plot_creates_correct_ui, test_build_widgets_for_scatter_plot_creates_correct_ui,
     test_build_widgets_for_unsupported_plot_type_handles_gracefully,
     test_build_column_selectors_signal_blocking_prevents_recursion,
     test_build_limit_selectors_passes_line_edit_references,
     test_build_dynamic_properties_handles_data_column_errors_gracefully.
   * `tests/unit/services/commands/test_new_commands.py` (NEW): test_change_children_order_command_execute_undo,
     test_group_nodes_command_execute_undo, test_ungroup_nodes_command_execute_undo.
   * `tests/unit/services/test_layout_manager.py` (NEW): test_infer_grid_parameters_updates_last_grid_config_only,
     test_infer_grid_parameters_emits_gridConfigParametersChanged,
     test_infer_grid_config_from_plots_gutter_calculation_accuracy.
   * `tests/unit/models/layout/test_grid_layout_engine.py` (EXISTING): test_apply_fixed_layout_direct_gutter_usage,
     test_apply_fixed_layout_with_single_gutter_value, test_apply_fixed_layout_with_multiple_gutter_values,
  Integration Tests


   * `tests/integration/test_main_window_integration.py` (EXISTING):
     test_side_panel_dock_visibility_and_tab_interaction.
   * `tests/integration/test_properties_tab_interaction.py` (NEW): test_subplot_selection_and_property_update,
     test_data_loading_workflow, test_plot_type_change_and_dynamic_ui.
   * `tests/integration/test_layout_tab_interaction.py` (NEW): test_toggle_layout_mode_and_layout_control_interaction.
   * `tests/integration/test_layers_tab_interaction.py` (NEW):
     test_full_layers_tab_interaction_visibility_lock_reorder_group_ungroup_rename.
   * `tests/integration/test_canvas_double_click_interaction.py` (NEW):
     test_double_click_workflow_opens_side_panel_and_selects_plot, test_plot_type_change_ui_integrity,
     test_infer_grid_no_plot_change_and_ui_update, test_infer_and_apply_grid_consistency,
     test_limit_editing_persists_across_selections, test_column_selector_stability_on_rebuild.

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

# Technical Design Document 2 (Revised): Hierarchical Theming, Headless Architecture, and Dynamic UI

## Epic Overview
This epic transitions the application from a flat, coupled property model to a **Strict Hierarchical Tree**. It enforces a "No Defaults" policy where all visual attributes are injected via the `StyleService`. 
Crucially, this revision addresses the architectural violations currently breaking the system: it strictly enforces a **Headless Model** (stripping Matplotlib from the data layer) and implements a **Sanitized Interaction Layer** to decouple UI/Tools from backend rendering events.

### Completed Prerequisites (Do Not Re-implement)
*   **Hierarchical Dataclasses:** `plot_properties.py` atoms (`FontProperties`, `LineProperties`, etc.) are established.
*   **Style Injection:** `StyleService` is functional, validating against `REQUIRED_KEYS` and acting as the sole factory.
*   **Path-Based Commands:** `ChangePlotPropertyCommand` correctly handles recursive traversal, wildcards, and versioning.
*   **Event Infrastructure:** Generic path events (`CHANGE_PLOT_NODE_PROPERTY_REQUESTED`, `PLOT_NODE_PROPERTY_CHANGED`, `SUB_COMPONENT_SELECTED`) exist in `events.py`.

---

## Outstanding Implementation Plan

### Feature 1: Enforcing the Headless Model (`PlotNode`)
**Problem:** `PlotNode` is currently broken. It holds live Matplotlib `Axes` references, uses stale property classes (`AxesLimits`), and relies on backend rendering for hit-testing, violating the MVP Passive View mandate.

**Implementation Steps:**
1.  **Modify `src/models/nodes/plot_node.py`:**
    *   **Purge Backend:** Remove `import matplotlib` and delete the `self.axes` attribute.
    *   **Restore Serialization:** Rewrite `from_dict` and `to_dict` to exclusively use the new recursive `PlotProperties.from_dict()` and `to_dict()` methods. Remove manual reconstruction of legacy classes.
    *   **Headless Hit-Testing:** Refactor `hit_test(pos)`. It must no longer use `self.axes.get_window_extent()`. Instead, perform a purely mathematical bounds check against `self.geometry` (which is stored in normalized 0-1 figure coordinates).
2.  **Modify `src/models/plots/plot_properties.py` (Cleanup):**
    *   Uncomment and properly type the commented-out fields in `TextProperties` (e.g., `rotation`, `va`, `ha`) and `AxisProperties` to ensure full visual control is restored.

### Feature 2: Renderer as the "Artist Registry"
**Problem:** Because the Model is now headless, it can no longer manage the lifecycle of Matplotlib objects. The `Renderer` must take ownership.

**Implementation Steps:**
1.  **Modify `src/ui/renderers/renderer.py`:**
    *   **Registry Implementation:** Add `self._axes_registry: dict[str, matplotlib.axes.Axes]` to map `node.id` to the live axes.
    *   **Lifecycle Management:** In `_render_plots`, query the registry by `node.id`. If missing, create the axes via the `CoordSyncStrategy` and store it.
    *   **Garbage Collection:** Subscribe the `Renderer` to `Events.NODE_REMOVED_FROM_SCENE`. When a node is deleted, the Renderer must remove the `Axes` from the Matplotlib `Figure` and delete it from the `_axes_registry` to prevent memory leaks and "zombie" plots.
    *   **Strategy Cleanup:** Move hardcoded property hacks (like `set_limits` overrides) into the respective `CoordSyncStrategy` to ensure `_sync_component` remains a generic recursive loop.

### Feature 3: Sanitized Interaction Layer
**Problem:** `CanvasController` passes Matplotlib `MouseEvent` and `PickEvent` objects directly to the `ToolService`, coupling the entire interactive layer to the Matplotlib backend.

**Implementation Steps:**
1.  **Modify `src/ui/widgets/canvas_widget.py`:**
    *   Remove business logic from `mouseDoubleClickEvent` and `wheelEvent`. The widget should strictly handle Illustrator-style Qt viewport navigation (panning/zooming the artboard, not the data).
    *   Implement a `map_to_figure(qt_pos) -> tuple[float, float]` helper to safely translate screen pixels into 0-1 figure coordinates.
2.  **Modify `src/controllers/canvas_controller.py`:**
    *   **The Translator:** Intercept `button_press_event` from Matplotlib. Use `canvas_widget.map_to_figure()` to get coordinates, query the headless model (`get_node_at`), and pass backend-neutral data `(node_id, fig_coords, button)` to the `ToolService`.
    *   **Pick Sanitization:** Intercept Matplotlib's `pick_event`. Extract `node_id` and the `gid` (the property path) from the artist. Publish `Events.SUB_COMPONENT_SELECTED(node_id, path)`.
    *   **Logic Extraction:** Move the data mapping logic out of `on_data_ready`. It should trigger an `ApplyDataCommand` that utilizes the `StyleService` to generate valid properties.
3.  **Modify `src/services/tools/selection_tool.py`:**
    *   Update method signatures to accept primitive coordinates and `node_id` instead of Matplotlib events.
    *   Handle `path` selection updates seamlessly, completely detached from the GUI.

### Feature 4: Path-Aware Recursive UI Factory
**Problem:** The `PlotPropertiesUIFactory` is completely stale, trying to build massive, static forms for deprecated property models.

**Implementation Steps:**
1.  **Modify `src/ui/factories/plot_properties_ui_factory.py`:**
    *   **Breadcrumb Navigation:** Implement a header widget reflecting the `selected_path` (e.g., `Plot 1 > X-Axis > Label`). Clicking a parent segment must publish a `SUB_COMPONENT_SELECTED` event for that parent path.
    *   **Atom Builders:** Create modular generator functions:
        *   `build_text_ui(path)`: Yields QLineEdit (text), QComboBox (font), QPushButton (color picker).
        *   `build_line_ui(path)`: Yields QSlider (width), QComboBox (style), QPushButton (color).
    *   **Recursive Dispatch:** Rewrite `build_widgets(node, path)`. It must traverse `node.plot_properties` using the `path`. Using `is_dataclass` and `type()`, it dispatches layout generation to the specific Atom Builder matching that type.
    *   **Generic Data Binding:** Every generated widget is instantiated with its absolute `path`. On `editingFinished` or `clicked`, it publishes `CHANGE_PLOT_NODE_PROPERTY_REQUESTED(node.id, path, new_value)`.

### Feature 5: Controller & Event Pruning (Legacy Cleanup)
**Problem:** The codebase is littered with handlers for granular events that bypass the new architectural systems.

**Implementation Steps:**
1.  **Modify `src/controllers/node_controller.py`:**
    *   Delete all legacy property handlers (`_handle_generic_property_change_request`, `_handle_limit_editing_request`, etc.).
    *   This controller should now only handle structural scene requests (Rename, Visibility, Lock, Data Loading).
2.  **Modify `src/core/composition_root.py`:**
    *   Delete subscriptions to `PLOT_TITLE_CHANGED`, `PLOT_XLABEL_CHANGED`, etc.
    *   Ensure `SCENE_GRAPH_CHANGED`, `PLOT_NODE_PROPERTY_CHANGED`, and `NODE_LAYOUT_RECONCILED` are the primary triggers for `_redraw_canvas_callback`. (The `Renderer`'s version gating will ensure this is performant).
3.  **Modify `src/shared/events.py`:**
    *   Delete the legacy property Enums (e.g., `PLOT_TITLE_CHANGED`) to finalize the deprecation and prevent future regressions.

---

### Data & Event Flow Example (Click to Edit)

1.  **User Clicks X-Axis Label:**
    *   Matplotlib detects hit on artist with `gid="coords.xaxis.label"`.
    *   `CanvasController` catches `pick_event`, extracts `gid`.
    *   `CanvasController` publishes `SUB_COMPONENT_SELECTED(node_id, "coords.xaxis.label")`.
2.  **State Update & UI Build:**
    *   `ApplicationModel` sets `selected_path = "coords.xaxis.label"`.
    *   `PlotPropertiesUIFactory` reads path, identifies `TextProperties` dataclass.
    *   Factory clears UI panel, renders `Text Atom Builder` (Text, Font, Color inputs).
3.  **User Edits Text:**
    *   User types "Time (s)" into QLineEdit.
    *   QLineEdit publishes `CHANGE_PLOT_NODE_PROPERTY_REQUESTED(node_id, "coords.xaxis.label.text", "Time (s)")`.
    *   `ChangePlotPropertyCommand` executes, updates nested dataclass, increments `_version`.
    *   `Renderer` detects version bump, syncs the new text to the specific Matplotlib title object.


# Technical Design Document 3: Decoupled Property System and State Reconciliation

## Epic Overview
This epic decouples **Structural Logic** (path resolution) from **User Intent** (Commands) by introducing a standalone `PropertyService`. This architecture enables the **Bypass Pattern**, allowing the system to reconcile its internal state (e.g., syncing back Matplotlib's autoscale results) without polluting the undo stack or triggering recursive redraw loops.

---

### Feature 1: Standalone `PropertyService`
**Description:** Extract all path-based navigation and property-setting logic from `ChangePlotPropertyCommand` into a stateless, domain-level service.

**Planned Implementation:**

1.  **Create `src/services/property_service.py`:**
    *   **Task:** Implement `get_value(obj, path: str) -> Any`: A robust, recursive navigator for nested dataclasses, dictionaries, and lists.
    *   **Task:** Implement `set_value(obj, path: str, value: Any)`: A safe leaf-setter that handles type-coercion (e.g., converting strings to Enums or floats where appropriate).
    *   **Task:** Implement `resolve_concrete_paths(obj, path: str) -> list[str]`: A wildcard expansion engine (e.g., resolving `artists.*.visible` into specific indexed paths).
2.  **Refactor `ChangePlotPropertyCommand` (`src/services/commands/change_plot_property_command.py`):**
    *   **Task:** Purge internal path-navigation methods (`_get_value_by_path`, `_set_value_by_path`, `_recursive_resolve`).
    *   **Task:** Update constructor to accept `PropertyService`.
    *   **Task:** Delegate all model interrogation and modification to `PropertyService`.
3.  **Modify `CompositionRoot` (`src/core/composition_root.py`):**
    *   **Task:** Instantiate `PropertyService` as a singleton-like service.
    *   **Task:** Inject `PropertyService` into `NodeController` and `CommandManager` (or directly into commands via factories).

---

### Feature 2: The "Bypass Pattern" for Model Updates
**Description:** Implement a non-undoable update path for background reconciliation tasks that ensures the model reflects reality without being treated as a "User Transaction."

**Planned Implementation:**

1.  **Modify `src/shared/events.py`:**
    *   **Task:** Add `Events.PLOT_NODE_PROPERTY_RECONCILED` (Payload: `node_id: str, path: str, value: Any`). This event signals a "Fact" (state sync) rather than an "Action" (user change).
2.  **Update `NodeController` (`src/controllers/node_controller.py`):**
    *   **Task:** Implement `reconcile_node_property(node_id: str, path: str, value: Any)`:
        *   Retrieves the node.
        *   Uses `PropertyService` to update the model value directly (Bypassing the `CommandManager`).
        *   Increments the node's `plot_properties._version` to maintain sync integrity.
        *   Publishes `Events.PLOT_NODE_PROPERTY_RECONCILED`.
3.  **Update `Renderer` (`src/ui/renderers/renderer.py`):**
    *   **Task:** Refactor `sync_back_limits(node_id: str)` to use `NodeController.reconcile_node_property()` instead of publishing a `CHANGE_REQUESTED` event. This effectively "closes the loop" silently.

---

### Feature 3: Redraw Loop Suppression (Event Scoping)
**Description:** Prevent feedback loops by distinguishing between redraw-triggering events and UI-sync-only events.

**Planned Implementation:**

1.  **Modify `CompositionRoot` (`src/core/composition_root.py`):**
    *   **Task:** Ensure `_redraw_canvas_callback` is **NOT** subscribed to `Events.PLOT_NODE_PROPERTY_RECONCILED`. This is the primary mechanism for breaking the infinite redraw loop.
2.  **Modify `SidePanel` / `PropertiesTab` (`src/ui/panels/properties_tab.py`):**
    *   **Task:** Update the UI to subscribe to **BOTH** `PLOT_NODE_PROPERTY_CHANGED` (User) and `PLOT_NODE_PROPERTY_RECONCILED` (System). This ensures the Property Panel always reflects the "real" Matplotlib limits even if they weren't set by the user.

---

### Testing Plan
*   **Unit Tests (`tests/unit/services/test_property_service.py`):**
    *   Verify deep navigation of nested `PlotProperties`.
    *   Verify wildcard expansion for multiple artists.
    *   Verify type conversion for leaf attributes.
*   **Integration Tests (`tests/integration/test_reconciliation_cycle.py`):**
    *   Load a template, drop data.
    *   Verify that `Renderer.sync_back_limits` is called.
    *   Verify that `ApplicationModel` is updated.
    *   **Assert:** The `CommandManager` undo stack remains empty.
    *   **Assert:** The `_redraw_canvas_callback` is only called once per data drop, not recursively.

---

### Risks & Mitigations
*   **Risk: Ghost Redraws**: If any component accidentally publishes `PLOT_NODE_PROPERTY_CHANGED` during a reconciliation cycle, the loop will return.
    *   **Mitigation**: Enforce strict event naming. Use logging in `EventAggregator` to audit which specific events are triggering `_redraw_canvas_callback`.
*   **Risk: Architectural Drift**: Direct model updates might be misused for user actions.
    *   **Mitigation**: Standardize the reconciliation path through a single method in `NodeController` that is explicitly named `reconcile_...` to distinguish it from standard commands.
*   **Risk: Dirty State Desync**: The user might think the project is "clean" even after an autoscale update.
    *   **Mitigation**: Decisions on whether reconciliation makes a project "dirty" should be centralized. For now, reconciliation is treated as a visual sync that does not require a save.

---

### Architectural Update Plan

1.  **`GEMINI.md` Update:**
    *   **Refinement:** Update the "Command Pattern Mandate." Distinguish between **Transactions** (User-initiated, undoable, triggers redraw) and **Reconciliation** (System-initiated, non-undoable, bypasses redraw).
2.  **`Architecture Design Document` Update:**
    *   **New Component:** Formally introduce the `PropertyService` as the owner of structural navigation.
    *   **Pattern Addition:** Document the "Bypass Pattern" as the standard for engine-to-model synchronization.



Scan for new values that should really be config values
Fix and refactor the layout engine to use numpy for calculations, and check whether the calculations are actually correct and have dedicated methods
Config_service is passed around a lot. I should rather inject the important sections during initialization
Make the event aggregator a singleton because I need it literally everywhere, so I can just assume its dependence, and I'm not hiding anything with that

# Technical Design Document 3: Themed Layout Orchestration

## Epic: Themed Figure and Grid Layout

This epic focuses on centralizing the source of truth for figure-level layout defaults (margins, gutters, and padding) within the `StyleService`. By treating layout configuration as a themeable property, we ensure consistency across different journal styles and remove service-level coupling between the layout and style systems.

---

### Feature 1: StyleService Expansion for Figure Layout
**Description:** Extend the `StyleService` to act as the "Mandatory Factory" for layout-related dataclasses. This removes redundant configuration in `ConfigService` and ensures that switching themes (e.g., from Nature to Science) automatically updates figure margins and plot spacing.

**Planned Implementation:**

1.  **Modify `StyleService` (`src/services/style_service.py`):**
    *   **Task:** Add figure layout keys to `REQUIRED_KEYS`:
        *   `figure.subplot.left`, `figure.subplot.right`, `figure.subplot.bottom`, `figure.subplot.top` (Absolute Margins).
        *   `figure.subplot.wspace`, `figure.subplot.hspace` (Absolute Gutters).
        *   `figure.constrained_layout.h_pad`, `figure.constrained_layout.w_pad`, `figure.constrained_layout.hspace`, `figure.constrained_layout.wspace` (Constrained Pads).
    *   **Task:** Implement `create_themed_grid_config(rows, cols) -> GridConfig`:
        *   Resolves the above keys from `_current_style`.
        *   Returns a fully populated `GridConfig` with nested `Margins` and `Gutters` objects.
    *   **Task:** Subscribe to `Events.INITIALIZE_LAYOUT_THEME_REQUESTED`.
    *   **Task:** Implement `_on_initialize_layout_theme_requested`:
        *   Generates the themed `GridConfig` and publishes `Events.NODE_LAYOUT_RECONCILED`.

2.  **Enrich `GridConfig` Dataclass (`src/models/layout/layout_config.py`):**
    *   **Task:** Add fields for constrained layout parameters: `h_pad: float`, `w_pad: float`, `constrained_hspace: float`, `constrained_wspace: float`.
    *   **Task:** Update `to_dict` and `from_dict` to include these new fields.

**Testing Plan:**
*   **Unit Tests (`tests/unit/services/test_style_service.py`):** Verify `create_themed_grid_config` correctly maps `.mplstyle` keys to the `GridConfig` hierarchy.
*   **Integration Tests:** Load a custom style and verify that the layout-related events carry the correct themed values.

---

### Feature 2: Stateless Grid Engine with Absolute-to-Relative Conversion
**Description:** Refactor the `GridLayoutEngine` to be strictly stateless and mathematically correct. The engine will no longer pull from services; it will rely entirely on the provided `GridConfig` and perform internal conversion of absolute figure fractions to Matplotlib-relative values.

**Planned Implementation:**

1.  **Modify `GridLayoutEngine` (`src/models/layout/grid_layout_engine.py`):**
    *   **Task:** Remove `config_service` from `__init__`.
    *   **Task:** Implement absolute-to-relative conversion logic in `_apply_fixed_layout`:
        *   `avg_subplot_w = (plot_area_width - (cols-1)*abs_gutter_w) / cols`.
        *   `gs_wspace = abs_gutter_w / avg_subplot_w`.
    *   **Task:** Update `_apply_constrained_layout` to use pads provided in the `GridConfig` instead of pulling from `ConfigService`.
    *   **Task:** Fix the "Zero Plot" bug: Return `grid_config.margins` and `grid_config.gutters` when the plot list is empty.

2.  **Update `LayoutManager` (`src/services/layout_manager.py`):**
    *   **Task:** Refactor `_create_minimal_grid_config` to publish `INITIALIZE_LAYOUT_THEME_REQUESTED` instead of manually constructing a config from `ConfigService`.

**Testing Plan:**
*   **Unit Tests (`tests/unit/models/layout/test_grid_layout_engine.py`):** 
    *   Verify that absolute gutters in `GridConfig` result in correct `0.375` (not `0.390`) plot widths in a 2x2 grid.
    *   Verify that empty plot lists preserve the input margins.
*   **Regression Tests:** Run existing `FreeLayoutEngine` tests to ensure no impact on other layout modes.

---

### Feature 3: Event-Driven Layout Initialization
**Description:** Standardize how layouts are initialized and reset using the event system, matching the pattern used for `PlotProperties`.

**Planned Implementation:**

1.  **Modify `src/shared/events.py`:**
    *   **Task:** Register `INITIALIZE_LAYOUT_THEME_REQUESTED`.

2.  **Update `ProjectController` / `LayoutController`:**
    *   **Task:** Use the initialization event when creating a new project or switching to grid mode for the first time.

**Risks & Mitigations:**
*   **Risk:** `GridSpec` behavior when `avg_subplot_width` is near zero.
*   **Mitigation:** Add guard clauses in the conversion logic to return `0.0` or a safe minimum if denominators are too small.
*   **Risk:** Backward compatibility with old project files.
*   **Mitigation:** `GridConfig.from_dict` will provide defaults for the new constrained padding fields if they are missing from older serialized dictionaries.


# Technical Design Document 5: Absolute Physical Coordinate System as Source of Truth

## 1. Introduction & Objectives

### 1.1. The Problem
Currently, SciFig uses **Normalized Figure Coordinates (0.0–1.0)** as the absolute source of truth for plot geometries and layout constraints. This creates a "Leaky Abstraction":
1.  **Non-Deterministic Sizing**: Resizing the figure window silently changes the physical size of all plots.
2.  **Logic Duplication**: The conversion math (`pixels / width` or `cm / fig_width`) is scattered across `CanvasController`, `LayoutManager`, and `OverlayRenderer`.
3.  **Rounding Drift**: Repetitive back-and-forth conversions between spaces during UI interactions lead to floating-point errors where plots "shift" by sub-pixels.

### 1.2. The Objective
To introduce a centralized **`CoordinateService`** and a **`CoordinateSpace`** enum to manage all transformations. We will move the **Absolute Source of Truth** to **Centimeters (cm)** within the Headless Model.

---

## 2. Architectural Components

### 2.1. The `CoordinateSpace` Enum
A new enum in `src/shared/types.py` to explicitly tag the **Reference Basis** of a value:
*   `PHYSICAL`: Absolute distance in Centimeters (The Model's Canonical Truth).
*   `FRACTIONAL_FIG`: 0.0 to 1.0 relative to the total Figure size.
*   `FRACTIONAL_LOCAL`: 0.0 to 1.0 relative to the **immediate parent** (e.g., subplot spacing).
*   `DISPLAY_PX`: Device pixels relative to the Canvas viewport.

### 2.2. The `CoordinateService`
A central, stateless service that provides a unified API for transformations and unit mapping.
**Core Responsibilities**:
*   **Space Translation**: Converts values between `PHYSICAL`, `FRACTIONAL_FIG`, `FRACTIONAL_LOCAL`, and `DISPLAY_PX`.
*   **Canonical Mapping**: Acts as the system "Gateway". Converts inbound user units (inches, mm) to the internal `PHYSICAL` (CM) standard.
*   **Display Formatting**: Converts internal CM to requested display units (e.g., for UI Spinboxes) with scientific rounding to prevent floating-point artifacts.

---

## 3. Data Structures & Model Updates

### 3.1. `ApplicationModel`
*   **New Property**: `figure_size: tuple[float, float]` (Width in cm, Height in cm).
*   **Initialization**: Sourced from `ConfigService` (converting default inches to cm).
*   **Event**: `Events.FIGURE_SIZE_CHANGED` published when changed.

### 3.2. `Rect` (Physical cm)
*   The `Rect` class in `src/shared/geometry.py` now strictly represents **Centimeters**. 
*   **Validation**: Methods like `scaled_by` will use a minimum threshold of `0.1 cm`.

---

## 4. Component Responsibilities

### 4.1. `CanvasController` (Input)
*   **Current**: Converts pixels to 0-1 using Matplotlib's `transFigure`.
*   **New**: Uses `CoordinateService` to convert that 0-1 value immediately into **Centimeters** using the `ApplicationModel.figure_size`.
*   **Impact**: Tools (`SelectionTool`, `AddPlotTool`) now receive and emit deltas in `cm`.

### 4.2. `LayoutManager` (Translation)
*   **Responsibility**: The sole provider of fractional geometries to the Renderer.
*   **Logic**: It queries the Layout Engines (which work in `cm`), then uses `CoordinateService` to scale them by the `figure_size` before publishing them to the `FigureRenderer`.

### 4.3. `GridLayoutEngine` (GridSpec Bridge)
*   **Margins**: Handled as absolute subtractions from the physical `figure_size`.
*   **Gutters**: Converts physical `cm` gaps into the relative `hspace/wspace` fractions expected by Matplotlib.
    *   `hspace = gutter_cm / average_subplot_height_cm`.

### 4.4. `OverlayRenderer` (View Feedback)
*   **Logic**: Uses `CoordinateService` to map the physical `Rect` from the model directly to `DISPLAY` pixels for drawing handles and ghosts.

---

## 5. Implementation & Migration Steps

### Phase 1: Foundation (Enums & Service)
1.  Define `CoordinateSpace` Enum.
2.  Implement `CoordinateService` in `src/services/coordinate_service.py`.
3.  **Test**: Add unit tests verifying `CM <-> Fractional <-> Pixel` math with various DPIs and figure sizes.

### Phase 2: Model & Event Update
1.  Add `figure_size` to `ApplicationModel`.
2.  Update `Rect` docstrings and verify `src/shared/geometry.py` logic works with absolute floats.
3.  Add `Events.FIGURE_SIZE_CHANGED`.
4.  **Test**: Verify Model state and event publication.

### Phase 3: The Interaction Bridge
1.  Refactor `CanvasController` to use `CoordinateService`.
2.  Update `SelectionTool` logic to handle `cm` deltas.
3.  **Test**: Verify a "1cm drag" on screen results in a `+1.0` change in the `Rect` model regardless of figure size.

### Phase 4: The Layout Bridge
1.  Refactor `LayoutManager.get_current_layout_geometries` to use `CoordinateService` for physical->fractional mapping.
2.  Refactor `GridLayoutEngine` to handle physical margins and relative `GridSpec` gaps.
3.  **Test**: Verify that a 10cm wide plot on a 20cm figure renders at `0.5` position.

### Phase 5: View & Persistence
1.  Update `OverlayRenderer` to use the service for ghost drawing.
2.  Do NOT implement a versioning step. Backwards compatibility does not need to be maintained


---

## 6. Edge Cases & Constraints

*   **Zero or Negative Sizes**: When subtracting cm margins from the figure size, the available plot area could become `<= 0`. The engines must fallback to a minimum plot size (e.g., 0.2 cm).
*   **Precision**: Using CM as truth eliminates rounding drift during UI interactions.
*   **File I/O (Legacy)**: Existing saved projects assumption: normalized `0.5` becomes `0.5 cm`. There is no need to keep backwards compatibility to the legacy notation.

---

## 7. Affected Files Audit

To ensure a comprehensive migration, the following files must be reviewed and updated according to their coordinate space role:

### 7.1. Group A: Design Space (Primary Truth)
*These files currently store "Truth" as normalized values; they must shift to Physical Inches.*
*   `src/models/nodes/plot_node.py`: `self.geometry` storage and initialization.
*   `src/models/layout/layout_config.py`: `Margins` and `Gutters` data structures.
*   `src/shared/geometry.py`: `Rect` logic (docstrings and methods like `moved_by`).
*   `src/services/commands/add_plot_command.py`: Geometry passing for new nodes.
*   `src/services/commands/batch_change_plot_geometry_command.py`: Geometry updates.
*   `src/services/commands/change_grid_parameters_command.py`: `GridConfig` updates.

### 7.2. Group B: Fractional Space (The Translators)
*These files perform the math to convert Physical Model values into Matplotlib-ready fractions.*
*   `src/services/layout_manager.py`: Core translation logic in `get_current_layout_geometries` and grid heuristics.
*   `src/models/layout/free_layout_engine.py`: Math for `perform_align` and `perform_distribute`.
*   `src/models/layout/grid_layout_engine.py`: Conversion of physical margins/gutters to `GridSpec` relative values.
*   `src/ui/renderers/figure_renderer.py`: Version gating and comparison of MPL vs Model limits.

### 7.3. Group C: Viewport Space (Display & Interaction)
*These files bridge the screen pixels to the model.*
*   `src/ui/widgets/canvas_widget.py`: Pixel-to-Normalized mappings.
*   `src/controllers/canvas_controller.py`: Input capture scaling (Pixels -> Normalized -> Physical).
*   `src/ui/renderers/overlay_renderer.py`: Handle/Ghost drawing logic.
*   `src/services/tools/selection_tool.py`: Hit-test thresholds (currently hardcoded px).
*   `src/services/tools/add_plot_tool.py`: Click-vs-Drag thresholds.

### 7.4. Configuration & Utilities
*The source of constants.*
*   `configs/default_config.yaml`: `default_dpi`.
*   `configs/default.mplstyle`: `figure.figsize` and `figure.dpi`.
*   `src/services/config_service.py`: Provider of these constants.


Remaining Features
- Delete plot in free form with select/right_click/delete
- Make the add plot dialog similar to the shape dialog of adobe illustrator
## New Grid Layout Manager
- Note: Before implementing this, we might have to refactor the layout controller, layout manager, free layout engine, grid layout engine and grid config to make space for these capabilities
- Ability to display grid layout lines with hspace, wspace, and gutters as grid lines and on top of the existing matplotlib figure
    - To support this feature and not collide with the rest of the application, these lines shouldn't always be visible, but only, when we are in grid layout mode, and not in free form layout mode
    - Support for a nested subplot layout with many subplotgridspec objects inside, so not just a flat top-level representation
    - For grid lines that are only valid for a specific subplotgridspec, the lines should only be visible within that subplotgridspec
    - I will use the overlay renderer for displaying these lines and make them movable
    - The hspaces and wspaces should be slightly greyed out to clearly indicate that no plot can be put here
        - Unlike "native" matplotlib, where we only display the entire hspaces and wspaces, I want to have the "main" divider lines at hspace/2 and wspace/2, and then around them finer lines that indicate the hspace and wspace borders
- I need to think about a suitable internal representation and data structure for this with the recursive splitting into subplots
    - The internal data and the renderer need to be synced at all times
    - The representation needs to be serializable for saving and loading
    - Is there any inspiration that I can take from how I represent PlotProperties?
    - Maybe I can have an internal representation with a Figure, gutters, and a gridspec
    - The gridspec then fills up recursively with subplotgridspecs, and for each level, we can also hold information for hspace and wspace
    - The data structure potentially needs to support arbitrary level of nesting, but we should for safety put a limit at a depth of 10 layers
    - Eventually, there needs to be an option to "flatten" the highly nested subplot grid where appropriate, if the real subplot gridspec can actually be represented in a simpler way by a flatter subplotgridspec
- In essence, this looks to me like how you would have to represent a table in word or so internally and visually, which can also be nested and where cells can be merged and subdivided again
    - The hspace and wspace are similar to the cells whitespace boarders, only that in matplotlib, the represent the space between subplots in fractional coordinates relative to the subplot size, wheras for a table, we would have hspace or wspace/2 as the "padding" within each cell
- Supported actions
    - In the empty subplot spaces, clicking while the plot tool is selected will add a subplot. Unlike with the free layout, where a dialog opens up asking for the dimensions, the dimensions will automatically be calculated based on the gridspec
    - Likewise, there should the ability to subdivide the space again (with subplotspecgrid). Maybe for now this action can be handled by the selection tool when clicking on any cell
        - Upon clicking, the cell, a dialog should open to ask for how many rows and columns we want, and what their height and width ratios should be
        - If the cell is empty, the action is easy. If the cell contains a subplot, the existing subplot should automatically be moved into the upper left quadrant of the new grid
    - There should be delete and move actions for deleting subplots from the grid, moving hspace and gutters
    - There should be the option to move subplots from one "grid cell" to another
    - There should be the option to resize subplots, and the resized plot should intelligently snap to the existing grid (we'll have to think of an intelligent algorithm here)
    - there needs to be some sort of smart grid allocation because moving subplots will have to find the nearest subplot to land in
    - When hovering at the sides over one of the divider grid lines, a plus symbol should pop up and the divider line should be highlighted by a thicker linewidth, to add a new row or column at this point. I should check in word about the possible redistribution options like intelligent redistribute etc.
        - One option would be to take the middle value of the relative subplot fractions of the two adjacent lines. By using the relative fractions, we make sure that when the new row/column is added, and the adjacent ones are shrunk down, that the newly added column isn't actually bigger than the adjacent ones (e.g. if we have a 10cm figure with two columns, 5 cm each: In absolute terms, the new column would have to be also 5 cm but because the total width of the figure is 10 cm, the existing columns would now have to be 2.5 cm. By using relative fractions (1:1 -> 1:1:1, everything gets scaled correctly))
- There should be the option in the layout ribbon bar to create a new grid, where a dropdown pops up with with a 7 cols x 6 rows square plot preview where the user can over over to select the table to create the size that they want
    - For now, the easier option will be to just have a dialog where the user is being asked for the number of rows and number of columns to quickly create a grid layout
    - Implement the table layout ribbon bar from word where there is the option to
        - toggle visibility of the grid lines
        - Ability to delete
            - Dub items to delete an individual cell (think about how to fill the gap)
            - Delete row/column, which will do the opposite of adding
        - Ability to add
            - Row above
            - Row below
            - Column left
            - Column right
        - Merge / split
            - Split is what I discussed before
            - Merge will require selection of multiple cells in the grid (I need to support that option)
        - Cell dimensions
            - See above. I will have to think about whether this is the plotnode.geometry rect or if this is the subplotgrid size or whether the two are the same
            - Auto redistribute height and width of columns to the same value
                - This should be applied to the topmost gridspec, not to the nested gridspecs
            - Cell borders
                - This will be the hspace/2 and wspace/2
                - We will need support for setting these in cm despite matplotlib keeping track of them in fractions relative to the subplot size
                - For a balanced look, I will probably want this value to be set globally (for the most part), but as an absolute value. This will require some sort of conversion on my side because matplotlib sets it to the fictional "size 1" subplot within the respective gridspec, so if we added a nested gridspec, where the absolute size of "size 1" is different, the hspace (say size 0.2) will be different in absolute coordinates. This is not desired. Instead, they should match in terms x cm across all nestings
- The grid layout manager will have to communicate with the style service because it holds the information on default margins and spaces
- I assume the rectangle dimensions will come from plotnode.geometry (not sure, because we need to have space for the labels. I should check how matplotlib handles this internally)
- Eventually, there should be the option, like in word, to have predefined layout margins like narrow, wide etc.

- Check for mpl examples for displaying grid lines

# Integration Tests
- Open project, load in 2x2 template, drag and drop data into all four plots

# Errors/Bugs
- Empty dropdown in the properties tab
- Do a TODO: search in the code base to find open tickets
- Back syncing very inefficient, constant rerenders
- Double and triple logging, e.g. during hydration of plots
    - Also when 

# Code Smells
- The "Data-Mapping Leak": The NodeController currently knows too much about how data is mapped to specific plot types (e.g., it knows that a line plot needs an "x_column" and a "y_column"). This should ideally be handled by a specialized MappingService or the PlotNode itself.
- The "CompositionRoot Orchestrator": The CompositionRoot is doing more than just wiring; it's handling the "Limit Syncing" logic (taking Matplotlib's autoscale results and pushing them back to the Model). This is a cross-cutting concern that makes it hard to test the Model in isolation from the "Redraw Loop."
- Murky Spot: The LayoutManager is currently the "Muckiest" spot. It directly reaches into the ApplicationModel and rearranges nodes (like creating GridNode containers). This is a strong coupling. Our integration tests here will be vital when we eventually refactor this to be more decoupled.