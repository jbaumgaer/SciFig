# Technical Design Document (TDD)

This document is intended to provide detailed, technical implementation plans for specific new features or refactoring tasks. It serves as a blueprint for the developer (human or AI) executing the task.

A TDD should be created as part of the **"Reason & Plan"** phase for any sufficiently complex task.

---

## Epic: Architectural Refinement

### Feature: Pluggable Plot Properties and Dynamic View
**Task:** Refactor `PlotProperties` into a hierarchical, type-specific structure and make the `PropertiesView` dynamically update its UI based on the selected plot type.
**Background & Context:** The current `PlotProperties` is a monolithic dataclass, and the plot type is a simple string. This is not scalable for plot types with different property needs (e.g., a 3D plot needing a Z-axis column, or a scatter plot needing a `marker_size` property). To support true pluggability, the properties model and the view that edits it must both be made more dynamic.

**Phase 1: Model Refactoring**
1.  **Create `PlotType` Enum:**
    *   In a new file, `src/models/plot_types.py`, define a `PlotType` enum using `enum.Enum`.
    *   `class PlotType(str, Enum): LINE = "line"; SCATTER = "scatter"` (inheriting from `str` helps with serialization if needed).
2.  **Refactor `PlotProperties` Hierarchy:**
    *   In `src/models/nodes/plot_properties.py`:
        *   Rename the existing `PlotProperties` dataclass to `BasePlotProperties`.
        *   Change its `plot_type` attribute from `str` to `PlotType`.
        *   Create new dataclasses `LinePlotProperties` and `ScatterPlotProperties`, both inheriting from `BasePlotProperties`.
        *   For now, these subclasses will be simple `pass` statements, but this establishes the required structure. For example, `ScatterPlotProperties` could later have `marker_size: int = 10`.
3.  **Update Core Model and Renderer:**
    *   In `PlotNode`, change the type hint for `plot_properties` to `Optional[BasePlotProperties]`.
    *   In the `Renderer`, change the keys of the `plotting_strategies` dictionary from strings to `PlotType` enum members (e.g., `{PlotType.LINE: LinePlotStrategy(), ...}`).
    *   In `PropertiesView`, update its `__init__` to accept `list[PlotType]` and modify the `QComboBox` to be populated from this list. The `_on_plot_type_changed` signal will now emit a `PlotType` member.

**Phase 2: Dynamic View Implementation**
1.  **Create `PropertiesUIFactory`:**
    *   Create a new class `PropertiesUIFactory` in `src/views/properties_ui_factory.py`.
    *   This class will be responsible for building the specific QWidgets needed for a given `BasePlotProperties` instance.
    *   It will have a central method, e.g., `build_widgets(props: BasePlotProperties, layout: QFormLayout, command_manager: CommandManager)`.
    *   Inside `build_widgets`, it will use `isinstance` checks to determine which specific builder method to call (e.g., `if isinstance(props, ScatterPlotProperties): self._build_scatter_widgets(...)`).
    *   The specific builder methods (`_build_scatter_widgets`) will create the `QSpinBox` for `marker_size`, connect its `valueChanged` signal to a `ChangePropertyCommand`, etc.
2.  **Refactor `PropertiesView`:**
    *   In `PropertiesView.__init__`, create an instance of the `PropertiesUIFactory`.
    *   In `_build_plotnode_ui`, after creating the common widgets (Title, Labels, Plot Type dropdown), it will call `self.ui_factory.build_widgets(props, form_layout, self.command_manager)`. This delegates the creation of type-specific widgets to the factory, keeping the main view clean.

**Test Plan:**
-   Update existing tests that fail due to the `PlotProperties` and `PlotType` refactoring.
-   Write a unit test for the `PropertiesUIFactory` to ensure it calls the correct builder method for each property type.
-   Write an integration test to verify that when the user changes the `plot_type` in the `PropertiesView` dropdown, the old type-specific widgets are removed and the new ones are created correctly. For example, changing from "scatter" to "line" should make the `marker_size` editor disappear.

**Risks & Mitigations:**
-   **Risk:** The refactoring is significant and will touch many files, potentially breaking existing functionality.
-   **Mitigation:** The work is broken into two phases. After Phase 1, the application should still be fully functional before proceeding to Phase 2. The comprehensive test suite will be relied upon to catch regressions.

---

### Feature: Pluggable Node Renderer Strategy
**Task:** Refactor the main rendering loop to use a Strategy Pattern for rendering different `SceneNode` types.  
**Background & Context:** The main `_render_node` recursive method uses a large `if isinstance(node, PlotNode):` block. As more node types are added (`RectangleNode`, `TextNode`, etc.), this will become a long and difficult-to-maintain `if/elif/else` chain, violating the Open/Closed Principle.

**Proposed Implementation:**  
1.  **Isolate Node Rendering Logic:**
    *   Move the existing logic for rendering a `PlotNode` from `_render_node` into its own dedicated method within the `Renderer` class: `_render_plot_node(self, figure, node)`.
    *   Create placeholder methods for future node types, e.g., `_render_rectangle_node(self, figure, node)`.
2.  **Create the Strategy Map:**
    *   In the `Renderer.__init__`, create a `_render_strategies` dictionary that maps the *class type* of a node to the appropriate rendering function.
        ```python
        from src.models.nodes import PlotNode, RectangleNode # etc.

        self._render_strategies = {
            PlotNode: self._render_plot_node,
            # RectangleNode: self._render_rectangle_node, # To be added later
        }
        ```
3.  **Refactor the Main Render Loop:**
    *   Simplify the `_render_node` method dramatically. Its only job now is to find the correct strategy and call it.
        ```python
        def _render_node(self, figure, node):
            if not node.visible:
                return

            # Find and execute the strategy for the current node
            render_func = self._render_strategies.get(type(node))
            if render_func:
                render_func(figure, node)
            else:
                # Optionally log a warning for unhandled node types
                print(f"Warning: No renderer found for node type {type(node)}")

            # Recursively render children
            for child in node.children:
                self._render_node(figure, child)
        ```

**Test Plan:**  
-   Verify that `PlotNode` objects continue to render exactly as they did before the refactor.
-   Create a new, simple `TestNode` class and a corresponding `_render_test_node` function. Write a test to add a `TestNode` to the scene, add its renderer to the strategy map, and confirm that the correct rendering function is called.
-   Test that the recursive rendering of children is unaffected.

**Risks & Mitigations:**  
-   **Risk:** A new node type is created, but a developer forgets to add it to the strategy map.
-   **Mitigation:** The implementation includes a warning for unhandled node types. This can be elevated to an error during debug builds if necessary. A unit test can also be written to check that all non-abstract `SceneNode` subclasses exist as keys in the strategy map.

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
