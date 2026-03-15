# Technical Design Document 4: Advanced Nested Grid Editor (SciFig Grid 2.0)

## 1. Introduction & Objectives

This document outlines the architectural blueprint for "SciFig Grid 2.0," transforming the application's layout capabilities from a simple tabular applier into a fully interactive, WYSIWYG nested grid editor. The design draws inspiration from MS Word and Excel table engines, mapped onto the rigorous constraints of publication-quality scientific plotting.

### 1.1. Core Objectives
1.  **Arbitrary Nesting**: Support for recursive grid structures (grids within grids) up to an arbitrary (but practically limited, e.g., 10) depth.
2.  **Absolute CM Precision**: Guarantee that a 0.5 cm gap between plots remains exactly 0.5 cm regardless of nesting depth, completely bypassing Matplotlib's relative `GridSpec` limitations.
3.  **Excel-Style Interaction**: Support for visual row/column spanning (merging), interactive divider dragging, and intuitive block-based collision handling.
4.  **"Shrink-to-Fit" Optimization**: Automatically calculate whitespace for overlapping text labels while strictly respecting the Figure Size as a Hard Limit.
5.  **Mixed-Content Support**: Allow grids to contain `PlotNode`s, other `GridNode`s, empty cells, and free-floating vector annotations.

---

## 2. Architectural Paradigm Shift: Logical Grid vs. Renderer

### 2.1. The Limitation of Matplotlib `GridSpec`
Currently, the application relies on Matplotlib's `GridSpec` (and `constrained_layout`) to calculate plot positions. This poses a severe problem for nesting: Matplotlib calculates `wspace` and `hspace` as a fraction of the *average subplot size*. In a nested grid, the average subplot size shrinks, making absolute CM spacing impossible to enforce natively without complex, brittle inverse-math.

### 2.2. The Custom Engine Solution
We must decouple the **Logical Layout** from the **Rendering Engine**.
1.  **The Layout Engine (`GridLayoutEngine`)** will be completely rewritten. It will no longer use `GridSpec`. Instead, it will be a pure, recursive mathematical calculator that takes a tree of nodes and outputs exact absolute physical geometries (CM) for every cell.
2.  **The Renderer (`FigureRenderer`)** will act as a "dumb" drawer. It receives the absolute geometries, normalizes them to the figure, and places Matplotlib `Axes` precisely at those coordinates using `fig.add_axes([rect])`.

### 2.3. The "Surgical Scoped Sync" Pattern
To maintain 60 FPS performance during complex layout updates, the system follows a "Surgical" synchronization rule: **Update all positions first, then draw exactly once.**
*   **Dirty-Geometry Tracking**: `PlotNode` and `GridNode` will maintain a `_geometry_version` (distinct from the aesthetic `_version`). This is only incremented by the `GridLayoutEngine` if the absolute CM `Rect` has actually changed.
*   **Surgical Render**: The `FigureRenderer` will only call the expensive `ax.set_position()` if a node's `_geometry_version` is higher than the renderer's `last_synced_geom_version` (tracked in the renderer's internal registry).
*   **The Bypass Pattern (Real-Time Dragging)**: During interactive divider dragging, the `OverlayRenderer` will use the `NodeController.reconcile_node_property` bypass path. This updates the model's ratios silently without triggering a full Matplotlib redraw loop until the mouse is released.

---

## 3. Data Structures & Scene Graph Integration

To support nesting, the flat `GridConfig` must be replaced by a hierarchical node in the Scene Graph.

### 3.1. `GridNode` (Extends `GroupNode` or `SceneNode`)
The `GridNode` acts as a managing container with a strict layout policy.
*   **Attributes**:
    *   `rows`: int
    *   `cols`: int
    *   `row_ratios`: list[float]
    *   `col_ratios`: list[float]
    *   `gutters`: `Gutters` (Absolute CM)
    *   `margins`: `Margins` (Only applied if it is the root GridNode; nested nodes usually have 0 margins, relying on the parent cell's padding).
*   **Behavior**: It calculates the boundaries of its $M \times N$ cells and assigns exact physical coordinates to its children based on their `GridPosition`.

### 3.2. `GridPosition` (Attached to Children)
Any node placed *inside* a `GridNode` must have a `GridPosition` dataclass to define its location.
*   **Attributes**:
    *   `row`: int
    *   `col`: int
    *   `rowspan`: int (Default 1)
    *   `colspan`: int (Default 1)
*   **Floating Sibling Rule**: A node (e.g., `TextNode`) can exist as a sibling to the `GridNode` in the `scene_root`. In this case, it lacks a `GridPosition` and is treated as a free-floating annotation layer above the grid.

### 3.3. Serialization (`to_dict` / `from_dict`)
Because `GridNode` is part of the Scene Graph, serialization becomes naturally recursive.
*   The `to_dict` of a `GridNode` serializes its grid parameters, and then calls `to_dict` on all its `children`.
*   The `node_factory` must be updated to reconstruct `GridNode` instances and correctly restore the `GridPosition` of their children.

### 3.4. Single Source of Truth (SSoT) Mandate
To ensure architectural integrity and prevent "State Drift," the application enforces a strict Single Source of Truth policy:
1.  **No Shadow Configs**: The `LayoutManager` and `ApplicationModel` are prohibited from caching `GridConfig` DTOs as persistent state. All layout parameters must be derived directly from the active `GridNode` in the Scene Graph.
2.  **DTOs as Proposals**: The `GridConfig` dataclass is demoted from a "State Container" to a "Transient Proposal." It is used strictly as a messenger for analysis results (e.g., Inference, Optimization) before being translated into commands.
3.  **Atomic Property Commands**: A new `BatchChangeNodePropertyCommand` replaces bulk DTO-based updaters. This allows the UI to modify a subset of properties (e.g., `row_ratios` and `margins.top`) via path-based updates without needing a full `GridConfig` object to represent the intent.

---

## 4. The Custom CM-Based Layout Engine (`GridLayoutEngine`)

The engine must calculate the bounding box for every cell, moving top-to-bottom, left-to-right.

### 4.1. The "Option A" Data Spines Strategy
*   **The Grid defines the Spines**: The cells calculated by the engine represent the absolute physical boundaries of the Matplotlib Axes (the data rectangle), NOT the outer bounding box of the labels.
*   **Empty Cells**: An empty cell simply means a calculated region of space with no `PlotNode` assigned to that `(row, col)`. No Axes are drawn, but the space is reserved. 
*   **Automatic Centering**: If a `ShapeNode` or `TextNode` is assigned to a grid cell, the `GridNode` must calculate its `geometry` such that the node is **perfectly centered** (horizontally and vertically) within the cell's calculated boundaries.

### 4.2. The Recursive Calculation Algorithm (Dry Run)
1.  **Input**: `node: GridNode`, `available_rect: Rect` (Physical CM).
2.  **Deduct Margins**: `net_rect = available_rect - node.margins`.
3.  **The "Cell-Padding" Model**: Internally, the engine treats gutters as **internal cell padding**. For a cell at `(r, c)`, the padding is:
    *   `Top = hspace[r-1] / 2` (if r > 0, else 0)
    *   `Bottom = hspace[r] / 2` (if r < rows-1, else 0)
    *   `Left = wspace[c-1] / 2` (if c > 0, else 0)
    *   `Right = wspace[c] / 2` (if c < cols-1, else 0)
4.  **Deduct Total Gutters**:
    *   Total W-Space = `sum(node.gutters.wspace)` (e.g., `(cols - 1) * 0.5 cm`).
    *   Total H-Space = `sum(node.gutters.hspace)`.
    *   `pure_cell_rect = net_rect - W-Space - H-Space`.
5.  **Calculate Cell Sizes**: Divide `pure_cell_rect` among the rows/cols according to `row_ratios` and `col_ratios`.
6.  **Coordinate Mapping**: Use `CoordinateService.transform_value` to ensure all internal math is performed in high-precision Physical CM before being normalized to Figure units for the renderer.
7.  **Assign Child Geometries**:
    *   For each child, calculate its spanning bounding box based on the summed width/height of spanned cells + internal gutters.
    *   Set the child's `geometry` to this absolute physical `Rect`.
    *   **Recursion**: If the child is *another* `GridNode`, recursively call `calculate_geometries(child, child.geometry)`.

---

## 5. Spacing Strategy & Whitespace Optimization

Because we use Option A (Grid = Spines), labels *can* overlap if the user sets `hspace` too small. We provide a "Shrink-to-Fit" optimizer to fix this automatically.

### 5.1. The Figure Size Hard Limit
*   The overall `Figure_Size` (e.g., 20cm x 20cm) is absolute and inviolable.
*   The optimizer cannot push plots outward past the margins. It must shrink the plots inward.

### 5.2. The "Shrink-to-Fit" Algorithm
Triggered via UI action `Events.OPTIMIZE_LAYOUT_REQUESTED`.
1.  **Identify Ink Footprint**: For every plot, calculate the `RequiredPadding` (Top, Bottom, Left, Right) needed for tick labels, titles, and axis labels. (Can use Matplotlib's `get_tightbbox`).
2.  **Calculate Required Gaps**: For every row interface, find the maximum required gap: `max(TopPlot.bottom_padding + BottomPlot.top_padding)`.
3.  **Calculate Available Data Space**: `Net_Width = Figure_Width - (Margins + Required Gaps)`.
4.  **Redistribute**: Update the root `GridNode.gutters` to match the `Required Gaps`. Recalculate the layout. The Spines will naturally shrink to fit the new gutters.

### 5.3. The "Minimum Viable Plot" Conflict
If `Net_Width` or `Net_Height` falls below `MIN_PLOT_SIZE` (e.g., 0.5 cm):
*   **Action**: The command is cancelled (or partially applied).
*   **Feedback**: The system publishes a `LAYOUT_IMPOSSIBLE` event.
*   **Visual Warning**: The `OverlayRenderer` highlights the offending cells with a red warning border, indicating the figure size is too small for the requested labels.

### 5.4. Initial Style Integration
*   When a `GridNode` is first created, it should query the `StyleService` for default font sizes and tick padding to estimate safe starting values for its `margins` and `gutters`, avoiding immediate overlap.

---

## 6. Visual Overlay & Interaction Mechanics (`OverlayRenderer`)

The `OverlayRenderer` is upgraded to provide WYSIWYG table-editing visuals, active ONLY when `LayoutMode.GRID` is selected.

### 6.1. Gutter Zones
*   Draw thick, semi-transparent grey bands (`QGraphicsRectItem`) representing the absolute physical space of the `hspace` and `wspace`.
*   These visually communicate "dead zones" where no data spines can exist.
*   **Visual Scoping**: For nested grids, the gutter bands and divider lines must only be drawn *within the bounding box* of their parent `GridNode`. They do not extend across the entire figure unless they belong to the root grid.

### 6.2. Interactive Dividers
*   Draw a primary thin line down the center of each Gutter Zone (e.g., at `hspace / 2`), with fine lines flanking the true gutter boundaries.
*   **Hover**: Hovering changes the cursor to `Qt.SplitHCursor` or `Qt.SplitVCursor`. A "+" icon can optionally appear to indicate row/col insertion.
*   **Drag Logic**:
    *   Dragging a vertical divider rightwards decreases the `col_ratio` of the left column and increases the `col_ratio` of the right column.
    *   The total figure width remains unchanged. The change is strictly a ratio redistribution.

### 6.3. The "Ink-Box" Ghost
*   When a plot is selected, draw the standard blue selection border around the *Spine* (`plotnode.geometry`).
*   Additionally, draw a faint, dotted secondary rectangle representing the `plotnode.ink_bbox` (the full extent of all labels).
*   **Margin Collision**: If the `ink_bbox` rect intersects the Figure's outer bounding box, the `OverlayRenderer` must turn the corresponding Figure Margin line red as a real-time warning.

---

## 7. Spanning & Resizing Actions

### 7.1. Excel-Style Resizing (Spanning)
*   **Interaction**: Grabbing a corner handle of a plot inside a Grid and dragging it does not set arbitrary pixel dimensions. It acts as a "Grid Span Selector".
*   **Multi-Cell Selection (For Merging)**: The `SelectionTool` is updated to support marquee selection (rubber-banding) specifically for Grid Cells. When the user drags across multiple empty or occupied cells, the overlay highlights the entire "candidate merge area".
*   **Visual Feedback**: As the mouse moves, a blue highlight "snaps" to the nearest cell boundaries, outlining the proposed span.
*   **The "Block" Collision Handling**:
    *   During the drag for **Resizing**, the system checks if the proposed span `(row_start:row_end, col_start:col_end)` intersects any cell occupied by *another* node.
    *   If **YES**: The highlight turns **RED**.
    *   If the user releases the mouse while RED, the action is discarded (no command pushed).
*   **Command**: `ResizeGridPlotCommand` updates the `colspan` and `rowspan` of the target node. For merging, the `MergeCellsCommand` is used, which replaces the selection with a single spanning node.

### 7.2. Moving / Reallocation
*   **Interaction**: Dragging the body of a plot allows moving it to another cell.
*   **Ghost Snapping**: During the drag, the `OverlayRenderer` must draw a "Ghost Target" rectangle that discretely **snaps to the nearest available grid cell** boundaries. This ensures the user sees exactly which cell the plot will occupy before they release the mouse.
*   **The "Block" Logic**: The "Block" logic applies identically: if the snapped ghost target overlaps an occupied cell, the ghost turns **RED**, the drop is rejected, and the plot returns to its origin.

---

## 8. Grid Manipulation Workflows & Ribbon UI

The Ribbon Bar must expose a "Table Design" style toolset. These map to specific commands that manipulate the `GridNode` structure.

### 8.1. Creation & Splitting
*   **New Grid Dropdown**: In the layout ribbon, a dropdown with a 7x6 grid of squares allows the user to hover and click to quickly create an initial grid (or a simple dialog asking for rows/cols as MVP).
*   **Insert Subplot**: Clicking an empty cell with the Plot Tool automatically instantiates a `PlotNode` spanning exactly that cell (1x1), dimensions calculated via the grid spec.
*   **Split Cell (Subdivide)**: Right-click -> "Split". Opens a dialog for rows/cols and their ratios.
    *   **Logic**: Removes the `PlotNode` (if present), creates a new `GridNode` at that `GridPosition`, and moves the original `PlotNode` into the `(0,0)` position of the new child grid.

### 8.2. Add/Delete Rows and Columns
*   **Ribbon Actions**: "Insert Row Above", "Insert Row Below", "Insert Column Left", "Insert Column Right".
*   **Add Logic (`InsertGridRowCommand`)**:
    *   Increments `node.rows`.
    *   Inserts a new default `row_ratio` (e.g., using the middle value of adjacent relative fractions to ensure size scaling makes sense: `1:1` -> `1:1:1`).
    *   Iterates through all children: If their `row >= insertion_index`, increment their `row` by 1.
    *   If a node spans *across* the insertion index, increment its `rowspan` by 1.
*   **Delete Action**: The inverse, but must handle deletion of any nodes completely contained within the deleted row/col (dubbed items left behind must be handled, e.g., leaving an empty cell).
*   **Auto Redistribute**: Buttons to set all `row_ratios` or `col_ratios` to equal sizes (`1.0`) on the topmost grid.

### 8.3. Cell Borders & Predefined Layouts
*   **Toggle Grid Lines**: A button in the ribbon to show/hide the grey gutter zones and divider lines in the `OverlayRenderer`, allowing the user to preview the clean figure without leaving Grid Mode.
*   **Cell Borders (Gutters)**: Configurable absolute CM values in the ribbon. Applying `0.5 cm` to the root grid propagates properly, but if nested grids have their own gutters, they are managed per `GridNode`. The style service will govern default narrow, wide, etc.
*   **Flattening**:
    *   Because flattening is a destructive mathematical approximation, it is explicitly a user command (`FlattenGridCommand`), never automatic.
    *   It calculates the lowest common denominator of rows/cols across the nested grids and translates them into a single, massive top-level `GridNode` with complex spans.

---

## 9. Implementation Sequence & Phased Roadmap

### **Mandatory Verification Rule**
To maintain architectural integrity, **every class** added or refactored during any phase must have its corresponding unit test file created (or updated) and successfully executed **immediately** after implementation. No phase is considered complete until all new logic is covered by automated tests.

### Phase 1: Model & Math Core (Non-Visual)
1.  Implement `GridNode` and `GridPosition` in `src/models/nodes/`.
2.  Refactor `ApplicationModel` to support the nested structure.
3.  Write the recursive CM-based calculator in `GridLayoutEngine`. Banish `GridSpec`.
4.  Implement recursive serialization/deserialization.
5.  *Milestone*: Headless unit tests prove 10-layer nesting maintains absolute CM gutters.

### Phase 2: Renderer & Static Visuals
6.  Refactor `FigureRenderer` to place axes directly using absolute geometries.
7.  Update `OverlayRenderer` to draw the Gutter Zones, interactive dividers, and Ink-Box Ghosts based on the new model.
8.  *Milestone*: The UI displays the grid structure, and plots render correctly, but nothing is interactive yet.

### Phase 3: Selection & Basic Interactions
9.  Update `SelectionTool` to handle "Block" collision logic for target areas.
10. Implement Excel-style Spanning (`rowspan`/`colspan`) via resize handles.
11. Implement Drag-and-Drop reallocation between cells.
12. *Milestone*: User can reorganize a static grid interactively.

### Phase 3.5: Legacy System Refactor (UI & Commands)
13. **New `ChangeGridPropertyCommand`**: 
    *   Implement a specialized command for `GridNode` attributes (rows, cols, row_ratios, col_ratios, gutters, margins).
    *   This command must publish a new granular event: `Events.GRID_COMPONENT_CHANGED`.
    *   It must also trigger `Events.SCENE_GRAPH_CHANGED` to notify the rendering pipeline.
14. **Event Registry Update**: Add `GRID_COMPONENT_CHANGED` to `src/shared/events.py`.
15. **LayoutController Refactor**: 
    *   Update `_handle_change_grid_parameter_request` to stop constructing legacy `GridConfig` objects.
    *   Instead, it must find the active `GridNode` and dispatch `ChangeGridPropertyCommand` for specific paths (e.g., `"rows"`, `"margins.top"`).
16. **LayoutManager Refactor**:
    *   Remove legacy `GridConfig` state management. 
    *   Subscribe to `GRID_COMPONENT_CHANGED`. Upon receiving, trigger the recursive `GridLayoutEngine` using the sender `GridNode`.
17. **ApplyGridCommand Refactor**: Update this command to handle the transition from Free-Form to Grid by:
    1. Creating a new root `GridNode`.
    2. Moving existing `PlotNode` siblings into the grid as children.
    3. Running the `GridLayoutEngine`.
18. *Milestone*: The Layout Tab UI is fully functional and controls the recursive grid engine via high-signal granular events.

### Phase 3.6: Semantic Cleanup & Domain Handshake
To prevent redraw cascades and maintain structural clarity, the event pipeline is strictly divided into "Aesthetic", "Layout", and "Geometry" domains using a handshake protocol.
19. **Event Taxonomy Update**: Refactor `src/shared/events.py` using standardized `PROPERTY` and `CHANGED` language.
    *   **Aesthetic Domain**: `PLOT_NODE_PROPERTY_CHANGED` (Affects ink/style only; replaces `PLOT_NODE_PROPERTY_CHANGED`).
    *   **Layout Domain**: `NODE_LAYOUT_CHANGED` (Structural intent: signals that a node has shifted slots or constraints).
    *   **Geometry Domain**: `NODE_GEOMETRY_CHANGED` (Positional fact: signals that mathematical CM coordinates are finalized; replaces `NODE_LAYOUT_RECONCILED`).
    *   **Reconciliation**: `PLOT_NODE_PROPERTY_RECONCILED` remains reserved strictly for the Bypass Pattern (back-sync from renderer to model).
20. **Command Taxonomy Update**:
    *   **`ChangeNodePropertyCommand`**: A generic updater for non-structural properties. It must be smart enough to publish `PLOT_NODE_PROPERTY_CHANGED` if the target is a `PlotNode`.
    *   **`MoveNodeCommand`**: A specialized structural command for drag-and-drop or grid reallocation. It must publish `NODE_LAYOUT_CHANGED`.
21. **Zero-Logic Handshake Implementation**:
    *   `LayoutManager`: Subscribes only to `NODE_LAYOUT_CHANGED`. Upon receiving, it runs the appropriate engine (Grid or Free-Form) and then publishes `NODE_GEOMETRY_CHANGED`.
    *   `FigureRenderer`: Subscribes to `PLOT_NODE_PROPERTY_CHANGED` (artist sync) and `NODE_GEOMETRY_CHANGED` (position sync).
    *   **Free-Form Refactor**: Update `LayoutController` alignment/distribution actions to use the new `MoveNodeCommand` (batch) and publish `NODE_LAYOUT_CHANGED` rather than generic structural changes.
22. *Milestone*: Clear architectural boundaries established. Responsibilities are strictly decoupled, ensuring atomic redraws and a maintainable, high-signal event bus for both Grid and Free-Form modes.


### Phase 4: Structural Mutations & Ribbon
13. Implement `InsertGridRowCommand`, `SplitCellCommand`, etc.
14. Wire these commands to the Ribbon UI (Table Design tab) and Context Menus.
15. Implement Interactive Dividers (dragging to change ratios).
16. *Milestone*: Full WYSIWYG table editing.

### Phase 5: Polish & Finalization
17. Implement the "Shrink-to-Fit" whitespace optimization logic.
18. Implement the `MIN_PLOT_SIZE` conflict highlighting.
19. Integrate `StyleService` for default layout generation (Narrow, Wide presets).
20. **Final Documentation Update**: Exhaustively update the `README.md`, `Architecture Design Document (ADD)`, and `Folder Structure` document to reflect the new nested grid architecture and specialized components.
21. *Milestone*: Feature complete, verified, and fully documented.

---

## 10. Edge Cases & Risks

*   **Risk**: Recursive Geometry drift.
    *   **Mitigation**: Perform all calculations using high-precision floats from the top of the tree down, passing `available_rect` downward. Do not rely on relative delta accumulations.
*   **Risk**: Matplotlib rendering overlap during fast resizes.
    *   **Mitigation**: Maintain the Dual-Layer Canvas paradigm. The expensive `FigureRenderer` must only sync on `mouse_release`. The `OverlayRenderer` provides all live feedback.
*   **Risk**: User accidentally hides a plot behind an opaque `ShapeNode` sibling.
    *   **Mitigation**: Rely on the existing Z-Order controls (`MoveToFront`, `MoveToBack`) which will still function for top-level siblings.
*   **Risk**: Corrupted spans (e.g., `rowspan` extends beyond `node.rows`).
    *   **Mitigation**: The `GridNode` must have a `validate_structure()` method called after any command execution to assert that all children's `GridPosition`s are mathematically sound, auto-clamping them if violated.

---

## 11. Obsolete Components & Cleanup

Following the successful implementation and verification of SciFig Grid 2.0, the following legacy components will be redundant and should be removed or completely refactored:

### 11.1. Legacy Engines
*   **`src/models/layout/grid_layout_engine.py`**: The entire class using Matplotlib `GridSpec` and `constrained_layout` logic will be deleted.
*   **`src/models/layout/free_layout_engine.py`**: Its logic will be absorbed into the root Scene Graph traversal, as "Free Layout" is simply a grid-less `scene_root`.

### 11.2. Legacy Configuration
*   **`src/models/layout/layout_config.py`**: The `GridConfig`, `Margins`, and `Gutters` dataclasses will be obsolete, as their properties are now first-class attributes of the `GridNode` and `PlotNode`.
*   **`src/models/layout/layout_manager.py`**: The flat geometry caching and "Grid Inference" heuristics will be replaced by the recursive tree-traversal engine.

### 11.3. Logic & UI
*   **`src/controllers/layout_controller.py`**: String-based parameter parsing (e.g., `_on_param_change("margin_top", val)`) will be removed in favor of direct `ChangePropertyCommand` calls to the `GridNode`.
*   **Matplotlib `GridSpec` Dependency**: All imports and logic involving `matplotlib.gridspec` for layout calculation will be banished from the services and models, moving strictly into the renderer if needed for "dumb" axes placement.