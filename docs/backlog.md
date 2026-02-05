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