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

The application uses a robust architecture centered around a **scene graph**, specialized **controllers**, domain-specific **services**, a **tool-based event system**, and a **pluggable layout engine**. Key principles include **Dependency Injection**, **Strategy Pattern**, and **Factory Pattern** to ensure a clean, stable, predictable, and scalable system.

### 3.1. The Scene Graph: A Hierarchical Model (`src/models/application_model.py`)

The application's core state is represented by an `ApplicationModel` which acts as the single source of truth. It manages the root of the **scene graph**, a hierarchical tree structure that defines the layering, grouping, and relationships of all objects on the canvas.

-   **`ApplicationModel`**: Located in `src/models/application_model.py`, it manages the root of the scene graph (`SceneNode`), the current selection state, and the application's global layout configuration (`LayoutConfig`). It emits signals (`modelChanged`, `selectionChanged`, `layoutConfigChanged`) to notify dependent components of state changes.
-   **`SceneNode`**: The abstract base class for all objects in the scene (e.g., plots, shapes), located in `src/models/nodes/scene_node.py`. Provides common properties like visibility, ID, and basic hit-testing.
-   **`PlotNode`**: A specialized node for a single subplot, located in `src/models/nodes/plot_node.py`, containing its associated data (as a Pandas DataFrame), plot-specific properties (e.g., `LinePlotProperties`, `ScatterPlotProperties`), and a reference to its Matplotlib `Axes` object.
-   **`GroupNode`**: A container for grouping other nodes, located in `src/models/nodes/group_node.py`, allowing them to be manipulated as a single unit.

### 3.2. Configuration Management (`src/services/config_service.py`)

All application-wide defaults, settings, and "magic strings" are externalized into `configs/default_config.yaml`.

-   **`ConfigService`**: Located in `src/services/config_service.py`, this singleton-like service is responsible for loading and providing access to configuration values using dot-separated keys (e.g., `figure.default_width`). It handles default values and gracefully manages missing keys. This decouples settings from code, enhancing flexibility and maintainability.

### 3.3. Logging (`src/services/logger_service.py`)

A centralized logging system is integrated to provide clear insight into application behavior, aid debugging, and track user actions.

-   **`LoggerService` (Renamed from `LoggerConfig`)**: Located in `src/services/logger_service.py`, it configures Python's `logging` module based on settings from `ConfigService` (e.g., log level, console/file output).

### 3.4. Dynamic Theming (`src/core/theme_manager.py`)

The application's visual theme can be dynamically selected and applied.

-   **`ThemeManager`**: Located in `src/core/theme_manager.py`, it is responsible for loading theme definitions (styles and `QPalette` color roles) from `ConfigService` and applying them to the `QApplication` instance at runtime.

### 3.5. Layout Management: Controllers, Services, and Pluggable Engines

This core feature provides flexible control over plot arrangement using a **Strategy Pattern** for layout logic and **Factory/Builder Patterns** for UI adaptation. It is now split between a UI-facing Controller and a domain-specific Manager and Model components.

-   **`LayoutController` (`src/controllers/layout_controller.py`)**:
    *   **Role:** Acts as the primary intermediary between the UI and the layout management logic. It handles user interactions related to layout (e.g., button clicks for "Align Left", slider changes for "Grid Gutter", menu selections for "Set Layout Mode").
    *   **Responsibilities:** Translates UI events into calls to the `LayoutManager` and constructs/executes `BatchChangePlotGeometryCommand`s via the `CommandManager` to ensure undoability.
-   **`LayoutManager` (`src/services/layout_manager.py`)**:
    *   **Role:** The core domain service for managing the application's layout state and delegating layout calculations. It encapsulates business rules and state related to layout, independent of direct UI interaction.
    *   **Responsibilities:** Manages the `ApplicationModel`'s `current_layout_config`, orchestrates `LayoutEngine`s, and emits signals when layout state changes.
-   **`LayoutConfig` (Abstract Base Class, `src/models/layout/layout_config.py`):** Represents the state/parameters specific to a layout mode.
    -   **`FreeConfig`**: Minimal state, signifying free-form.
    -   **`GridConfig`**: Stores grid parameters (`rows`, `cols`, `row_ratios`, `col_ratios`, `margins`, `gutters`).
-   **`LayoutEngine` (Abstract Base Class, `src/models/layout/layout_engines.py`):** Defines the contract for layout calculation.
    -   `calculate_geometries(plots: List[PlotNode], config: LayoutConfig) -> Dict[PlotNode, Tuple[float, float, float, float]]`: Takes a list of plots and an engine-specific `LayoutConfig` to return calculated geometries.
-   **`FreeLayoutEngine` (Concrete Strategy, `src/models/layout/layout_engines.py`):** Implements free-form specific operations like "Align" and "Distribute".
-   **`GridLayoutEngine` (Concrete Strategy, `src/models/layout/layout_engines.py`):** Implements grid-based tiling, calculating `(x, y, w, h)` based on `GridConfig`.
-   **`LayoutUIFactory` (`src/ui/factories/layout_ui_factory.py`):**
    *   Registers builder functions for each layout mode.
    *   Dynamically creates and updates UI elements (QActions, menus, dialogs) in `MainWindow` or `PropertiesPanel` based on the active `LayoutMode` reported by `LayoutManager`.

### 3.6. Tool-Based Event Handling (`src/services/tool_management/tool_service.py`)

A `ToolService` now manages the currently active interactive tool (e.g., `SelectionTool`, `ZoomTool`) and delegates all canvas events (mouse presses, moves, key presses) to it. This design makes it easy to add new interactive tools in the future, each encapsulating its own interaction logic.

-   **`ToolService` (Renamed from `ToolManager`)**: Located in `src/services/tool_management/tool_service.py`, it manages the collection of available tools and the currently active tool. It dispatches canvas events (received from `CanvasController`) to the active tool's specific event handlers.
-   **`BaseTool` (`src/services/tool_management/tools/base_tool.py`)**: Abstract base class for all interactive tools, defining the common interface for event handling (e.g., `mouse_press_event`, `mouse_move_event`).
-   **`SelectionTool` (`src/services/tool_management/tools/selection_tool.py`)**: A concrete tool implementation for selecting nodes on the canvas.

### 3.7. The Properties and Layout Panel (`src/ui/panels/properties_panel.py`)

A non-modal `PropertiesPanel` is a permanent part of the main window. It dynamically displays UI elements for both individual node properties and global layout settings, orchestrated by dedicated controllers.

-   **`PropertiesPanel` (Renamed from `PropertiesView`)**: Located in `src/ui/panels/properties_panel.py`, this UI container dynamically displays controls based on the application's context (e.g., selected node, active layout mode). It orchestrates UI elements provided by the `NodeController` and `LayoutController`.
-   **`NodeController` (`src/controllers/node_controller.py`)**:
    *   **Role:** Manages the intrinsic attributes (properties) and specific behaviors of *selected `SceneNode`s*.
    *   **Responsibilities:** Listens for `ApplicationModel.selectionChanged`, populates the `PropertiesPanel` with UI appropriate for the selected node(s) (using `PropertiesUIFactory`), and executes `ChangePropertyCommand`s.
-   **`PropertiesUIFactory` (`src/ui/factories/properties_ui_factory.py`):**
    *   Registers builder functions for each `SceneNode` type.
    *   Dynamically creates and updates the specific UI widgets for editing properties of different node types (e.g., `LinePlotProperties` vs. `ScatterPlotProperties`).

### 3.8. The Command & History System: Enabling Undo/Redo (`src/services/commands/command_manager.py`)

All actions that modify the application state are encapsulated in `Command` objects. A `CommandManager` executes these commands and maintains an undo/redo stack, providing robust, application-wide history and state management.

-   **`CommandManager`**: Located in `src/services/commands/command_manager.py`, it executes `BaseCommand` objects and maintains an undo/redo stack.
-   **`BaseCommand`**: Abstract base class for all commands.

### 3.9. Project Management (`src/controllers/project_controller.py`)

A dedicated controller handles all aspects of project file management.

-   **`ProjectController`**: Located in `src/controllers/project_controller.py`, it is responsible for managing all project-related operations, including saving (`.sci`), opening, and maintaining a list of recent files using `QSettings`.

### 3.10. Application Assembly: The Composition Root (`src/core/composition_root.py`)

To maintain a clean separation of concerns and enhance testability, the entire application's component graph is constructed and wired together using the **Builder pattern**.

-   **`CompositionRoot` (Renamed from `ApplicationAssembler`)**: Located in `src/core/composition_root.py`, this dedicated class is responsible for the entire construction and assembly process of all core application components (Models, Controllers, Services, UI Builders). It instantiates all services, builds the main window and its sub-components (using builders), and wires up all signals and slots.
-   **Decoupled Components**: This approach decouples individual components from their complex instantiation and dependency management, making them simpler, more focused, and easier to test in isolation.
-   **Consistent UI Construction with Builders (`src/ui/builders/`)**: Complex UI elements like `MainWindow`, `PropertiesPanel`, `CanvasWidget`, `QMenuBar`, and `QToolBar` are now constructed by dedicated builder classes (e.g., `main_window_builder.py`, `properties_panel_builder.py`). This ensures a consistent approach to UI construction across the application.

## 4. Cross-Cutting Concerns

-   **Dependency Injection**: Used extensively throughout the architecture. Components receive their dependencies (e.g., `ConfigService`, `ApplicationModel`) through their constructors, promoting loose coupling and testability.
-   **Signals & Slots (PySide6)**: Used for asynchronous communication between components, especially between Models, Views, and Controllers, ensuring responsiveness and decoupling.
-   **Separation of Concerns**: Each class and module has a clearly defined responsibility, minimizing inter-dependencies and enhancing maintainability.
-   **Constants & Types (`src/shared/`)**: Centralized definitions for shared constants and custom types.
-   **Utilities (`src/shared/`)**: General-purpose utility functions.
-   **Static Assets (`assets/`)**: Dedicated location at project root for icons, images, etc.
