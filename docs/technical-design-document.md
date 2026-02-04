# Technical Design Document (TDD)

This document is intended to provide detailed, technical implementation plans for specific new features or refactoring tasks. It serves as a blueprint for the developer (human or AI) executing the task.

A TDD should be created as part of the **"Reason & Plan"** phase for any sufficiently complex task.

---

## Epic: Canvas & Layout

### Feature: Zoom Feature
**Backlog Task:** Display zoom level in the corner  
**Background & Context:** Users need to know the current magnification of the canvas.

**Proposed Implementation:**  
1. **Model:** Add `zoom_level: float` property to `CanvasModel`.  
2. **View:** Add small widget in the lower corner to display `zoom_level`.  
3. **Controller:** Update `zoom_level` on mouse wheel events or zoom commands.  
4. **Renderer:** Trigger redraw when zoom changes.  

**Test Plan:**  
- Unit test zoom property updates correctly.  
- Verify corner widget updates on zoom events.  
- Ensure canvas redraw occurs.  

**Risks & Mitigations:**  
- Widget may overlap objects → place in reserved corner area.

---

## Epic: Object & Layer Management

### Feature: Layer Panel
**Backlog Task:** Manage layers (create, delete, rename, reorder, lock, toggle visibility)  
**Background & Context:** Users need structured access to objects; follows scene graph pattern.

**Proposed Implementation:**  
1. **Model:** Extend `SceneNode` hierarchy with `LayerNode`; maintain `layer_list` in `ApplicationModel`.  
2. **View:** Dockable `LayerPanel` widget with tree view, icons for visibility/lock, drag-and-drop reordering.  
3. **Controller:** Connect panel actions to `CommandManager` (`AddLayerCommand`, `DeleteLayerCommand`, `ReorderLayerCommand`).  
4. **Renderer:** Render layers in scene graph order; update when visibility or z-order changes.

**Test Plan:**  
- Unit tests for panel actions (add/delete/reorder).  
- Verify scene graph updates correctly.  
- Test undo/redo functionality.  

**Risks & Mitigations:**  
- Reordering may affect grouped nodes → encapsulate in commands to ensure atomic updates.

---

### Feature: Grouping & Ungrouping UI
**Backlog Task:** Group and ungroup multiple objects.

**Proposed Implementation:**  
1. **Model:** `GroupNode` to contain multiple `SceneNode`s.  
2. **View:** Enable multi-selection; right-click menu or button for group/ungroup.  
3. **Controller:** `GroupCommand` / `UngroupCommand` in `CommandManager`.  
4. **Renderer:** Render grouped nodes as a single selectable unit; individual nodes remain editable.

**Test Plan:**  
- Verify grouping/ungrouping operations.  
- Confirm undo/redo works correctly.  

**Risks & Mitigations:**  
- Grouped nodes must maintain relative positions; verify with unit tests.

---

## Epic: Drawing & Annotation

### Feature: Shape Tools
**Backlog Task:** Rectangle, ellipse, line shapes.

**Proposed Implementation:**  
1. **Model:** `ShapeNode` subclasses: `RectangleNode`, `EllipseNode`, `LineNode`.  
2. **View:** Canvas draws shapes; properties panel allows stroke/fill editing.  
3. **Controller:** ToolManager handles shape creation and manipulation.  
4. **Renderer:** Use PySide6/QPainter or Matplotlib backend for drawing shapes.

**Test Plan:**  
- Create, resize, move, and delete shapes.  
- Verify undo/redo functionality.  

**Risks & Mitigations:**  
- None significant.

---

### Feature: Path Tool (Pen Tool)
**Backlog Task:** Bezier curve drawing.

**Proposed Implementation:**  
1. **Model:** `PathNode` with list of control points.  
2. **View:** Canvas allows mouse clicks to define points; curves drawn interactively.  
3. **Controller:** ToolManager handles point creation, curve editing, moving points.  
4. **Renderer:** Draw path with QPainter or Matplotlib.

**Test Plan:**  
- Verify creation of curves, editing points, undo/redo functionality.

**Risks & Mitigations:**  
- Complex curves may require snapping or smoothing later.

---

### Feature: Advanced Text Tool
**Backlog Task:** On-canvas text editing, rich text, LaTeX support.

**Proposed Implementation:**  
1. **Model:** `TextNode` with properties `content`, `font`, `style`, `latex_enabled`.  
2. **View:** Editable canvas text; rich text toolbar; LaTeX rendering via Matplotlib/MathTex.  
3. **Controller:** ToolManager handles text creation and editing.  
4. **Renderer:** Render text using Qt text or Matplotlib `Text` objects.

**Test Plan:**  
- Edit, move, resize text.  
- Verify LaTeX formulas render correctly.  

**Risks & Mitigations:**  
- Large LaTeX expressions may affect performance; provide optional rendering optimization.

---

### Feature: Image Import (Drag & Drop)
**Backlog Task:** Allow drag-and-drop of PNG/JPG into subplot.

**Proposed Implementation:**  
1. **Model:** `ImageNode` containing `np.ndarray` image data.  
2. **View:** Handle drag-and-drop; show placeholder while loading.  
3. **Controller:** Read file via Pillow → NumPy array → assign to `ImageNode`; trigger `ChangePropertyCommand`.  
4. **Renderer:** Draw image in subplot using Matplotlib `imshow`.

**Test Plan:**  
- Load images of various formats/sizes.  
- Verify placement, resizing, undo/redo functionality.  

**Risks & Mitigations:**  
- Large images may require downsampling to maintain UI performance.

---

### Feature: Strokes, Fills, Gradients
**Backlog Task:** Detailed controls for object appearance.

**Proposed Implementation:**  
1. **Model:** Extend `ShapeNode` and `TextNode` with `stroke_color`, `fill_color`, `gradient`.  
2. **View:** Properties inspector widgets for editing.  
3. **Controller:** Trigger `ChangePropertyCommand` on edits.  
4. **Renderer:** Apply styles during node rendering.

**Test Plan:**  
- Verify color and gradient updates are correctly applied.  
- Test undo/redo functionality.

**Risks & Mitigations:**  
- Gradients may affect rendering performance; optimize drawing pipeline.

---

### Feature: Reusable Styles/Templates
**Backlog Task:** Save named styles for reuse.

**Proposed Implementation:**  
1. **Model:** `StyleTemplate` registry storing style properties.  
2. **View:** Dropdown in properties panel for applying styles.  
3. **Controller:** Apply style via command to selected nodes.

**Test Plan:**  
- Create, apply, delete style templates.  
- Verify undo/redo works.  

**Risks & Mitigations:**  
- Conflicts with existing node styles; ensure proper merge logic.

---

## Epic: Data Management & Interaction

### Feature: Interactive Data Worksheet
**Backlog Task:** Dockable panel to view/edit plot data.

**Proposed Implementation:**  
1. **Model:** `DataFrame` stored in `PlotNode`.  
2. **View:** Table widget for editing/sorting; updates reflected in canvas plot.  
3. **Controller:** Connect edits to `ChangeDataCommand`.

**Test Plan:**  
- Modify data in table; verify canvas updates.  
- Test undo/redo functionality.

**Risks & Mitigations:**  
- Large datasets may require virtualized table to maintain performance.

---

### Feature: Curve Fitting Panel
**Backlog Task:** Advanced curve fitting with built-in and user-defined functions.

**Proposed Implementation:**  
1. **Model:** Fit parameters stored in `PlotNode`.  
2. **View:** Dockable panel for selecting parameters/functions.  
3. **Controller:** Compute fit via SciPy/NumPy; update plot on changes.

**Test Plan:**  
- Fit sample datasets; verify results.  
- Test undo/redo functionality.  

**Risks & Mitigations:**  
- Non-convergent fits → handle errors gracefully.

---

## Epic: Export & Configuration

### Feature: Export Engine
**Backlog Task:** Vector and raster export (SVG, PDF, EPS, PNG, TIFF).

**Proposed Implementation:**  
1. **Renderer:** Use Matplotlib backends for raster/vector output.  
2. **View:** Export dialog with format selection.  
3. **Controller:** Validate export params; trigger render and save.

**Test Plan:**  
- Export plots of various types/sizes; verify quality and content.  

**Risks & Mitigations:**  
- Complex plots may require layout adjustments for vector export.

---

### Feature: Externalize Configurations
**Backlog Task:** Use Pydantic to manage central configuration.

**Proposed Implementation:**  
1. **Model:** `ConfigModel` using Pydantic for validation.  
2. **View:** Optional settings panel for editing.  
3. **Controller:** Changes update live settings or persist to file.

**Test Plan:**  
- Verify defaults, edits, and validation errors.  

**Risks & Mitigations:**  
- Invalid configs should not crash the app → fallback to defaults.

### Refactoring Task: Clean Application Composition

**Task:** Refactor the application startup and component wiring to use a clean composition root, eliminating circular dependencies and `None` initializations for UI components, and reducing the bloat in `setup_application`.

**Background & Context:** The current `setup_application` function in `main.py` has become a "God function," handling too many responsibilities including core component instantiation, builder execution, tool registration, view instantiation, post-instantiation wiring, and signal/slot connections. This leads to a fragile, hard-to-read, and difficult-to-maintain codebase, as evidenced by recent `AttributeError`s and the re-introduction of `None` initializers in `MainWindow`'s constructor. The original intention of decoupling `MainWindow` initialization was compromised by circular dependencies where builders needed a `MainWindow` parent before `MainWindow` itself could be fully constructed with the components built by those builders.

**Proposed Solution:** Implement a robust dependency injection pattern using dedicated builder/assembler classes to delegate construction responsibilities.

1.  **`ApplicationComponents` Dataclass:** Introduce a `dataclass` to provide a clear, type-hinted structure for the application's core components returned by the composition root.
2.  **Refactored `MenuBarBuilder`:** Modify `MenuBarBuilder` to *create and return* a `QMenuBar` and `MainMenuActions` without requiring a `QMainWindow` parent during its `build()` method. The responsibility of attaching the `QMenuBar` to the `MainWindow` will be handled by the composition root.
3.  **Refactored `ToolBarBuilder`:** Modify `ToolBarBuilder` to *create and return* a `QToolBar` and `ToolBarActions` without requiring a `QMainWindow` parent during its `build()` method. The responsibility of attaching the `QToolBar` to the `MainWindow` will be handled by the composition root.
4.  **Clean `MainWindow` Constructor:** The `MainWindow` constructor will be refactored to accept all its UI dependencies (`QMenuBar`, `MainMenuActions`, `QToolBar`, `ToolBarActions`, etc.) directly as arguments. This ensures `MainWindow` is always in a fully valid and initialized state after construction, eliminating the need for `None` initializations and post-construction setup methods.
5.  **`ApplicationAssembler` Class:** Introduce a new class, `ApplicationAssembler`, that will serve as the primary composition root. Its `assemble()` method will orchestrate the entire application setup process, delegating to other builders and creating all components in the correct order.
6.  **Simplified `main.py`:** The `setup_application` function in `main.py` will be significantly simplified, primarily responsible for instantiating the `ApplicationAssembler` and calling its `assemble()` method, then returning the `ApplicationComponents`.

**Implementation Plan (Detailed Steps):**

1.  **Create `src/application_components.py`:**
    *   Define the `ApplicationComponents` dataclass, listing all core application components.

2.  **Refactor `src/builders/menu_bar_builder.py`:**
    *   Change `__init__(self, parent_window: QMainWindow, main_controller: MainController, command_manager: CommandManager)` to `__init__(self, main_controller: MainController, command_manager: CommandManager)`.
    *   Modify `build() -> Tuple[QMenuBar, MainMenuActions]`:
        *   Create `menu_bar = QMenuBar()` (instead of `self._parent_window.menuBar()`).
        *   Remove any calls to `self._parent_window.setMenuBar()`. The `menu_bar` object is returned, and attachment is external.
        *   Ensure all `QAction`s are correctly parented to `menu_bar` or its sub-menus (or `None` if `QAction`s can exist without a parent until added to a menu, which is usually fine).

3.  **Refactor `src/builders/tool_bar_builder.py`:**
    *   Change `__init__(self, parent_window: QMainWindow, tool_manager: ToolManager)` to `__init__(self, tool_manager: ToolManager)`.
    *   Modify `build() -> Tuple[QToolBar, ToolBarActions]`:
        *   Create `tool_bar = QToolBar("Tools")` (instead of `QToolBar("Tools", self._parent_window)`).
        *   Remove any calls to `self._parent_window.addToolBar()`. The `tool_bar` object is returned, and attachment is external.
        *   Ensure all `QAction`s are correctly parented to `tool_bar` (or `None` if they can exist without a parent until added).

4.  **Refactor `src/views/main_window.py`:**
    *   Modify `__init__` signature to accept `menu_bar: QMenuBar`, `main_menu_actions: MainMenuActions`, `tool_bar: QToolBar`, `tool_bar_actions: ToolBarActions` (and other core components) as arguments.
    *   Remove `setup_menu_bar` and `setup_tool_bar` methods.
    *   Inside `__init__`, directly set `self.setMenuBar(menu_bar)` and `self.addToolBar(tool_bar)`.
    *   Remove all `| None` optional type hints and `None` initializations related to these UI components. All UI-related attributes will be assigned directly from constructor arguments.

5.  **Create `src/application_assembler.py`:**
    *   Define the `ApplicationAssembler` class.
    *   It will have an `__init__` that takes the `QApplication` instance.
    *   It will have private methods (`_assemble_core_components`, `_assemble_menus`, `_assemble_tooling`, `_assemble_main_window`, `_assemble_canvas_controller`, `_connect_signals`) to encapsulate specific parts of the assembly process.
    *   The public `assemble() -> ApplicationComponents` method will orchestrate these private methods in the correct order. This ensures the `canvas_widget` is available for tools when they are created, and `MainWindow` receives fully built components.

6.  **Modify `main.py`:**
    *   Import `ApplicationAssembler` and `ApplicationComponents`.
    *   Simplify `setup_application` to:
        *   Get `QApplication` instance.
        *   Instantiate `ApplicationAssembler(app)`.
        *   Call `assembler.assemble()` and return its result.
    *   Ensure the `main()` function correctly uses the `ApplicationComponents` dataclass.

### Refactoring Task: Clean Application Composition

**Task:** Refactor the application startup and component wiring to use a clean composition root, eliminating circular dependencies and `None` initializations for UI components, and reducing the bloat in `setup_application`.

**Background & Context:** The current `setup_application` function in `main.py` has become a "God function," handling too many responsibilities including core component instantiation, builder execution, tool registration, view instantiation, post-instantiation wiring, and signal/slot connections. This leads to a fragile, hard-to-read, and difficult-to-maintain codebase, as evidenced by recent `AttributeError`s and the re-introduction of `None` initializations in `MainWindow`'s constructor. The original intention of decoupling `MainWindow` initialization was compromised by circular dependencies where builders needed a `MainWindow` parent before `MainWindow` itself could be fully constructed with the components built by those builders.

**Proposed Solution:** Implement a robust dependency injection pattern using dedicated builder/assembler classes to delegate construction responsibilities.

1.  **`ApplicationComponents` Dataclass:** Introduce a `dataclass` to provide a clear, type-hinted structure for the application's core components returned by the composition root.
2.  **Refactored `MenuBarBuilder`:** Modify `MenuBarBuilder` to *create and return* a `QMenuBar` and `MainMenuActions` without requiring a `QMainWindow` parent during its `build()` method. The responsibility of attaching the `QMenuBar` to the `MainWindow` will be handled by the composition root.
3.  **Refactored `ToolBarBuilder`:** Modify `ToolBarBuilder` to *create and return* a `QToolBar` and `ToolBarActions` without requiring a `QMainWindow` parent during its `build()` method. The responsibility of attaching the `QToolBar` to the `MainWindow` will be handled by the composition root.
4.  **Clean `MainWindow` Constructor:** The `MainWindow` constructor will be refactored to accept all its UI dependencies (`QMenuBar`, `MainMenuActions`, `QToolBar`, `ToolBarActions`, etc.) directly as arguments. This ensures `MainWindow` is always in a fully valid and initialized state after construction, eliminating the need for `None` initializations and post-construction setup methods.
5.  **`ApplicationAssembler` Class:** Introduce a new class, `ApplicationAssembler`, that will serve as the primary composition root. Its `assemble()` method will orchestrate the entire application setup process, delegating to other builders and creating all components in the correct order.
6.  **Simplified `main.py`:** The `setup_application` function in `main.py` will be significantly simplified, primarily responsible for instantiating the `ApplicationAssembler` and calling its `assemble()` method, then returning the `ApplicationComponents`.

**Test Plan:**
*   **Unit Tests for Builders:**
    *   `test_menu_bar_builder.py`: Update tests to verify `build()` returns `QMenuBar` and `MainMenuActions` correctly, and doesn't rely on an external parent.
    *   `test_tool_bar_builder.py` (new or existing): Create/update tests to verify `build()` returns `QToolBar` and `ToolBarActions` correctly, and doesn't rely on an external parent.
*   **Integration Tests for `ApplicationAssembler`:**
    *   Create `tests/test_application_assembler.py` to verify that `assemble()` correctly builds and connects all major application components.
*   **Existing Integration Tests:** Run all existing integration tests (especially `test_user_workflows.py` and `test_main_window.py`) to ensure no regressions are introduced by the structural changes.

**Risks & Mitigations:**
*   **Risk:** Extensive refactoring across multiple core files (`main.py`, `MainWindow`, `MenuBarBuilder`, `ToolBarBuilder`, new `ApplicationAssembler`) might introduce new bugs or break existing functionality.
*   **Mitigation:** Proceed in small, atomic steps, running tests after each significant change. Focus on modifying one builder or class at a time. The detailed implementation plan helps ensure a systematic approach. Thorough unit tests for the builders and `ApplicationAssembler` will be crucial.
*   **Risk:** Potential for temporary breaking changes during the refactoring process.
*   **Mitigation:** Use feature branches for this refactoring. Ensure robust CI/CD if available.

---

## Epic: UI Extensibility

### Refactoring Task: Formalize Properties UI Factory with Registration Pattern

**Background & Context:** The `PropertiesUIFactory.create_ui` static method currently uses `isinstance` checks to conditionally render UI elements based on the `PlotProperties` type. This approach violates the Open/Closed Principle, making it difficult to extend the UI for new plot types without modifying the factory itself.

**Proposed Solution:** Refactor `PropertiesUIFactory` to use a registration pattern. It will become an instance-based class that maintains a mapping of `PlotType` to builder functions. The `ApplicationAssembler` will be responsible for registering these builder functions during application startup.

**Implementation Plan (Detailed Steps):**

1.  **Refactor `src/views/properties_ui_factory.py`:**
    *   Change `PropertiesUIFactory` from a static class to an instance-based class.
    *   Add `__init__(self)` method to initialize `self._builders = {}`.
    *   Implement `register_builder(self, plot_type: PlotType, builder_func: Callable)` to store builder functions in `self._builders`.
    *   Modify `create_ui` (rename to `build_widgets` for clarity and consistency) to accept `self` and use `self._builders.get(props.plot_type)` to retrieve and call the appropriate builder function. The builder function will receive all necessary UI parameters (layout, parent, callbacks, etc.).
    *   Extract the common UI building logic (plot type combo, title, labels, column selectors, limit selectors) into a default builder function or helper methods that can be composed by specific plot type builders.
    *   Ensure the existing static methods like `_build_column_selectors` and `_build_limit_selectors` are adapted or moved as appropriate.

2.  **Create Plot-Specific UI Builder Functions:**
    *   For each `PlotType` (e.g., `PlotType.LINE`, `PlotType.SCATTER`), create a dedicated function (e.g., `build_line_plot_ui`, `build_scatter_plot_ui`) that encapsulates the logic for building the specific UI elements for that plot type. These functions will take the same arguments as `build_widgets` (or a subset) and be responsible for adding rows to the `QFormLayout`.

3.  **Update `src/application_assembler.py`:**
    *   Instantiate `PropertiesUIFactory` within `ApplicationAssembler`.
    *   In a new or existing assembly method (e.g., `_assemble_ui_factories` or within `_assemble_main_window`), register the plot-specific UI builder functions with the `PropertiesUIFactory` instance.

4.  **Update `src/views/main_window.py` (and related calls):**
    *   Modify the `MainWindow`'s constructor or setup method to accept the `PropertiesUIFactory` instance.
    *   Ensure that wherever `PropertiesUIFactory.create_ui` was previously called, it now calls `factory_instance.build_widgets`.

**Test Plan:**
*   **Unit Tests for `PropertiesUIFactory` (new or updated `test_properties_ui_factory_refactor.py`):**
    *   Verify factory instantiation (`__init__`).
    *   Test `register_builder`: Ensure builder functions are correctly stored for specific `PlotType`s.
    *   Test `build_widgets` with registered builders: Mock `PlotNode`, `PlotProperties`, and UI components; assert that the correct registered builder function is called with the expected arguments.
    *   Test `build_widgets` with unregistered builders: Ensure graceful handling (e.g., no error, no UI elements added) when a `PlotType` has no registered builder.
    *   Test plot-specific builder functions directly to ensure they create the correct widgets.
*   **Integration Tests for `ApplicationAssembler` (update `tests/test_application_assembler.py`):**
    *   Verify that `ApplicationAssembler` correctly instantiates `PropertiesUIFactory` and registers all expected plot type builders.
*   **End-to-End Tests (`tests/workflows/test_user_workflows.py`):
    *   Run existing user workflow tests to ensure that the properties panel still functions correctly for all existing plot types after the refactoring.

**Risks & Mitigations:**
*   **Risk:** Breaking existing UI generation logic due to the significant structural change from a static method to an instance with registration.
*   **Mitigation:** Develop the refactored factory and its tests in parallel. Use the new test file (`test_properties_ui_factory_refactor.py`) to confirm the new logic before integrating it into the main application flow. Ensure comprehensive mocking for unit tests.
*   **Risk:** The arguments to `create_ui` (now `build_widgets`) are numerous and tightly coupled with specific UI elements and callbacks. Passing these through builder functions could be cumbersome.
*   **Mitigation:** The builder functions will receive these arguments. If common arguments are always needed, they can be passed directly. If some are only needed for specific plot types, they might be passed as `**kwargs` or the builder signature can be specialized. The use of `partial` for callbacks is already present and should continue to work effectively. Consider if some arguments could be encapsulated within a `BuildContext` object to simplify signatures.
