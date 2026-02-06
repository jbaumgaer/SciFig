# Architecture Design Document

## 1. Vision: A Hybrid of Illustrator and Origin with a Focus on Reproducibility

This document outlines the architectural blueprint for the application. The vision is to create a hybrid tool that combines the fluid, intuitive design capabilities of a vector graphics editor (like Illustrator/Figma) with the powerful data analysis and plotting features of scientific software (like Origin/GraphPad). A strong emphasis is placed on reproducibility, ease of use for creating publication-quality figures, and robust extensibility for future features.

The architecture must support a highly interactive, non-modal user experience where data visualization, analysis, and publication-quality figure design are part of a single, seamless workflow.

## 2. Core Technologies

-   **Python 3.10+**
-   **PySide6 (Qt 6)**: For the rich graphical user interface.
-   **Matplotlib**: The primary plotting backend.
-   **Pandas**: For efficient data handling and manipulation.
-   **PyYAML**: For externalized configuration management.

## 3. Architectural Design: Layered, Modular, and Extensible

The application uses a robust architecture centered around a **scene graph**, a **tool-based controller system**, a **unified properties inspector**, a **command history**, and a **pluggable layout engine**. Key principles include **Dependency Injection**, **Strategy Pattern**, and **Factory Pattern** to ensure a clean, stable, predictable, and scalable system.

### 3.1. The Scene Graph: A Hierarchical Model (ApplicationModel)

The application's core state is represented by an `ApplicationModel` which acts as the single source of truth. It manages the root of the **scene graph**, a hierarchical tree structure that defines the layering, grouping, and relationships of all objects on the canvas.

-   **`ApplicationModel`**: Manages the root of the scene graph (`SceneNode`), the current selection state, and the application's global layout configuration (`LayoutConfig`). It emits signals (`modelChanged`, `selectionChanged`, `autoLayoutChanged`, `layoutConfigChanged`) to notify dependent components of state changes.
-   **`SceneNode`**: The abstract base class for all objects in the scene (e.g., plots, shapes). Provides common properties like visibility, ID, and basic hit-testing.
-   **`PlotNode`**: A specialized node for a single subplot, containing its associated data (as a Pandas DataFrame), plot-specific properties (e.g., `LinePlotProperties`, `ScatterPlotProperties`), and a reference to its Matplotlib `Axes` object.
-   **`GroupNode`**: A container for grouping other nodes, allowing them to be manipulated as a single unit.

### 3.2. Configuration Management (`ConfigService`)

All application-wide defaults, settings, and "magic strings" are externalized into `configs/default_config.yaml`.

-   **`ConfigService`**: A singleton-like service responsible for loading and providing access to configuration values using dot-separated keys (e.g., `figure.default_width`). It handles default values and gracefully manages missing keys. This decouples settings from code, enhancing flexibility and maintainability.

### 3.3. Logging (`LoggerConfig`)

A centralized logging system is integrated to provide clear insight into application behavior, aid debugging, and track user actions.

-   **`setup_logging`**: Configures Python's `logging` module based on settings from `ConfigService` (e.g., log level, console/file output).

### 3.4. Dynamic Theming (`ThemeManager`)

The application's visual theme can be dynamically selected and applied.

-   **`ThemeManager`**: Responsible for loading theme definitions (styles and `QPalette` color roles) from `ConfigService` and applying them to the `QApplication` instance at runtime.

### 3.5. Layout Management: Pluggable Engines and UI Adaptation

This is a core, sophisticated feature providing flexible control over plot arrangement. It uses a **Strategy Pattern** for layout logic and a **Factory Pattern** for UI adaptation.

-   **`LayoutMode` (Enum):** Defines the major layout paradigms (e.g., `FREE_FORM`, `GRID`). Stored in `ApplicationModel.current_layout_config`.
-   **`LayoutConfig` (Abstract Base Class):** Represents the state/parameters specific to a layout mode.
    -   **`FreeConfig`**: Minimal state, signifying free-form.
    -   **`GridConfig`**: Stores grid parameters (`rows`, `cols`, `row_ratios`, `col_ratios`, `margins`, `gutters`).
-   **`LayoutEngine` (Abstract Base Class):** Defines the contract for layout calculation.
    -   `calculate_geometries(plots: List[PlotNode], config: LayoutConfig) -> Dict[PlotNode, Tuple[float, float, float, float]]`: Takes a list of plots and an engine-specific `LayoutConfig` to return calculated geometries.
-   **`FreeLayoutEngine` (Concrete Strategy):** Implements free-form specific operations like "Align" and "Distribute". Its `calculate_geometries` would generally return the plots' existing geometries, acting as a pass-through unless performing a specific alignment/distribution operation.
-   **`GridLayoutEngine` (Concrete Strategy):** Implements grid-based tiling. Its `calculate_geometries` will calculate `(x, y, w, h)` based on the `GridConfig` and the arrangement of plots within the grid.
-   **`LayoutManager` (Context/Orchestrator):**
    -   Owns instances of all concrete `LayoutEngine`s (e.g., `FreeLayoutEngine`, `GridLayoutEngine`).
    -   Determines the currently active engine based on `ApplicationModel.current_layout_config.mode`.
    -   Provides high-level methods (e.g., `perform_align_left`, `apply_default_grid`) that delegate to the appropriate `LayoutEngine` and update the `ApplicationModel`'s `current_layout_config`.
    -   Handles transitions between layout modes (e.g., `snap_free_plots_to_grid` using `GridLayoutEngine` when switching from `FREE_FORM` to `GRID`).
    -   Emits signals (e.g., `layoutModeChanged`) for UI components to adapt.
-   **`LayoutUIFactory` (Factory Pattern for UI):**
    -   Registers builder functions for each `LayoutEngine` type.
    -   Dynamically creates and updates UI elements (QActions, menus, dialogs) in `MainWindow` based on the active `LayoutMode` reported by `LayoutManager`. This ensures the UI only presents relevant layout controls.

### 3.6. Tool-Based Event Handling (`ToolManager`)

A `ToolManager` manages the currently active interactive tool (e.g., `SelectionTool`, `ZoomTool`) and delegates all canvas events (mouse presses, moves, key presses) to it. This design makes it easy to add new interactive tools in the future, each encapsulating its own interaction logic.

### 3.7. The Properties Inspector: A Unified, Non-Modal View (`PropertiesView`)

A non-modal **Properties Panel** (`PropertiesView`) is a permanent part of the main window. It listens for selection changes in the model and dynamically displays widgets relevant to the selected `PlotNode` (using `PropertiesUIFactory`), allowing for live updates of plot properties.

### 3.8. The Command & History System: Enabling Undo/Redo (`CommandManager`)

All actions that modify the application state are encapsulated in `Command` objects (e.g., `ChangePropertyCommand`, `BatchChangePlotGeometryCommand`). A `CommandManager` executes these commands and maintains an undo/redo stack, providing robust, application-wide history and state management.

### 3.9. Application Assembly: The Builder Pattern (`ApplicationAssembler`)

To maintain a clean separation of concerns and enhance testability, the entire application's component graph is constructed and wired together using the **Builder pattern**.

-   **`ApplicationAssembler`**: This dedicated class is responsible for the entire construction and assembly process of the core application components (Model, Controllers, Managers, Views). It instantiates all services, builds the main window, and wires up all signals and slots.
-   **Decoupled Components**: This approach decouples individual components from their complex instantiation and dependency management, making them simpler, more focused, and easier to test in isolation.

## 4. Cross-Cutting Concerns

-   **Dependency Injection**: Used extensively throughout the architecture. Components receive their dependencies (e.g., `ConfigService`, `ApplicationModel`) through their constructors, promoting loose coupling and testability.
-   **Signals & Slots (PySide6)**: Used for asynchronous communication between components, especially between Model, Views, and Controllers, ensuring responsiveness and decoupling.
-   **Separation of Concerns**: Each class and module has a clearly defined responsibility, minimizing inter-dependencies and enhancing maintainability.