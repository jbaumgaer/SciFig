# Technical Design Document (TDD)

This document is intended to provide detailed, technical implementation plans for specific new features or refactoring tasks. It serves as a blueprint for the developer (human or AI) executing the task.

A TDD should be created as part of the **"Reason & Plan"** phase for any sufficiently complex task.

---

## Epic: UI Refactoring

### Feature: MainWindow Construction Refactoring
**Task:** Refactor the construction of the `MainWindow` to improve type safety, readability, and maintainability. This involves eliminating the monolithic `MainWindowBuilder` and making the `MainWindow` responsible for its own construction.

**Background & Context:** The current approach has several drawbacks:
- **`MainWindowBuilder` is a monolith:** It is responsible for creating every part of the main window, making it long and difficult to maintain.
- **Delayed Initialization:** The `MainWindow` is initialized with all its UI components set to `None`. The builder then populates these attributes.
- **Reduced Type Safety:** Because of the `None` initialization, all component attributes must be typed as `Optional` (e.g., `QWidget | None`). This requires constant `None` checks throughout the code and increases the risk of `NoneType` runtime errors, even though the components should be fully available after the initial setup.

**Proposed Implementation:**
The core principle of this refactoring is to make the `MainWindow` responsible for its own construction, following the principle of high cohesion.

1.  **Eliminate `MainWindowBuilder`:** The `src/builders/main_window_builder.py` file will be deleted. Its responsibilities will be moved into the `MainWindow` and a new `MenuBarBuilder`.

2.  **Refactor `MainWindow`:**
    *   The `__init__` method will be updated to accept the `ApplicationModel`, `CommandManager`, and `plot_types` as direct dependencies.
    *   The long list of `None`-initialized attributes will be removed.
    *   The `__init__` method will call a series of private factory methods to construct its own UI components (e.g., `_create_canvas`, `_create_properties_dock`).
    *   Attributes will be assigned directly from the return values of these factory methods, ensuring they are never `None` after initialization.

3.  **Introduce `MenuBarBuilder`:**
    *   A new file, `src/builders/menu_bar_builder.py`, will be created.
    *   It will contain a new `MenuBarBuilder` class and a `MainMenuActions` dataclass.
    *   The `MainMenuActions` dataclass will act as a container for all the menu components (`QMenuBar`, `QMenu`, `QAction`).
    *   The `MenuBarBuilder` will take the parent `MainWindow` and `CommandManager` as dependencies. It will contain the logic for building the file and edit menus.
    *   Its public `build()` method will return a fully populated `MainMenuActions` instance.

4.  **Update Application Entry Point:** The `main.py` file will be modified to instantiate `MainWindow` directly, instead of using the `MainWindowBuilder`.

**Test Plan:**
-   All existing UI-related tests in `tests/views/` and `tests/workflows/` must continue to pass after the refactoring.
-   A new unit test will be created for the `MenuBarBuilder` to verify that it correctly creates all menus and actions.

**Risks & Mitigations:**
-   **Risk:** This is a significant refactoring that touches the core of the UI initialization. It could lead to a non-functional UI if not done carefully.
-   **Mitigation:** The refactoring will be done incrementally. The application will be run after each major step to ensure the UI is still functional. The existing test suite will be crucial for catching regressions.

---

## Epic: Architectural Refinement





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

### Feature: Project Files & Templates
**Backlog Task:** Save/load workspace and layouts.

**Proposed Implementation:**  
1. **Model:** Serialize `ApplicationModel` and scene graph to JSON.  
2. **View:** Dialog for file selection.  
3. **Controller:** Load/save triggers update commands.

**Test Plan:**  
- Save/load multiple projects; verify scene graph and data consistency.

**Risks & Mitigations:**  
- Versioning issues → include project format version.

---

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
