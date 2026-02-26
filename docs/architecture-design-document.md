# Architecture Design Document

## 1. Vision: A Hybrid of Illustrator and Origin with a Focus on Reproducibility

This document outlines the architectural blueprint for the application. The vision is to create a hybrid tool that combines the fluid, intuitive design capabilities of a vector graphics editor (like Illustrator/Figma) with the powerful data analysis and plotting features of scientific software (like Origin/GraphPad). A strong emphasis is placed on reproducibility, ease of use for creating publication-quality figures, and robust extensibility for future features.

The architecture must support a highly interactive, non-modal user experience where data visualization, analysis, and publication-quality figure design are part of a single, seamless workflow.

## 2. Core Technologies

-   **Python 3.13+**
-   **PySide6 (Qt 6)**: For the rich graphical user interface.
-   **Matplotlib**: The primary plotting backend.
-   **Pandas**: For efficient data handling and manipulation.
-   **PyYAML**: For externalized configuration management.

# 3. Core Architectural Patterns

This section defines the fundamental architectural patterns that form the foundation of the application. These principles govern how components are structured, how they interact, and how responsibilities are separated. Adherence to these patterns is critical for maintaining the codebase's stability, testability, and scalability.

## 3.1. Overall Interaction Pattern: Model-View-Presenter (MVP)

The application employs the **Model-View-Presenter (MVP)** pattern, specifically the **"Passive View"** variant. This pattern enforces a strict separation of concerns between the application's data and business logic (Model), the user interface (View), and the application logic that handles user input (Presenter).

*   **Model (`ApplicationModel`):** The single source of truth for all application data and state. It is a "headless" component, containing no UI-specific code. Its responsibilities are limited to managing its internal state, enforcing business rules, and notifying observers when its state changes via signals.

*   **View (`MainWindow`, UI Panels):** A passive component whose sole responsibilities are to display data it is explicitly given and to capture raw user input (e.g., clicks, key presses), which it forwards to the Presenter. The View has no direct knowledge of the Model.

*   **Presenter (Controllers):** The mediator between the Model and the View. It contains all application and presentation logic. It responds to user input from the View, manipulates the Model (typically via the Command Pattern), and formats data from the Model to pass to the View for display. In this codebase, the Presenter role is fulfilled by the various **Controllers** (e.g., `ProjectController`, `NodeController`, `LayoutController`, `CanvasController`).

## 3.2. Decoupling with Event-Based Communication and Interfaces

Decoupling is central to this architecture, achieved through a strategic combination of event-based communication and explicitinterfaces.

*   **Event-Based Communication for Orchestration:** The `EventAggregator` is the primary mechanism for cross-component interaction and workflow orchestration. Components communicate bypublishing and subscribing to specific Events rather than direct calls. This completely decouples publishers from subscribers, enhancingscalability, testability, and clarity of application flow. It is primarily used for requests and state changes that are expected to have multiple listeners,allowing components to react to relevant events without direct knowledge of their origin. The communication contract is defined by the event type and its payload.

*   **Interfaces for Explicit Dependencies:** Abstract interfaces are utilized when a clear, direct, and singular dependency exists between two specific parts of the system. Theyestablish precise contracts for what functionality a component expects from its dependency. This ensures that a component does not rely on a concreteimplementation, promoting loose coupling for dependencies where a one-to-one relationship is fundamental, rather than a many-to-many eventbroadcast. The `CompositionRoot` remains responsible for injecting concrete implementations adhering to these interface contracts.

## 3.2. State Management Pattern: The Scene Graph Model

The application's core data model is not an arbitrary structure; it is specifically a **Scene Graph**—a hierarchical tree of nodes. This is a foundational decision that dictates how all visual elements are managed.

*   **Hierarchy and Grouping:** The tree structure allows complex figures to be composed of simple parts (nodes), which can be grouped and transformed together.
*   **Rendering Order:** The graph defines the z-order and layering of all visual elements.
*   **Targeted Updates:** It allows for efficient updates and hit-testing (i.e., determining which object is under the cursor).

## 3.3. History and Action Pattern: The Command Pattern

All actions that modify the state of the `ApplicationModel` must be encapsulated in **Command** objects. This is a strict requirement.

*   **Encapsulation:** Each command object contains all information required to perform an action and, crucially, to undo it.
*   **Undo/Redo:** A central `CommandManager` service executes these commands and maintains undo and redo stacks. This provides a robust, application-wide history mechanism.
*   **Decoupling:** This pattern decouples the UI components that initiate actions (e.g., menu items, buttons) from the objects that perform the work.

## 3.4. Assembly and Dependency Pattern: The Composition Root

The entire application is constructed and wired together in a single, dedicated location: the **`CompositionRoot`**.

*   **Centralized Construction:** The `CompositionRoot` is the only place in the application that has knowledge of concrete component classes. It is responsible for instantiating all Models, Views, Presenters, and Services.
*   **Dependency Injection (DI):** By centralizing construction, the `CompositionRoot` enables DI throughout the application. It injects dependencies (typically as abstract interfaces) into each component's constructor, meaning no component is responsible for finding or creating its own dependencies. This is critical for achieving loose coupling and high testability.

# 4. Key Components and Services

This section describes the major *concrete* components that operate within the architecture defined in Section 3. While Section 3 describes the abstract patterns, this section introduces the key players and their specific jobs.

### 4.1. Domain Logic and Scene Composition

This section details the key components that make up the application's core domain: the scene and its contents.

*   **4.1.1. Node Structure (`src/models/nodes/`)**: The building blocks of the scene graph. All objects on the canvas (plots, shapes, text) inherit from a common `SceneNode` base class. Key concrete implementations include `PlotNode`, `GroupNode`, `RectangleNode`, and `TextNode`. This provides a unified, hierarchical way to manage all visual elements.

*   **4.1.2. Layout Logic (`src/models/layout/`, `src/services/layout_manager.py`)**: The system for arranging nodes on the canvas. It is a concrete example of the Strategy Pattern.
    *   **`LayoutManager`**: A domain service that orchestrates layout calculations.
    *   **`LayoutEngine`s**: Swappable strategies (`GridLayoutEngine`, `FreeLayoutEngine`) that contain the specific mathematical logic for each layout mode.

*   **4.1.3. Plotting System (`src/ui/renderers/plotting_strategies.py`, `src/models/plots/`)**: The system for drawing data within a `PlotNode`. This is another application of the Strategy Pattern.
    *   **`PlottingStrategy`**: An interface for different plot types (e.g., line plot, scatter plot).
    *   **`PlotProperties`**: Data objects that hold the specific properties for each plot type (e.g., line color, marker style). The main `Renderer` uses the appropriate strategy to draw the plot based on its properties.

### 4.2. Core Application Services (`src/services/`)

This group includes services that provide fundamental, application-wide capabilities.

*   **`EventAggregator`:** The central hub for event-based communication. This service facilitates decoupled interaction between all application components by allowing them to publish and subscribe to specific events without direct knowledge of each other. It significantly enhances flexibility, testability, and scalability by replacing direct method calls for cross-component communication with an indirect, message-based system.
*   **`ToolService`**: Manages the collection of interactive canvas tools (e.g., `SelectionTool`) and is responsible for dispatching UI events to the currently active tool.
*   **`CommandManager`**: The concrete implementation of the Command Pattern. It executes all state-changing actions and manages the undo/redo stacks.

### 4.3. Configuration-Driven Design

A core principle of the application is its emphasis on externalized configuration. Hard-coded values, paths, and default settings are avoided wherever possible.

*   **`ConfigService` (`src/services/config_service.py`):** This is the concrete implementation of this principle. It is an application-wide service responsible for loading all settings from `.yaml` files and providing them to other components. This makes the application flexible and easier to modify without changing code.

### 4.4. UI Construction: Builders and Factories (`src/ui/builders/`, `src/ui/factories/`)

This group of components separates the complex task of UI creation from application logic.

*   **UI Builders (`MenuBarBuilder`, `ToolBarBuilder`):** Pure factories responsible for the one-time, static construction of complex UI widgets.
*   **UI Factories (`LayoutUIFactory`, `PlotPropertiesUIFactory`):** Dynamic factories that build and populate UI panels at runtime based on the application's state.

### 4.5. Rendering Pipeline (`src/ui/renderers/`)

This defines the component responsible for the final visual output.

*   **`Renderer`**: The class responsible for traversing the scene graph (from the `ApplicationModel`) and using the appropriate `PlottingStrategy` to render the model state to the Matplotlib canvas. It is the final bridge between application state and visual representation.
