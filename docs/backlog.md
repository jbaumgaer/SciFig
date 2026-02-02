# Backlog

This document tracks the implemented and future features of the Data Analysis GUI.

---

## Implemented Features

This section describes the functionality currently available in the application.

### Core Architecture (v2)

The application is built on a modern, robust architecture designed for interactivity and extensibility.

-   **Scene Graph Model**: The application state is managed by a hierarchical scene graph (`SceneNode`, `PlotNode`, `GroupNode`), allowing for complex object relationships.
-   **Tool-Based Controller**: A `ToolManager` delegates canvas events to the active tool. A `SelectionTool` for selecting, moving, and interacting with objects is implemented.
-   **Command & History System**: All actions that modify the application state are managed by a `CommandManager`, providing full Undo/Redo support (`Ctrl+Z` / `Ctrl+Y`).

### Figure & Plot Customization

-   **Unified Properties Inspector**: A non-modal sidebar allows for live, immediate editing of selected object properties. Double-clicking a plot will open the panel.
-   **Plot Properties**: The following properties of a selected plot can be modified:
    -   Title
    -   X-Axis and Y-Axis Labels
    -   X-Axis and Y-Axis data columns (via dropdown selectors)
    -   X-Axis and Y-Axis limits

### Data Handling

-   **CSV Data Import**: Users can drag and drop `.csv` files directly onto a subplot to load data.
-   **Default Layout**: The application starts with a default 2x2 grid of empty plots.
-   **Basic Data Plotting**: Loaded data is rendered as a simple line plot. If no columns are specified, the first two columns in the dataset are used by default.

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

    # Backlog

Tasks are broken down by functional Epics → Features → individual Tasks, with priority (P0, P1, P2) and size (S, M, L).

---

## Epic: Canvas & Layout

### Feature: Subplot Management
- [ ] (P0, M) Implement multi-subplot canvas with default layout
- [ ] (P0, M) Enable selection of a subplot
- [ ] (P0, M) Open properties panel on double-click
- [ ] (P1, M) Zooming and panning support
- [ ] (P1, S) Magnification indicator display
- [ ] (P1, M) Alignment and distribution tools

---

## Epic: Object & Layer Management

### Feature: Layer System
- [ ] (P1, L) Implement Layer model (visibility, lock, z-order)
- [ ] (P1, M) Render layers in canvas draw order
- [ ] (P1, M) Layer panel UI: create, delete, reorder
- [ ] (P2, M) Drag-and-drop reorder in panel

### Feature: Grouping & Selection
- [ ] (P1, S) Group objects
- [ ] (P1, S) Ungroup objects
- [ ] (P1, M) Multi-selection of objects
- [ ] (P1, M) Object stacking/order adjustments

---

## Epic: Drawing & Annotation Tools

### Feature: Shape & Path Tools
- [ ] (P0, S) Rectangle, ellipse, line shapes
- [ ] (P1, L) Path tool (Bezier curves) creation/editing

### Feature: Text Tools
- [ ] (P1, M) On-canvas text editing
- [ ] (P2, M) Rich text formatting (bold, italic)
- [ ] (P2, L) LaTeX integration

### Feature: Image & Style
- [ ] (P1, M) Drag-and-drop image import (PNG/JPG)
- [ ] (P1, M) Render image in subplot
- [ ] (P2, M) Resize and position image on canvas
- [ ] (P2, M) Eyedropper tool for style copy
- [ ] (P2, M) Save reusable styles/templates (strokes, fills, gradients)

---

## Epic: Data Management & Interaction

### Feature: Data Import
- [ ] (P0, M) Load CSV data via drag-and-drop
- [ ] (P1, L) Excel import support
- [ ] (P1, L) HDF5/SQL import support
- [ ] (P2, L) Folder batch import

### Feature: Interactive Data
- [ ] (P1, M) Interactive data worksheet dockable panel
- [ ] (P1, S) Display data source path in properties panel
- [ ] (P1, M) Multi-sheet workbook support

---

## Epic: Plotting & Visualization

### Feature: Plot Types
- [ ] (P0, M) Line, scatter, bar plots
- [ ] (P1, M) Multi-axis support
- [ ] (P1, M) Trellis/facet plots
- [ ] (P0, M) Automatic default rendering on data load

---

## Epic: Data Analysis & Processing

### Feature: Analysis Gadgets
- [ ] (P1, M) Region of Interest tool
- [ ] (P1, M) Basic measurement tools

### Feature: Curve Fitting
- [ ] (P1, L) Built-in fit functions
- [ ] (P1, L) User-defined function fitting

### Feature: Signal Processing
- [ ] (P2, M) Smoothing and filtering
- [ ] (P2, M) FFT analysis

---

## Epic: Project & File Management

### Feature: Project & Template
- [ ] (P0, M) Save/load project file
- [ ] (P2, M) Template project layouts

### Feature: Export
- [ ] (P1, M) PNG export
- [ ] (P1, M) Vector export (SVG, PDF, EPS)

### Feature: Configuration & Paths
- [ ] (P1, S) Path handling via pathlib
- [ ] (P2, M) Externalized configuration management via Pydantic

---

## Epic: Undo/Redo & Command History
- [ ] (P0, M) Track all state-changing actions
- [ ] (P0, M) Implement full undo/redo stack for plots and canvas modifications
