# Proposed Future Folder and File Structure

This document outlines the proposed refactoring of the project's folder and file structure, along with the rationale behind these changes. The goal is to improve intuitiveness, maintainability, scalability, and adherence to software architectural principles such as the Single Responsibility Principle (SRP), high cohesion, and low coupling.

---

## High-Level Overview

The new structure organizes the codebase into logical domains, moving away from a flat `src/` directory and explicitly separating core application logic, user interface components, data models, infrastructure services, and shared utilities.

```
.
├── main.py                     # Project entry point
├── assets/                     # Static assets (icons, images)
└── src/                        # Application source code package
    ├── app.py                  # Main application setup
    ├── core/                   # Core application services, composition root
    ├── controllers/            # Application logic and coordination
    ├── models/                 # Data structures and business entities
    ├── services/               # Infrastructure services, cross-cutting concerns
    ├── shared/                 # Generic utilities, constants, types
    └── ui/                     # User interface components
```

---

## Detailed Proposed Folder Structure and Rationale

Below is a detailed breakdown of the proposed folder and file structure, along with the rationale for each component.

### `main.py`
*   **Location:** Project root (`./main.py`)
*   **Purpose:** The initial entry point for the Python application. Its sole responsibility is to kick off the application startup process, typically by calling `src.app.run()`.
*   **Rationale:** Standard practice for Python applications to have a simple entry point at the project root.

### `assets/`
*   **Location:** Project root (`./assets/`)
*   **Purpose:** Contains static assets such as icons, images, and other media files used by the UI.
*   **Rationale:** Static assets are generally kept separate from source code, usually at the project root or in a dedicated `res/` or `static/` directory. This makes them easy to find and manage without cluttering the `src/` package. The `ConfigService` or `IconPath` constant would then point to this root-level `assets/` folder.

### `src/`
*   **Location:** Project root (`./src/`)
*   **Purpose:** The main Python package containing all application source code.
*   **Rationale:** Adheres to common project structuring where `src/` holds the primary source code package.

### `src/app.py`
*   **Location:** `src/app.py`
*   **Purpose:** Contains the main application setup logic, including error handling, initial configuration loading (if not handled by `composition_root`), and orchestrating the `CompositionRoot` to assemble the application. It acts as the "bootstrap" for the application within the package.
*   **Rationale:** Separates the package-internal application startup from the minimal `main.py` entry.

### `src/core/`
*   **Purpose:** Houses foundational application services and the composition root that wires the entire application together. These are central components that all other parts depend on or are orchestrated by.
*   **`composition_root.py` (Renamed from `application_assembler.py`)**
    *   **Rationale:** "Composition Root" precisely describes its Single Responsibility: assembling the entire object graph of the application. It creates and wires all dependencies.
*   **`application_components.py`**
    *   **Rationale:** A simple data structure to hold references to the fully assembled core components, returned by the `CompositionRoot`.
*   **`theme_manager.py`**
    *   **Rationale:** Manages the application's visual theme, a core application-wide concern that affects the UI but is distinct from individual UI components.

### `src/controllers/`
*   **Purpose:** Contains all controllers responsible for handling user input, orchestrating application flow, and mediating between models and views. This directory now reflects a clearer division of labor, addressing the "God Object" anti-pattern identified in the former `MainController`.
*   **`canvas_controller.py`**
    *   **Rationale:** Manages interactions on the canvas, primarily forwarding events to the `ToolService`. Its responsibility remains focused on canvas-specific input handling.
*   **`project_controller.py` (New, extracted from former `MainController`)**
    *   **Rationale:** Dedicated to managing all project-related operations, including saving (`.sci`), opening, and managing recent files. This cleanly separates file I/O concerns.
*   **`layout_controller.py` (New, extracted from former `MainController`)**
    *   **Rationale:** Responsible for all layout management logic, such as setting layout modes (grid/free-form), applying grid configurations, and executing alignment and distribution commands. It interacts with the `LayoutManager` and `CommandManager`.
*   **`node_controller.py` (New, refined from `PropertiesController` idea)**
    *   **Rationale:** Manages the intrinsic attributes and specific behaviors of *selected `SceneNode`s* (e.g., `PlotNode`, `TextNode`). Its job is to handle the logic for displaying, validating, and applying changes to individual object properties via the `CommandManager`. This name is more precise than `PropertiesController`.

### `src/models/`
*   **Purpose:** Defines the core data structures and business entities of the application, representing its state and logic.
*   **`application_model.py`**
    *   **Rationale:** The central data store and source of truth for the application's state, adhering to the Model in MVC.
*   **`layout/` (Sub-directory)**
    *   **Purpose:** Groups models specifically related to layout configurations and engines.
    *   **`layout_config.py`**
        *   **Rationale:** Defines the data structures for various layout configurations (e.g., `FreeConfig`, `GridConfig`).
    *   **`layout_engines.py` (Renamed from `layout_engine.py`)**
        *   **Rationale:** Contains the abstract `LayoutEngine` and its concrete implementations (`FreeLayoutEngine`, `GridLayoutEngine`). These are core domain logic components that define *how* layouts are calculated, hence their placement with layout models.
*   **`nodes/` (Sub-directory)**
    *   **Rationale:** Stays as a cohesive group of scene graph elements (`group_node.py`, `plot_node.py`, `scene_node.py`, `text_node.py`, etc.), representing the visual hierarchy.
*   **`plots/` (Sub-directory)**
    *   **Rationale:** Groups models specifically related to plot properties and types (e.g., `plot_properties.py`, `plot_types.py`), centralizing plot-specific model details.

### `src/services/`
*   **Purpose:** A dedicated location for infrastructure-level services or cross-cutting concerns that support the application but are not core business logic or UI-specific.
*   **`commands/` (Sub-directory)**
    *   **Rationale:** The Command pattern, encapsulated by `CommandManager`, provides a service to the application for managing undo/redo operations. Placing it here keeps the specific implementations of `BaseCommand` and its derivatives well-organized as an infrastructure concern.
*   **`config_service.py`**
    *   **Rationale:** Manages application configuration loading and access.
*   **`logger_service.py` (Renamed from `logger_config.py`)**
    *   **Rationale:** `_service` suffix is consistent with `config_service` and better reflects its role as a provider of logging functionality.
*   **`data_loader.py` (Moved from `src/processing/data_loader.py`)**
    *   **Rationale:** `DataLoader` is an infrastructure service responsible for asynchronous data I/O. Placing it here makes its role clearer as a utility service. (The `processing/` directory would be removed).
*   **`layout_manager.py` (Moved from `layout_manager.py`)**
    *   **Rationale:** The `LayoutManager` orchestrates layout engines and manages the active layout mode, acting as a domain-specific service that is consumed by the `LayoutController`. Its role is distinct from a UI controller but provides core layout management functionality.
*   **`tool_management/` (Sub-directory)**
    *   **Purpose:** Manages the state and behavior of interactive tools.
    *   **`tool_service.py` (Renamed from `tool_manager.py`)**
        *   **Rationale:** `ToolService` more accurately reflects its role as a service that manages tool state and dispatches events to the active tool, rather than being a direct UI controller. It's the orchestrator of tool *behavior*.
    *   **`tools/` (Sub-directory)**
        *   **Rationale:** Logical grouping for individual `BaseTool` implementations (e.g., `selection_tool.py`, `mock_tool.py`), which are behavioral strategies consumed by the `ToolService`. These are not UI controllers themselves.

### `src/shared/`
*   **Purpose:** For truly generic utilities, constants, and custom type definitions that are used across multiple domains and do not fit into a more specific category.
*   **`constants.py`**
    *   **Rationale:** Centralizes application-wide constant values.
*   **`types.py`**
    *   **Rationale:** Defines custom type aliases and data structures throughout the application.
*   **`utils.py`**
    *   **Rationale:** General-purpose utility functions that don't belong elsewhere.

### `src/ui/`
*   **Purpose:** Consolidates all user interface-related components, reflecting the "View" part of an MVC/MVP architecture. This provides clear boundaries for UI code.
*   **`builders/` (Sub-directory)**
    *   **Rationale:** Home for classes implementing the **Builder Pattern** for complex UI components. This ensures a consistent approach to UI construction, separating the "how" of building from the "what" of presentation.
        *   **`menu_bar_builder.py`**
        *   **`tool_bar_builder.py`**
        *   **`main_window_builder.py` (New)**: Constructs the `MainWindow` instance.
        *   **`canvas_widget_builder.py` (New)**: Constructs the `CanvasWidget` instance.
        *   **`properties_panel_builder.py` (New)**: Constructs the `PropertiesPanel` instance.
*   **`factories/` (Sub-directory)**
    *   **Rationale:** Home for classes implementing the **Factory Pattern** to create *dynamic internal UI elements* based on specific types or contexts.
        *   **`properties_ui_factory.py`**
        *   **`layout_ui_factory.py`**
*   **`panels/` (Sub-directory)**
    *   **Rationale:** For larger, often dockable, application-specific UI containers that aggregate multiple smaller widgets or dynamically change their content (e.g., property editors, history panels).
        *   **`properties_panel.py` (Renamed from `properties_view.py`)**
            *   **Rationale:** "Panel" is more descriptive of its role as a dynamic, dockable UI container than the generic "view."
*   **`renderers/` (Sub-directory)**
    *   **Rationale:** Groups components responsible for translating model data into visual output on the canvas.
        *   **`renderer.py`**
        *   **`plotting_strategies.py`**
*   **`widgets/` (Sub-directory)**
    *   **Rationale:** For reusable, self-contained, granular UI controls that can be embedded within other components (e.g., custom buttons, input fields, specialized display elements).
        *   **`canvas_widget.py`**
        *   **`column_mapping_widget.py` (New)**
        *   **`axes_limits_widget.py` (New)**
*   **`windows/` (Sub-directory)**
    *   **Rationale:** For top-level application windows (e.g., `main_window.py`).

---

## UI Construction Strategy (Builder vs. Factory)

To address the observed inconsistency in UI construction, the following strategy will be adopted:

*   **Builder Pattern for Top-Level/Complex UI Component Instantiation:**
    *   Classes in `src/ui/builders/` will be responsible for creating and configuring instances of complex UI components like `MainWindow`, `PropertiesPanel`, `CanvasWidget`, `QMenuBar`, and `QToolBar`. These builders will manage the step-by-step construction of these components and inject their dependencies (e.g., controllers, factories).
*   **Factory Pattern for Dynamic Internal UI Content:**
    *   Classes in `src/ui/factories/` will be responsible for creating *different types of internal UI elements* (e.g., the specific widgets for editing `LinePlotProperties` versus `ScatterPlotProperties`). These factories will use a registration mechanism to dynamically provide the correct sub-UI based on a given context or type.

This layered approach clearly separates the construction of the main UI containers from the dynamic generation of their internal content, leading to a more consistent, testable, and maintainable UI architecture.