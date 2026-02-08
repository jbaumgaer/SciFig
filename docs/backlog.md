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


* Add a to_str method to handle data validation from user or config file input instead of insisting on lower or upper case input, maybe write a general parser that can also analyze lists etc.

* Clean up imports, unnecessary comments, lint the document, and make it type safe, e.g. by adding more custom types (axis string in layout manager)
* Fix how properties_view doesn't treat layout_ui_factory and properties_ui_factory on equal ground.
* Try and see if we can increase code reusability in any way

Make sure that when a plot is unclicked, that we switch back to the layout managment properties panel
Make sure that grid options actually update properly
