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
---

## Epic: Tool System

### Refactoring Task: Enhance Tool Management Architecture

**Task:** Refactor the core tool management and event dispatching mechanism to support a pluggable and extensible tool system.

**Background & Context:** The current `CanvasController` directly handles canvas events, which will lead to unmaintainable `if/elif/else` chains as more interactive tools are introduced. The `ToolManager` is currently a basic container. To support a rich toolbar and interactive tools, a more robust, decoupled architecture is required.

**Proposed Solution:** Implement a Strategy-like pattern where the `ToolManager` acts as the context, and individual tools are strategies that handle specific user interactions. The UI will trigger state changes in the `ToolManager`, and the UI will react to signals from the `ToolManager`.

**Implementation Plan:**

1.  **Create `src/controllers/tools/base_tool.py`:**
    *   Define an abstract base class `BaseTool` (inheriting from `ABC` from `abc` module and `QObject` from `PySide6.QtCore`).
    *   It will have an `__init__` method accepting `model: ApplicationModel`, `command_manager: CommandManager`, and `canvas_widget: CanvasWidget`.
    *   Define abstract methods that all tools must implement. These include:
        *   `name(self) -> str` (property: unique name of the tool, e.g., "selection")
        *   `icon_path(self) -> str` (property: path to the tool's icon)
        *   `on_activated(self)`: Called when the tool becomes active.
        *   `on_deactivated(self)`: Called when the tool becomes inactive.
        *   `mouse_press_event(self, event: QMouseEvent)`
        *   `mouse_move_event(self, event: QMouseEvent)`
        *   `mouse_release_event(self, event: QMouseEvent)`
        *   `key_press_event(self, event: QKeyEvent)` (Optional, with a default no-op implementation)
        *   `paint_event(self, painter: QPainter)` (Optional, for tools that need to draw temporary overlays on the canvas)

2.  **Refactor `src/controllers/tool_manager.py`:**
    *   Add a `_tools: Dict[str, BaseTool]` attribute to store registered tools.
    *   Add a `_active_tool_name: str | None` attribute to track the currently active tool.
    *   Add a `activeToolChanged = Signal(str)` to emit when the active tool changes.
    *   Modify `add_tool(self, name: str, tool: BaseTool)` to store the tool.
    *   Modify `set_active_tool(self, tool_name: str)`:
        *   If an old tool was active, call `old_tool.on_deactivated()`.
        *   Set the new active tool.
        *   Call `new_tool.on_activated()`.
        *   Emit `self.activeToolChanged.emit(tool_name)`.
    *   Add methods to dispatch canvas events to the active tool:
        *   `dispatch_mouse_press_event(self, event: QMouseEvent)` -> `self.active_tool.mouse_press_event(event)`
        *   `dispatch_mouse_move_event(self, event: QMouseEvent)` -> `self.active_tool.mouse_move_event(event)`
        *   `dispatch_mouse_release_event(self, event: QMouseEvent)` -> `self.active_tool.mouse_release_event(event)`
        *   `dispatch_key_press_event(self, event: QKeyEvent)` -> `self.active_tool.key_press_event(event)`

3.  **Refactor `src/controllers/canvas_controller.py`:** EDIT: This is where we left off last time
    *   Remove all event handling logic (mouse presses, moves, releases) from `CanvasController` itself.
    *   Its `__init__` will now take `tool_manager: ToolManager` as an argument.
    *   Connect the `canvas_widget`'s event signals directly to the `tool_manager`'s dispatch methods (e.g., `canvas_widget.mousePress.connect(tool_manager.dispatch_mouse_press_event)`).
    *   The `CanvasController` effectively becomes a pure event *forwarder* to the `ToolManager`.

4.  **Refactor `src/controllers/tools/selection_tool.py`:**
    *   Make `SelectionTool` inherit from `BaseTool`.
    *   Implement all abstract methods defined in `BaseTool`.
    *   Move its current event handling logic into the corresponding `BaseTool` methods.
    *   Ensure `SelectionTool.name` property returns "selection".

**Test Plan:**
-   Unit tests for `BaseTool` (ensure abstract methods are enforced).
-   Unit tests for `ToolManager`:
    *   `add_tool` correctly registers tools.
    *   `set_active_tool` correctly activates/deactivates tools and emits `activeToolChanged` signal.
    *   Event dispatch methods correctly call the active tool's methods.
-   Unit tests for `CanvasController`: Ensure it correctly forwards events to `ToolManager`.
-   Unit tests for `SelectionTool`: Ensure it correctly implements `BaseTool` and its existing logic still functions.
-   Integration tests: Verify that activating a tool in `ToolManager` changes the application's behavior on the canvas as expected.

**Risks & Mitigations:**
-   **Risk:** Extensive changes to core event handling might introduce regressions.
-   **Mitigation:** A phased refactoring approach will be used, starting with `BaseTool`, then `ToolManager`, then `CanvasController`, and finally existing tools. Comprehensive unit and integration tests will be crucial at each step.
-   **Risk:** The `paint_event` method for `BaseTool` might be complex for overlay drawing.
-   **Mitigation:** Start with a simple implementation, providing the `QPainter` directly. Refine as needed for complex overlays or integrate with a dedicated overlay manager later.

---

### Feature: Interactive Toolbar

**Task:** Implement the main application toolbar, populated with placeholder icons for all planned tools, integrated with the new tool management architecture.

**Background & Context:** The application needs a dedicated toolbar for quick access to various interactive tools. This toolbar should visually reflect the currently active tool.

**Proposed Implementation:** Create a `ToolBarBuilder` class, similar to `MenuBarBuilder`, to construct and populate the toolbar. The toolbar will be integrated into the `MainWindow` and will respond to `ToolManager` signals to update its visual state.

**Implementation Plan:**

1.  **Create Placeholder Icons:**
    *   Create a new directory: `src/assets/icons`.
    *   Programmatically generate simple SVG icons for each tool:
        *   `selection_tool.svg` (e.g., an arrow)
        *   `direct_selection_tool.svg` (e.g., white arrow)
        *   `shape_tool.svg` (e.g., a square)
        *   `path_tool.svg` (e.g., pen nib)
        *   `text_tool.svg` (e.g., "T")
        *   `eyedropper_tool.svg` (e.g., eyedropper)
        *   `plot_tool.svg` (e.g., simple line graph)
        *   `zoom_tool.svg` (e.g., magnifying glass)
        *   `rotate_tool.svg` (e.g., circular arrow)
        *   `figure_tool.svg` (e.g., small window icon)

2.  **Create `src/builders/tool_bar_builder.py`:**
    *   Define a `ToolBarBuilder` class.
    *   `__init__(self, parent_window: QMainWindow, tool_manager: ToolManager)`
    *   Define a `ToolBarActions` dataclass to hold references to the created `QAction`s.
    *   `build(self) -> Tuple[QToolBar, ToolBarActions]`:
        *   Create `tool_bar = QToolBar("Tools", self._parent_window)`.
        *   Set `tool_bar.setMovable(False)`, `tool_bar.setFloatable(False)`.
        *   Add `tool_bar` to `parent_window` using `self._parent_window.addToolBar(Qt.LeftToolBarArea, tool_bar)`.
        *   For each tool, create a `QAction`:
            *   Load the SVG icon (`QIcon(tool_icon_path)`).
            *   Set a tooltip (`action.setToolTip("Selection Tool")`).
            *   Set the action to be checkable (`action.setCheckable(True)`).
            *   Connect `action.triggered.connect(lambda checked, tool_name=tool_name: self._tool_manager.set_active_tool(tool_name))`.
            *   Add the action to the toolbar.
        *   Connect `self._tool_manager.activeToolChanged.connect(self._update_tool_bar_state)`.
        *   Return the `QToolBar` and the `ToolBarActions` dataclass.
    *   `_update_tool_bar_state(self, active_tool_name: str)`:
        *   Iterate through all tool actions in `ToolBarActions`.
        *   Set `action.setChecked(action.tool_name == active_tool_name)`.

3.  **Integrate with `main.py` (`setup_application` function):**
    *   Instantiate `ToolManager`.
    *   Instantiate `ToolBarBuilder`, passing it the `MainWindow` and `ToolManager`.
    *   Call `tool_bar_builder.build()` and store the returned toolbar and actions.
    *   Register all tools (e.g., `tool_manager.add_tool("selection", SelectionTool(...))`) after `MainWindow` is created, as the tools will need the `canvas_widget`.
    *   Ensure the `ToolManager` is passed to the `CanvasController` and any other components that need it.

4.  **Integrate with `src/views/main_window.py`:**
    *   Import `ToolBarBuilder`.
    *   Store the created `QToolBar` and `ToolBarActions` as attributes (e.g., `self.tool_bar`, `self.tool_actions`).
    *   **Crucially:** `MainWindow` itself should not instantiate the `ToolBarBuilder` directly but receive the built `QToolBar` and `ToolBarActions` from `setup_application` (similar to how `MenuBarBuilder` is handled in `MainWindow`).

**Test Plan:**
-   Unit tests for `ToolBarBuilder`:
    *   Ensure it correctly creates a `QToolBar` and all `QAction`s.
    *   Verify icons, tooltips, and checkable states are set.
    *   Test that `_update_tool_bar_state` correctly sets the checked state of actions.
-   Integration tests:
    *   Run the application, click toolbar buttons, and verify that the `ToolManager`'s active tool changes.
    *   Verify that when the active tool changes (e.g., programmatically via `tool_manager.set_active_tool()`), the correct toolbar button becomes checked.
    *   Verify that placeholder icons are correctly displayed.

**Risks & Mitigations:**
-   **Risk:** Managing SVG icons might require `PySide6.QtSvgWidgets` or similar, adding a dependency.
-   **Mitigation:** Verify if `QIcon` can load SVGs directly. If not, consider a simpler icon format or add `QtSvgWidgets`.
-   **Risk:** The `setup_application` function in `main.py` is becoming quite large due to all the wiring.
-   **Mitigation:** This is acceptable for a "composition root." If it becomes unwieldy, a dedicated `ApplicationBuilder` class could be introduced later to encapsulate `setup_application`'s logic.