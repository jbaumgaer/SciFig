# Technical Design Document 4: Interactive Layout Capabilities (Complete & Exhaustive)

## 1. Introduction & Objectives

This document defines the architectural blueprint for introducing fully interactive, vector-editor-style layout capabilities to the application's Free Form layout mode. The goal is to provide a user experience similar to Adobe Illustrator or PowerPoint, where scientific plots can be manipulated as fluid geometric objects.

### 1.1. Core Objectives:
1.  **Interactive Plot Creation**: Support for adding plots via precise dimension dialogs or visual "rubber-banding."
2.  **High-Performance Transformation**: Moving and resizing plots with 60 FPS feedback.
3.  **Dynamic Deletion**: Intuitive removal via keyboard and context menus.
4.  **Depth Management**: Z-Order control (Front/Back) for complex, overlapping figure compositions.
5.  **Professional Alignment**: Snapping and visual guides to ensure publication-quality precision.

---

## 2. Architectural Paradigm: The Dual-Layer Canvas

### 2.1. The Performance Problem
The primary challenge is Matplotlib's rendering architecture. Matplotlib is a "Truth-First" renderer; any change to an Axes position triggers a cascade of calculations (tick repositioning, spine clipping, artist re-pathing). Performing this 60 times per second during a drag operation is computationally prohibitive and results in significant lag.

### 2.2. The Dual-Layer Solution
To solve this, we decouple the **Aesthetic Data Layer** from the **Interactive UI Layer**:
*   **Matplotlib Layer (`FigureCanvasQTAgg`)**: The bottom layer. It remains static during mouse movement. It is only updated when an interaction concludes (e.g., `mouseRelease`).
*   **Interaction Layer (`QGraphicsScene`)**: The top layer. As a `QGraphicsView`, the `CanvasWidget` can host lightweight Qt objects. We will use these for "Ghosts" and "Rubber-bands." Updating a Qt rectangle's coordinates is a simple O(1) memory operation, ensuring silky-smooth feedback regardless of plot complexity.

---

## 3. Data Structures & Foundational Refactoring

### 3.1. The `Rect` Value Object (`src/shared/geometry.py`)
Currently, geometries are managed as raw `tuple[float, float, float, float]`. To support complex scaling and movement, we will promote this to a formal `Rect` dataclass.
*   **Attributes**: `x, y, w, h` (Normalized Figure Coordinates 0.0 - 1.0).
*   **Logic (Simulated Dry Run)**: 
    *   **Movement**: `moved_by(dx, dy)` calculates a new `Rect` relative to the start point. **Critical**: To avoid cumulative rounding errors, we always calculate from the *initial* rect, not the *previous frame's* rect.
    *   **Scaling**: `scaled_by(anchor, dx, dy)` is more complex. If the "Right" handle is dragged, `x` remains the anchor; if the "Left" handle is dragged, `x` moves while `width` adjusts inversely.
    *   **Clamping**: `clamp_to_bounds(0, 0, 1, 1)` ensures plots cannot be dragged entirely off the paper.

### 3.2. Coordinate Mapping & Symmetry (`src/ui/widgets/canvas_widget.py`)
The "Y-Inversion" problem is the most common source of layout bugs. Qt's 0,0 is Top-Left; Matplotlib's 0,0 is Bottom-Left.
*   **`map_to_figure(scene_pos)`**: Translates Qt pixels to normalized units.
*   **`map_from_figure(fig_pos)`**: Translates normalized units back to Qt pixels for overlay placement.
*   **Symmetry Mandate**: These functions must be mathematically symmetrical. Any "drift" between the ghost rectangle and the final Matplotlib axis is a failure state.

### 3.3. Interaction Overlay API (`src/ui/widgets/canvas_widget.py`)
A stateless management system for temporary UI elements (ghosts, handles, guides).
*   **`draw_preview_rect(rect: QRectF, style: str) -> QGraphicsRectItem`**: Adds a styled rectangle (e.g., dashed border for rubber-band, semi-transparent blue for ghosting) to the `QGraphicsScene`. 
*   **`draw_handle(pos: QPointF) -> QGraphicsRectItem`**: Draws a small square (e.g., 6x6 pixels) for resizing affordances.
*   **`draw_guide_line(p1: QPointF, p2: QPointF)`**: Draws alignment lines during snapping.
*   **`clear_previews()`**: Flushes all interactive items from the scene.
*   **Z-Value Policy**: Previews must use a `zValue` range (e.g., 1000+) to ensure they never fall behind the Matplotlib canvas.

---

## 4. Feature Implementation Details

### 4.1. Feature A & B: Add Plot (The Rubber-Band Workflow)
**Tool**: `AddPlotTool`.
*   **Simulated Dry Run**:
    1.  **Press**: Record `_start_pos_fig`. The tool is now in "Defining" state.
    2.  **Move**: Calculate the bounding box between start and current mouse. Publish `UPDATE_PREVIEW_REQUESTED` with style="rubber_band" (dashed gray).
    3.  **Release**:
        *   **The Click Check**: If the resulting width/height is less than 5 pixels (the "noise threshold"), interpret this as a **Click**. Publish `SHOW_ADD_PLOT_DIALOG_REQUESTED`.
        *   **Implementation Detail**: Upon dialog confirmation, the new subplot must be initialized such that the original click point becomes the **geometric center** of the new `Rect`.
        *   **The Drag Check**: If larger, interpret as a **Visual Creation**. Publish `ADD_PLOT_REQUESTED(geometry=final_rect)`.
*   **Command (`AddPlotCommand`)**: Creates a `PlotNode`. It must immediately request themed `PlotProperties` from the `StyleService` so the new plot isn't "empty" but inherits the current project's visual style.

### 4.2. Feature C: Deletion (The Safe Removal Workflow)
**Tool**: `SelectionTool`.
*   **Workflow**:
    *   **Keyboard**: Listens for `Qt.Key_Delete`.
    *   **Context Menu**: `CanvasController` maps a right-click to the node ID and shows a menu.
*   **Command (`DeleteNodesCommand`)**:
    *   **How it works**: Simply removing a node is easy; supporting **Undo** is hard. The command must deep-copy the nodes (and their dataframes!) into memory before removal.
    *   **Refinement**: The `Renderer` must be notified via `Events.SCENE_GRAPH_CHANGED` so it can call `fig.delaxes()` on the corresponding Matplotlib objects.

### 4.3. Move Plots (Tool: `SelectionTool`)
*   **State**: `_is_dragging`, `_drag_start_fig`, `_initial_geoms: dict[PlotID, Rect]`, `_ghosts: dict[PlotID, QGraphicsRectItem]`.
*   **Workflow Logic**: 
    1.  On `mousePress`, create a semi-transparent ghost for every selected node and add to the `_ghosts` map.
    2.  As the user drags, the tool calculates the delta from the **original** press point. **Critical**: Do not use frame-by-frame deltas to avoid rounding error accumulation.
    3.  **Persistence Detail**: The `CanvasController` must maintain references to these ghost items. During `mouseMove`, it updates the existing items using `item.setRect()` rather than clearing and recreating the scene. This prevents flickering and ensures high performance.
    4.  *Performance Optimization*: If more than 10 plots are selected, moving individual ghosts may lag. In this case, the tool will fall back to a single "Group Bounding Box" ghost to maintain 60 FPS.
*   **Command**: `BatchChangePlotGeometryCommand` applies final positions on `mouse_release`.

### 4.4. Resize Plots (Tool: `SelectionTool`)
*   **Visual Affordances**: When a node is selected, 8 small handles (6x6 pixel squares) are drawn around its bounding box in the Qt Overlay Layer.
*   **Scaling Logic (Dry Run)**: 
    1.  `mouse_press`: Detect if a handle was hit. Set the `_resize_anchor` (usually the opposite corner).
    2.  `mouse_move`: Recalculate the `Rect` relative to the anchor. 
        *   *Example*: Dragging the "Bottom-Right" handle increases `width` and `height` while keeping `x` and `y` constant. Dragging "Left" increases `width` but also moves `x`.
    3.  **Constraints**: Implement a minimum size threshold (e.g., 0.05 fig units) to prevent negative geometries or "inside-out" flipping.
*   **Ghosting**: Update the ghost item `QRectF` continuously during the scale interaction.

### 4.5. Snapping & Alignment Guides (Service: `SnappingService`)
*   **Magnetic Logic**: As a plot is moved or resized, the `SelectionTool` queries the `SnappingService` with the `proposed_rect`.
*   **Checkpoints**:
    *   **Figure Edges**: Snaps to 0.0, 0.5, and 1.0.
    *   **Sibling Edges**: Snaps to the edges or centers of other plots in the scene.
*   **Thresholds**: A `pixel_threshold` (e.g., 5px) is converted to figure units. If the proposed edge is within this range, it "jumps" to the target.
*   **Outputs**: Returns a `SnappedRect` and a list of `GuideLines` (e.g., vertical magenta lines) to be drawn in the Qt Overlay.

### 4.6. Z-Order Control (Presenter: `ProjectController`)
*   **Depth Management**: Controlling overlap in Free Form mode is essential for complex layouts.
*   **Commands**: `MoveToFrontCommand`, `MoveToBackCommand`.
*   **Logic**: Reorders the node within its parent's `children` list. 
*   **Renderer Integration**: The `Renderer` must be updated to derive the Matplotlib `zorder` attribute from the node's index in its parent's children list during synchronization. Items appearing later in the `children` list are automatically assigned a higher `zorder`.

### 4.7. Implementation Details & Foreseen Edge Cases
1.  **The "Invalid Region" Boundary**: `Rect.clamp_to_bounds(0, 0, 1, 1)` must be enforced during Move and Resize to prevent users from losing plots off-canvas.
2.  **Coordinate Precision (The "Jitter" Fix)**: All drag math is performed in **Qt Scene (pixel) coordinates** and only converted to **Figure (0-1)** at the moment of Command execution. This prevents the "dancing" or jittering of ghost rectangles due to floating-point truncation during movement.
3.  **Anchor Point Stability**: During resizing, the "Anchor" point (the corner opposite to the one being dragged) must remain strictly fixed in **Figure coordinates** to prevent the entire plot from drifting.
4.  **Matplotlib Figure Limits Sync**: Moving a plot changes its *position on the paper*, not the *data limits* (`xlim`/`ylim`) inside the axes.
5.  **Grid Mode Safeguard**: The `SelectionTool` must act as a gate. If `ui_selected_layout_mode == GRID`, it must disable all Move/Resize/Add logic and fallback to simple selection to prevent corrupting the `GridSpec` logic.

---

## 5. Architectural Responsibilities & Decoupling

| Component | Responsibility | Pattern Adherence |
| :--- | :--- | :--- |
| **`Rect`** | Mathematical source of truth for geometry. | Headless Model |
| **`Tools`** | Statefully interpreting raw mouse/keyboard into Intents. | Controller Extension |
| **`CanvasWidget`** | Drawing raw pixels and temporary Qt overlays. | Passive View |
| **`CanvasController`** | Mapping "Click at X,Y" to "Node ID" and orchestrating previews. | Presenter |
| **`SnappingService`** | Calculating snap points and guide coordinates. | Domain Service |
| **`Commands`** | Encapsulating reversible state changes. | Command Pattern |

### Decoupling Strategy:
*   **Tools -> Model**: Tools **NEVER** modify the model directly. They only publish `..._REQUESTED` events.
*   **Model -> View**: The Model **NEVER** tells the View to redraw. It publishes `..._CHANGED` events which the `Renderer` and `Controllers` observe.
*   **Qt -> Matplotlib**: The Interaction Layer (Qt) and Visualization Layer (Matplotlib) only synchronize at the end of an interaction (Atomic Sync).

---

## 6. Implementation Sequence

1.  **Phase 1: Foundations**: Implement `Rect` dataclass and symmetrical coordinate mapping. Write exhaustive unit tests.
2.  **Phase 2: Infrastructure**: Add `draw_preview_rect` and `draw_guide_line` to `CanvasWidget`.
3.  **Phase 3: Deletion**: Implement the command and context menu.
4.  **Phase 4: Creation**: Implement `AddPlotTool` with rubber-band and dialog support.
5.  **Phase 5: Transformation**: Implement ghost-dragging, resizing handles, and the snapping engine.

---

## 7. Risks & Mitigations

*   **Risk: Coordinate Drift**: Floating-point rounding error during back-and-forth mapping.
    *   *Mitigation*: Use high-precision `decimal` for math if `float` fails, but primarily solve by using `initial_pos + delta` logic.
*   **Risk: Grid Mode Corruption**: Moving a plot while in Grid mode.
    *   *Mitigation*: The `LayoutManager` acts as a guard. Tools must verify `layout_mode == FREE_FORM` before enabling transformation logic.
*   **Risk: Undo Complexity**: Multiple plots moving at once.
    *   *Mitigation*: Use a `MacroCommand` to wrap individual `ChangeProperty` calls into a single undoable action.
