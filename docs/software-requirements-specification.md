# Software Requirements Specification (SRS)

## 1. Introduction

This document specifies the functional and non-functional requirements for the Data Analysis and Figure Preparation GUI. It defines what the system must do from a user's perspective, incorporating the refined architectural vision for a robust, flexible, and extensible application.

## 2. Functional Requirements

### 2.1. Canvas and Figure Management
-   The user shall be able to view a central canvas containing one or more subplots, shapes, and text elements.
-   The application shall provide a default layout of subplots upon starting, configurable via `default_config.yaml`.
-   The user shall be able to create new, empty projects.
-   The user shall be able to open and save project files (`.sci` extension).

### 2.2. Data Handling
-   The user shall be able to load data into a subplot by dragging and dropping a `.csv` file onto it.
-   The system shall parse the `.csv` file and store the data in a structured format (Pandas DataFrame).
-   The system shall automatically render a default plot (e.g., line plot) using the first two suitable columns upon successful data loading, setting appropriate default axis labels and plot titles.

### 2.3. Object Selection and Interaction
-   The user shall be able to select one or more plots, shapes, or text elements by clicking or dragging a selection box on the canvas.
-   The application shall provide visual feedback for selected objects (e.g., bounding box highlights).
-   The user shall be able to open a properties panel for a selected object by double-clicking it.

### 2.4. Properties Inspector
-   The user shall be able to view and edit the properties of selected objects in a dedicated, non-modal side panel.
-   The properties panel shall dynamically adapt its displayed controls based on the type and properties of the selected object(s).
-   For `PlotNode`s, the user shall be able to edit:
    -   Plot Title
    -   X-Axis Label
    -   Y-Axis Label
    -   Data column used for the X-Axis
    -   Data column(s) used for the Y-Axis
    -   Plot Type (e.g., Line, Scatter)
    -   Minimum and maximum limits for the X-Axis
    -   Minimum and maximum limits for the Y-Axis
-   All changes made in the properties inspector shall be reflected on the canvas in real-time.

### 2.5. Command History (Undo/Redo)
-   The user shall be able to undo any action that modifies the state of the application model (e.g., changing a plot property, adding/removing a plot, layout changes).
-   The user shall be able to redo any undone action.

### 2.6. Configuration and Theming
-   The application shall load its default settings from a `default_config.yaml` file at startup.
-   The user shall be able to select from predefined color themes (e.g., "dark", "light").
-   The selected theme shall be applied dynamically to the application UI and persisted across sessions.

### 2.7. Layout Management (Core Feature)

The application shall provide a flexible and robust layout management system, allowing users to switch between managed grid-based layouts and free-form manual arrangements, with dynamic UI adaptation based on the active mode.

#### 2.7.1. Managed Grid Layout (Auto-Layout ON)
-   The user shall be able to enable/disable an "Auto Layout" mode (Managed Grid Layout).
-   When "Auto Layout" is ON:
    -   Plots shall be arranged in a grid structure, with their positions and sizes dynamically calculated by the `GridLayoutEngine`.
    -   The layout shall adapt dynamically to the addition or removal of plots, recalculating the grid to maintain non-overlapping, aesthetic spacing.
    -   The user shall be able to define the number of rows and columns for the grid.
    -   The user shall be able to interactively adjust the relative heights and widths of rows and columns (e.g., by dragging visual splitters), causing all affected plots to adapt their sizes accordingly.
    -   The system shall maintain configurable margins around the entire figure and gutters between plots.
    -   Plot titles and labels shall automatically adjust their spacing to avoid overlap, leveraging Matplotlib's layout capabilities.

#### 2.7.2. Free-Form Layout (Auto-Layout OFF)
-   When "Auto Layout" is OFF, plots shall retain their explicit `(x, y, width, height)` positions and sizes, allowing for complete manual control.
-   The user shall be able to freely move and resize individual plots using direct manipulation on the canvas.
-   The user shall be able to select multiple plots and apply alignment operations (e.g., "Align Left", "Align Center", "Align Top", "Align Bottom") to them.
-   The user shall be able to select multiple plots and apply distribution operations (e.g., "Distribute Horizontally", "Distribute Vertically") to them.
-   The user shall be able to define a "snapping grid" to assist with precise manual placement and resizing, causing plots to snap to grid lines during interactive manipulation.

#### 2.7.3. Layout Mode Transition
-   The user shall be able to switch between "Managed Grid Layout" and "Free-Form Layout" modes.
-   When switching from "Managed Grid Layout" to "Free-Form Layout", plots shall retain their last calculated grid positions as explicit geometries.
-   When switching from "Free-Form Layout" to "Managed Grid Layout", the system shall apply a "snap back to grid" algorithm that arranges the plots into a coherent grid, attempting to preserve relative visual order.

### 2.8. Toolbar and Menus
-   The application shall provide a customizable toolbar for quick access to frequently used tools (e.g., selection, zoom).
-   The application shall have a comprehensive menu bar (File, Edit, View, Plot, Layout, Help).
-   The "Layout" menu shall dynamically present options relevant to the active layout mode (e.g., grid controls in Managed Grid mode, alignment/distribution in Free-Form mode).

### 2.9. Project Persistence
-   The system shall serialize the entire application state (scene graph, layout configuration, etc.) to a project file.
-   The system shall deserialize a project file, restoring the application to its saved state.

## 3. Non-Functional Requirements

### 3.1. Usability
-   The interface should be intuitive and discoverable for users familiar with both graphics editors and data plotting software.
-   The workflow shall be non-modal, avoiding disruptive pop-up dialogs for core editing tasks.
-   Layout and property changes shall provide immediate visual feedback.

### 3.2. Performance
-   The UI shall remain responsive during all user interactions, including interactive dragging of objects, editing properties, and dynamic layout recalculations.
-   Data loading for moderately-sized files shall be performed in the background to prevent freezing the UI.
-   Rendering updates shall be optimized to minimize visual flicker during interactive operations.

### 3.3. Reliability
-   The application shall handle invalid user inputs and file errors gracefully (e.g., invalid configuration files, corrupted project files).
-   The undo/redo system shall reliably revert/reapply any state-modifying action.

### 3.4. Extensibility
-   The architecture shall support the easy addition of new plot types, interactive tools, layout engines, and configuration options without requiring significant refactoring of existing core components.

### 3.5. Maintainability
-   The codebase shall adhere to Python best practices, including clear modularization, comprehensive type hinting, and consistent coding standards.
-   Documentation (internal code comments, ADR, SRS) shall be kept up-to-date.