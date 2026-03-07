# Application Folder and File Structure

This document describes the current architectural organization of the SciFig project. The structure follows the Model-View-Presenter (MVP) pattern, utilized alongside the Command and Event-driven orchestration patterns to ensure a highly decoupled, testable, and maintainable codebase.

---

## High-Level Overview

The codebase is organized into logical domains, separating core application logic, user interface components, data models, infrastructure services, and shared utilities.

```
.
├── main.py                     # Project entry point
├── configs/                    # External configuration files (.yaml, .mplstyle)
├── data/                       # Sample data files
├── docs/                       # Project documentation (ADD, TDDs, Backlog)
├── tests/                      # Comprehensive test suite (unit, integration, e2e)
└── src/                        # Application source code package
    ├── app.py                  # Main application setup and bootstrap
    ├── core/                   # Assembly and cross-cutting core components
    ├── controllers/            # Presenter layer (Mediators and Orchestrators)
    ├── interfaces/             # Abstract definitions for decoupled components
    ├── models/                 # Headless Model layer (Data and Business Logic)
    ├── processing/             # Specialized data parsing and worker objects
    ├── services/               # Infrastructure services and Command implementations
    ├── shared/                 # Generic constants, events, and value objects
    └── ui/                     # Passive View layer (Widgets, Builders, Renderers)
```

---

## Detailed Directory Breakdown

### `src/` (Root)
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`app.py`**: Contains the application bootstrapping logic (`run_application`). It initializes logging, creates the `QApplication`, invokes the `CompositionRoot` to assemble all components, applies the initial theme, and starts the main event loop.

### `src/core/`
The "Brain" of the application assembly and theme management.
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`composition_root.py`**: Contains the `CompositionRoot` class. It acts as the single source of truth for dependency injection. It instantiates all models, views, controllers, tools, and services, and wires their event subscriptions and dependencies together.
*   **`application_components.py`**: Contains the `ApplicationComponents` dataclass, which strictly defines and holds the object graph of the fully assembled application returned by the `CompositionRoot`.
*   **`theme_manager.py`**: Contains the `ThemeManager` class. It loads theme definitions from YAML configuration and manages the application's visual theme globally by applying Qt Styles, QPalettes, and Stylesheets to the `QApplication` instance.

### `src/controllers/`
The Presenter layer. These classes orchestrate workflows and translate user intents into state changes.
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`project_controller.py`**: Manages the high-level project lifecycle. It handles requests for new projects, opening templates, and saving/loading the `.sci` ZIP-based project format. It coordinates with the `ApplicationModel`'s lifecycle interface.
*   **`node_controller.py`**: The primary orchestrator for scene graph nodes. It handles property changes (renaming, visibility, locking), data assignment via `DataService`, and structural changes like plot deletion (using `MacroCommand` and `DeleteNodeCommand`). It also implements the "Bypass Pattern" for silent model reconciliation.
*   **`layout_controller.py`**: Manages figure-level layout operations. It translates UI requests for alignment, distribution, and grid parameter changes into executable commands. It acts as the mediator between the `LayoutUIFactory` and the `LayoutManager`.
*   **`canvas_controller.py`**: Acts as a "sanitizer" and orchestrator for the canvas. It translates raw Matplotlib backend events (button clicks, motion) into normalized figure coordinates and dispatches them to the `ToolService`. It also orchestrates the rendering of interaction previews (ghosts, handles) in the View.

### `src/interfaces/`
Contains abstract class definitions that define contracts between decoupled system layers.
*   **`project_io.py`**: Defines the `ProjectLifecycle`, `ProjectActions`, and `ProjectIOView` interfaces. These formalize how the Model, Controller, and View interact during file operations without direct coupling.

### `src/models/`
The Headless Model. Contains data structures with zero dependency on the UI.
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`application_model.py`**: The central state container and source of truth. It implements the `ProjectLifecycle` interface, managing the scene graph root, current selection, dirty status, and active layout configuration.

#### `src/models/layout/`
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`layout_config.py`**: Defines the data structures for layout configurations, including `FreeConfig` and `GridConfig`, along with value objects for `Margins` and `Gutters`.
*   **`layout_engine.py`**: Defines the abstract `LayoutEngine` base class.
*   **`free_layout_engine.py`**: A pass-through engine that respects individual node geometries for free-form arrangement.
*   **`grid_layout_engine.py`**: A complex engine that utilizes Matplotlib's `GridSpec` logic to calculate absolute geometries based on grid parameters (rows, columns, ratios).
*   **`layout_protocols.py`**: Defines runtime protocols for layout-related data exchange.

#### `src/models/nodes/`
The Scene Graph hierarchy components.
*   **`__init__.py`**: Exports the core node types and maps them for the factory.
*   **`scene_node.py`**: The base class for all objects in the scene. It manages parent-child relationships, visibility, locking, and hit-testing recursion. Includes the `node_factory` for deserialization.
*   **`plot_node.py`**: A specialized node representing a Matplotlib Axes. It stores its own `Rect` geometry, `PlotProperties`, and associated Pandas data.
*   **`group_node.py`**: A container node used to cluster multiple child nodes together for collective transformation.
*   **`rectangle_node.py`**: A specialized node for drawing simple vector rectangles.
*   **`text_node.py`**: A specialized node for managing text elements on the canvas.

#### `src/models/plots/`
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`plot_properties.py`**: Contains the deep hierarchy of dataclasses (e.g., `AxisProperties`, `ArtistProperties`, `LineProperties`) that define the visual state of a plot. Implements recursive `to_dict`/`from_dict` for serialization.
*   **`plot_types.py`**: Defines enums and types for plot components, such as `ArtistType`, `TickDirection`, and `SpinePosition`.

### `src/processing/`
Specialized worker objects for data-intensive background tasks.
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`data_loader.py`**: Contains the `DataLoader` class, a `QObject` worker designed to run in background threads. It handles the raw parsing of CSV/TSV data into Pandas DataFrames and notifies the system of completion via signals.

### `src/services/`
Infrastructure and specialized domain services.
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`event_aggregator.py`**: The central event bus. Implements the Publish-Subscribe pattern to facilitate decoupled communication across all system layers.
*   **`config_service.py`**: Manages the loading and retrieval of application-wide settings from YAML files. Supports dot-notated key access.
*   **`data_service.py`**: Orchestrates asynchronous data loading tasks by managing background threads and workers (`DataLoader`).
*   **`layout_manager.py`**: A domain-specific service that orchestrates layout calculations by delegating to specialized engines (`FreeLayoutEngine`, `GridLayoutEngine`).
*   **`property_service.py`**: A stateless utility for navigating and modifying nested Model attributes via string paths. Supports wildcards and type-safe coercion.
*   **`style_service.py`**: A factory that resolves flat theme keys from `.mplstyle` files into deep, hierarchical `PlotProperties` dataclass trees.
*   **`tool_service.py`**: Manages the registry of interactive canvas tools and dispatches UI events to the currently active tool.
*   **`logger_service.py`**: Configures the application-wide logging system based on settings.

#### `src/services/commands/`
Implementation of the Command Pattern for reversible state changes.
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`base_command.py`**: The abstract base class for all commands.
*   **`command_manager.py`**: Manages the undo/redo stacks and executes all state-changing actions.
*   **`macro_command.py`**: A composite command that groups multiple sub-commands into a single atomic undoable unit.
*   **`add_plot_command.py`**: Handles the addition of new plot nodes to the scene graph.
*   **`delete_node_command.py`**: Handles the removal of a single node, storing its state for full restoration on undo.
*   **`batch_change_plot_geometry_command.py`**: Atomically updates the `Rect` geometry of one or many plot nodes.
*   **`change_plot_property_command.py`**: A generic command for changing any nested property via `PropertyService`.
*   **`apply_data_to_node_command.py`**: A macro command that updates a node's dataframe and automatically resets its axis mappings and limits.
*   **`change_children_order_command.py`**: Reorders sibling nodes within the scene graph (used for Z-order management).
*   **`change_grid_parameters_command.py`**: Updates the global grid configuration parameters.

#### `src/services/tools/`
Interactive canvas tools that interpret user input.
*   **`__init__.py`**: Contains the `MockTool` implementation.
*   **`base_tool.py`**: The abstract base class defining the interface for all interactive tools.
*   **`selection_tool.py`**: Handles node selection, high-performance moving (ghosting), and keyboard-driven deletion.
*   **`add_plot_tool.py`**: Handles interactive plot creation via rubber-banding or direct clicks.

### `src/shared/`
Value objects and utilities shared across all layers.
*   **`__init__.py`**: Marks the directory as a Python package.
*   **`events.py`**: The central `Events` Enum. It defines the complete communication contract for the `EventAggregator`, including all notification and request event types.
*   **`geometry.py`**: Contains the robust `Rect` dataclass used for all coordinate and geometry logic in normalized figure space.
*   **`constants.py`**: Centralizes application-wide constants, such as `ToolName` and `LayoutMode` enums, and the `IconPath` configuration utility.
*   **`types.py`**: Defines custom type aliases used throughout the application (e.g., `PlotID`, `Rect` tuple alias).
*   **`exceptions.py`**: Defines custom application exceptions like `ConfigError`.
*   **`utils.py`**: Provides generic utility classes, such as the `Debouncer` for signal rate-limiting.

### `src/ui/`
The Passive View layer. Consolidates all UI-related components and rendering logic.
*   **`__init__.py`**: Marks the directory as a Python package.

#### `src/ui/builders/`
Static factories using the Builder Pattern for one-time construction of complex UI components.
*   **`menu_bar_builder.py`**: Constructs the hierarchical `QMenuBar`, including file, edit, and view menus.
*   **`ribbon_bar_builder.py`**: Constructs the complex multi-tab `RibbonBar`, populating groups and actions for "Insert", "Design", and "Layout".
*   **`tool_bar_builder.py`**: Constructs the vertical `QToolBar` for active tool selection.

#### `src/ui/factories/`
Dynamic factories using the Factory Pattern for runtime UI generation.
*   **`plot_properties_ui_factory.py`**: Generates property-specific widgets (e.g., Line vs. Scatter controls) for the SidePanel at runtime based on the selected plot type.
*   **`layout_ui_factory.py`**: Builds the granular controls for Grid and Free-form layout modes.

#### `src/ui/panels/`
Dockable UI containers that aggregate multiple widgets.
*   **`side_panel.py`**: A `QTabWidget` container that hosts the various sidebar tabs.
*   **`properties_tab.py`**: The dynamic property editor tab. It reacts to selection changes and delegates widget creation to the `PlotPropertiesUIFactory`.
*   **`layers_tab.py`**: Displays the Scene Graph as a hierarchical tree, allowing for selection and visibility control.
*   **`layout_tab.py`**: Hosts the controls for figure-level layout management.

#### `src/ui/renderers/`
Components responsible for visual translation from Model to View.
*   **`figure_renderer.py`**: The scientific rendering engine. It maps the `PlotNode` tree onto the Matplotlib `Figure` and its Axes.
*   **`overlay_renderer.py`**: The reactive interaction engine. It draws transient Qt overlays (handles, ghosts, guides) directly on the `QGraphicsScene`.
*   **`plotting_strategies.py`**: Implements the Strategy Pattern for different plot types (Line, Scatter, Image, etc.).

#### `src/ui/widgets/`
Reusable, self-contained custom UI controls.
*   **`canvas_widget.py`**: A specialized `QGraphicsView` that hosts the Matplotlib canvas and provides coordinate mapping and event capture.
*   **`ribbon_bar.py`**: Custom widget implementing the ribbon-style tabbed toolbar.

#### `src/ui/windows/`
Top-level application windows.
*   **`main_window.py`**: The primary application window. It integrates the menu, ribbon, toolbar, and sidebar, and handles high-level modal dialogs.

---

## Structural Principles

1.  **Strict Decoupling**: Components communicate primarily via the `EventAggregator`.
2.  **Unidirectional Data Flow (mostly)**: View -> Controller -> Command -> Model -> Event -> Renderer/View.
3.  **Command Pattern**: All permanent state modifications are reversible via the `CommandManager`.
