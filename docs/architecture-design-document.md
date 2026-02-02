# Architecture Design Document

## 1. Vision: A Hybrid of Illustrator and Origin

This document outlines the architectural blueprint for the application. The vision is to create a hybrid tool that combines the fluid, intuitive design capabilities of a vector graphics editor with the powerful data analysis and plotting features of scientific software.

The architecture must support a highly interactive, non-modal user experience where data visualization, analysis, and publication-quality figure design are part of a single, seamless workflow.

## 2. Core Technologies

-   **Python 3.10+**
-   **PySide6 (Qt 6)**
-   **Matplotlib**
-   **Pandas**

## 3. Architectural Design: Scene-Graph & Tool-Based Model

The application uses a robust architecture centered around a **scene graph**, a **tool-based controller system**, a **unified properties inspector**, and a **command history**.

### 3.1. The Scene Graph: A Hierarchical Model

The application's state is represented by a **scene graph**, a tree structure that defines the layering, grouping, and relationships of all objects on the canvas.

-   **`ApplicationModel`**: Manages the root of the scene graph and the current selection state.
-   **`SceneNode`**: The abstract base class for all objects in the scene (e.g., plots, shapes).
-   **`PlotNode`**: A specialized node for a single subplot, containing its data (as a DataFrame) and plot-specific properties.
-   **`GroupNode`**: A container for grouping other nodes.

### 3.2. Tool-Based Event Handling

A `ToolManager` manages the currently active tool (e.g., `SelectionTool`) and delegates all canvas events (mouse presses, moves, etc.) to it. This makes it easy to add new interactive tools in the future.

### 3.3. The Properties Inspector: A Unified, Non-Modal View

A non-modal **Properties Panel** (`PropertiesView`) is a permanent part of the main window. It listens for selection changes in the model and dynamically displays widgets relevant to the selected object, allowing for live updates.

### 3.4. The Command & History System: Enabling Undo/Redo

All actions that modify the application state are encapsulated in `Command` objects (e.g., `ChangePropertyCommand`). A `CommandManager` executes these commands and maintains an undo/redo stack, providing robust, application-wide history.

### 3.5. View Construction: The Builder Pattern

To maintain a clean separation of concerns and enhance testability, the application's main window (`MainWindow`) is constructed using the **Builder pattern**.

-   **`MainWindowBuilder`**: This dedicated class is responsible for the entire construction and assembly process of the `MainWindow`. It creates all child components (the canvas widget, properties dock, menu bar, etc.) and assembles them into the final `MainWindow` instance.
-   **Decoupled View**: This approach decouples the `MainWindow` from its own complex creation logic. The `MainWindow` class is a simpler, more passive component that is configured by the builder, making it significantly easier to instantiate and test in isolation.
