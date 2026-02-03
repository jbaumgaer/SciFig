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

## Epic: Project File Management

### Feature: Project File Management (`.sci` files)
**Task:** Implement a complete workflow for saving, loading, and accessing recent projects using a custom `.sci` file format.

**Background & Context:** A robust file management system is critical for a good user experience. The chosen format must handle a complex scene graph, various metadata, and potentially large datasets efficiently and safely. A single-file format is strongly preferred.

**Architectural Decisions:**
*   **Hybrid Archive Format (`.sci`):** The `.sci` file will be a zip archive containing a `project.json` for metadata and a `data/` directory for high-performance data serialization. This provides the readability of JSON for the project structure and the performance/efficiency of Parquet for the data, while avoiding the security risks of formats like `pickle`.
*   **Deserialization Strategy (Factory Pattern):** A factory function will be used to reconstruct nodes from the `project.json`. This function will read a `class_name` key from each node's dictionary and instantiate the corresponding Python class (e.g., `PlotNode`, `GroupNode`), making the process extensible.
*   **Recent Files Persistence (`QSettings`):** The `QSettings` class will be used to store a persistent, platform-agnostic list of recently opened files, providing a much more robust solution than a manual text or JSON file.

**`.sci` File Structure:**
```
my_project.sci (zip archive)
├── project.json
└── data/
    ├── {node_id_1}.parquet
    ├── {node_id_2}.parquet
    └── ...
```

**Implementation - Save Workflow:**
1.  **Controller (`save_project`):** Opens a `QFileDialog`, creates a temporary directory to stage files, iterates through the model's nodes to save data, creates `project.json` from the model's dictionary, zips the temp directory into the final `.sci` file, and cleans up.
2.  **Model (`to_dict`):** Nodes serialize their metadata. `PlotNode`s reference their data via a `data_path` (e.g., `data/node_id.parquet`) instead of embedding the data itself.

**Implementation - Open Workflow:**
1.  **Controller (`open_project`):** Opens a `QFileDialog` to select a `.sci` file. Unzips the file to a temporary directory, reads the `project.json`, and passes the resulting dictionary to the model for reconstruction. It will also handle adding the path to the recent files list.
2.  **Model (`load_from_dict`):** A new method in `ApplicationModel` will clear the current scene and then use a factory to recursively reconstruct the entire scene graph from the dictionary.
3.  **Node Deserialization (`from_dict`):** Each `SceneNode` subclass will have a `from_dict` class method. `PlotNode.from_dict` will be responsible for reading the `data_path` key and loading the corresponding Parquet file from the temporary directory into its `.data` attribute.

**Implementation - Open Recent Workflow:**
1.  **`QSettings` Management:** On successful save or open, the file path will be added to the top of a list stored in `QSettings`. The list will be capped at a reasonable number (e.g., 10).
2.  **Dynamic Menu:** The `MenuBarBuilder` will connect to the `aboutToShow` signal of the "Open Recent Projects" menu. The connected slot will clear the menu and repopulate it with `QAction`s for each path stored in `QSettings`. Clicking an action will call `open_project` with the corresponding path.

**Test Plan:**
- Unit tests for `to_dict` and `from_dict` methods on all node classes.
- Integration test for the full save workflow.
- Integration test for the full open workflow (save a file, then open it and assert the model state is identical).
- Integration test for the "Open Recent" menu logic, using a mocked `QSettings`.

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

---

## Refactoring Task: Decouple Controller-View Initialization

**Task:** Refactor the application startup sequence in `main.py` to remove the circular dependency between `MainController` and `MainWindow`.

**Background & Context:** The current implementation in `setup_application` creates an awkward "chicken-and-egg" problem.
1. `MainController` is created with `view=None`.
2. `MainWindow` is created and requires the `MainController` instance.
3. The `MainWindow` instance is then assigned back to `main_controller.view`.
4. `main_controller.setup_connections()` is called to finalize the wiring.

This multi-step initialization is confusing, error-prone, and makes the components tightly coupled during instantiation. The goal is to refactor this into a linear, unidirectional setup process.

**Proposed Solution: Centralized Connection**
The `setup_application` function will act as the "composition root," exclusively responsible for creating and wiring components together. The `MainController` will no longer be responsible for connecting itself to the view's signals.

**Implementation Plan:**

1.  **Modify `src/controllers/main_controller.py`:**
    *   **`__init__`:** Remove the `view` parameter. The controller will no longer store a reference to the main window.
    *   **Remove `setup_connections`:** This method's logic will be moved into `setup_application`.
    *   **Update `save_project` and `open_project`:** These methods require a parent widget for `QFileDialog`. Modify their signatures to accept a `parent: QWidget | None = None` argument. The call inside will be `QFileDialog.getSaveFileName(parent, ...)` and `QFileDialog.getOpenFileName(parent, ...)`.

2.  **Modify `src/views/main_window.py`:**
    *   No significant changes are needed here. The `__init__` method will still receive the `main_controller` instance and pass it to the `MenuBarBuilder`. This is acceptable because the builder only connects `QAction` signals to the controller's methods, which (after the refactoring) will no longer depend on a `view` attribute being present on the controller.

3.  **Modify `main.py` (the `setup_application` function):**
    *   **Instantiation:**
        *   Create `model`.
        *   Create `main_controller = MainController(model=model)`.
        *   Create `view = MainWindow(...)`, passing the `main_controller` as before.
    *   **Centralized Wiring:** After the `view` is created, add the following logic to explicitly connect the view's signals to the controller's slots:
        ```python
        # Connect main window actions to controller slots
        view.new_layout_action.triggered.connect(main_controller.create_new_layout)
        # Use a lambda to pass the view as the parent for the dialog
        view.save_project_action.triggered.connect(lambda: main_controller.save_project(parent=view))
        view.open_project_action.triggered.connect(lambda: main_controller.open_project(parent=view))
        ```
    *   **Remove Old Code:** Delete the lines that previously assigned `main_controller.view = view` and called `main_controller.setup_connections()`.
    *   **Update Controller Calls:** Ensure any other direct calls to `save/open_project` (e.g., from a future "open recent" menu) also pass the `view` as the parent.

**Test Plan:**
-   After refactoring, manually test the "New Layout", "Save Project", and "Open Project" menu actions to ensure they work as before.
-   Run the existing test suite to confirm that no regressions have been introduced. The `setup_application` function is used by tests, so they will benefit from this cleaner setup.

**Expected Outcome:**
The instantiation of core components will be linear and easier to follow. The `MainController` will be a more independent and reusable component, and the tight coupling at initialization will be broken.