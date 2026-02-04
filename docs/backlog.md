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
    *   In `PropertiesView`, update its `__init__` to accept `list[PlotType]` and modify the `QComboBox` to be populated from this list. The `_on_plot_type_changed` signal will now emit a `PlotType` member.

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

1.  **Introduce a Comprehensive Testing Framework (Highest Priority)**
    *   **Goal:** Ensure code correctness and prevent regressions.
    *   **Implementation:** Integrate `pytest` and `pytest-qt`, create a `tests/` directory, and begin writing unit tests for models/commands and integration tests for UI workflows.

2.  **Implement Strict Code Style and Linting**
    *   **Goal:** Improve code readability and catch common errors.
    *   **Implementation:** Adopt `Ruff` for all-in-one linting and formatting, configured via `pyproject.toml`.
    *   **Status Update (01.02.2026):** `black` and `ruff` installed and fully functional. `pyproject.toml` configured. Codebase has been formatted with `black` and linted with `ruff`.

3.  **Enforce Static Type Checking**
    *   **Goal:** Find type-related bugs before runtime.
    *   **Implementation:** Integrate `MyPy`, configured via `pyproject.toml`, and incrementally add missing type hints.

4.  **Externalize Configuration**
    *   **Goal:** Make the application more flexible by removing hard-coded values.
    *   **Implementation:** Use `Pydantic` to manage settings from a central configuration source.

5.  **Refine Dependency Management**
    *   **Goal:** Ensure reproducible builds by locking sub-dependencies.
    *   **Implementation:** Use `pip-tools` to compile a fully-pinned `requirements.txt` from a `requirements.in` file.