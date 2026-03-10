# Technical Design Document 5: Absolute Physical Coordinate System as Source of Truth

## 1. Introduction & Objectives

### 1.1. The Problem
Currently, SciFig uses **Normalized Figure Coordinates (0.0–1.0)** as the absolute source of truth for plot geometries and layout constraints. This creates a "Leaky Abstraction":
1.  **Non-Deterministic Sizing**: Resizing the figure window silently changes the physical size of all plots.
2.  **Logic Duplication**: The conversion math (`pixels / width` or `cm / fig_width`) is scattered across `CanvasController`, `LayoutManager`, and `OverlayRenderer`.
3.  **Rounding Drift**: Repetitive back-and-forth conversions between spaces during UI interactions lead to floating-point errors where plots "shift" by sub-pixels.

### 1.2. The Objective
To introduce a centralized **`CoordinateService`** and a **`CoordinateSpace`** enum to manage all transformations. We will move the **Absolute Source of Truth** to **Centimeters (cm)** within the Headless Model.

---

## 2. Architectural Components

### 2.1. The `CoordinateSpace` Enum
A new enum in `src/shared/types.py` to explicitly tag the **Reference Basis** of a value:
*   `PHYSICAL`: Absolute distance in Centimeters (The Model's Canonical Truth).
*   `FRACTIONAL_FIG`: 0.0 to 1.0 relative to the total Figure size.
*   `FRACTIONAL_LOCAL`: 0.0 to 1.0 relative to the **immediate parent** (e.g., subplot spacing).
*   `DISPLAY_PX`: Device pixels relative to the Canvas viewport.

### 2.2. The `CoordinateService`
A central, stateless service that provides a unified API for transformations and unit mapping.
**Core Responsibilities**:
*   **Space Translation**: Converts values between `PHYSICAL`, `FRACTIONAL_FIG`, `FRACTIONAL_LOCAL`, and `DISPLAY_PX`.
*   **Canonical Mapping**: Acts as the system "Gateway". Converts inbound user units (inches, mm) to the internal `PHYSICAL` (CM) standard.
*   **Display Formatting**: Converts internal CM to requested display units (e.g., for UI Spinboxes) with scientific rounding to prevent floating-point artifacts.

---

## 3. Data Structures & Model Updates

### 3.1. `ApplicationModel`
*   **New Property**: `figure_size: tuple[float, float]` (Width in cm, Height in cm).
*   **Initialization**: Sourced from `ConfigService` (converting default inches to cm).
*   **Event**: `Events.FIGURE_SIZE_CHANGED` published when changed.

### 3.2. `Rect` (Physical cm)
*   The `Rect` class in `src/shared/geometry.py` now strictly represents **Centimeters**. 
*   **Validation**: Methods like `scaled_by` will use a minimum threshold of `0.1 cm`.

---

## 4. Component Responsibilities

### 4.1. `CanvasController` (Input)
*   **Current**: Converts pixels to 0-1 using Matplotlib's `transFigure`.
*   **New**: Uses `CoordinateService` to convert that 0-1 value immediately into **Centimeters** using the `ApplicationModel.figure_size`.
*   **Impact**: Tools (`SelectionTool`, `AddPlotTool`) now receive and emit deltas in `cm`.

### 4.2. `LayoutManager` (Translation)
*   **Responsibility**: The sole provider of fractional geometries to the Renderer.
*   **Logic**: It queries the Layout Engines (which work in `cm`), then uses `CoordinateService` to scale them by the `figure_size` before publishing them to the `FigureRenderer`.

### 4.3. `GridLayoutEngine` (GridSpec Bridge)
*   **Margins**: Handled as absolute subtractions from the physical `figure_size`.
*   **Gutters**: Converts physical `cm` gaps into the relative `hspace/wspace` fractions expected by Matplotlib.
    *   `hspace = gutter_cm / average_subplot_height_cm`.

### 4.4. `OverlayRenderer` (View Feedback)
*   **Logic**: Uses `CoordinateService` to map the physical `Rect` from the model directly to `DISPLAY` pixels for drawing handles and ghosts.

---

## 5. Implementation & Migration Steps

### Phase 1: Foundation (Enums & Service)
1.  Define `CoordinateSpace` Enum.
2.  Implement `CoordinateService` in `src/services/coordinate_service.py`.
3.  **Test**: Add unit tests verifying `CM <-> Fractional <-> Pixel` math with various DPIs and figure sizes.

### Phase 2: Model & Event Update
1.  Add `figure_size` to `ApplicationModel`.
2.  Update `Rect` docstrings and verify `src/shared/geometry.py` logic works with absolute floats.
3.  Add `Events.FIGURE_SIZE_CHANGED`.
4.  **Test**: Verify Model state and event publication.

### Phase 3: The Interaction Bridge
1.  Refactor `CanvasController` to use `CoordinateService`.
2.  Update `SelectionTool` logic to handle `cm` deltas.
3.  **Test**: Verify a "1cm drag" on screen results in a `+1.0` change in the `Rect` model regardless of figure size.

### Phase 4: The Layout Bridge
1.  Refactor `LayoutManager.get_current_layout_geometries` to use `CoordinateService` for physical->fractional mapping.
2.  Refactor `GridLayoutEngine` to handle physical margins and relative `GridSpec` gaps.
3.  **Test**: Verify that a 10cm wide plot on a 20cm figure renders at `0.5` position.

### Phase 5: View & Persistence
1.  Update `OverlayRenderer` to use the service for ghost drawing.
2.  Do NOT implement a versioning step. Backwards compatibility does not need to be maintained


---

## 6. Edge Cases & Constraints

*   **Zero or Negative Sizes**: When subtracting cm margins from the figure size, the available plot area could become `<= 0`. The engines must fallback to a minimum plot size (e.g., 0.2 cm).
*   **Precision**: Using CM as truth eliminates rounding drift during UI interactions.
*   **File I/O (Legacy)**: Existing saved projects assumption: normalized `0.5` becomes `0.5 cm`. There is no need to keep backwards compatibility to the legacy notation.

---

## 7. Affected Files Audit

To ensure a comprehensive migration, the following files must be reviewed and updated according to their coordinate space role:

### 7.1. Group A: Design Space (Primary Truth)
*These files currently store "Truth" as normalized values; they must shift to Physical Inches.*
*   `src/models/nodes/plot_node.py`: `self.geometry` storage and initialization.
*   `src/models/layout/layout_config.py`: `Margins` and `Gutters` data structures.
*   `src/shared/geometry.py`: `Rect` logic (docstrings and methods like `moved_by`).
*   `src/services/commands/add_plot_command.py`: Geometry passing for new nodes.
*   `src/services/commands/batch_change_plot_geometry_command.py`: Geometry updates.
*   `src/services/commands/change_grid_parameters_command.py`: `GridConfig` updates.

### 7.2. Group B: Fractional Space (The Translators)
*These files perform the math to convert Physical Model values into Matplotlib-ready fractions.*
*   `src/services/layout_manager.py`: Core translation logic in `get_current_layout_geometries` and grid heuristics.
*   `src/models/layout/free_layout_engine.py`: Math for `perform_align` and `perform_distribute`.
*   `src/models/layout/grid_layout_engine.py`: Conversion of physical margins/gutters to `GridSpec` relative values.
*   `src/ui/renderers/figure_renderer.py`: Version gating and comparison of MPL vs Model limits.

### 7.3. Group C: Viewport Space (Display & Interaction)
*These files bridge the screen pixels to the model.*
*   `src/ui/widgets/canvas_widget.py`: Pixel-to-Normalized mappings.
*   `src/controllers/canvas_controller.py`: Input capture scaling (Pixels -> Normalized -> Physical).
*   `src/ui/renderers/overlay_renderer.py`: Handle/Ghost drawing logic.
*   `src/services/tools/selection_tool.py`: Hit-test thresholds (currently hardcoded px).
*   `src/services/tools/add_plot_tool.py`: Click-vs-Drag thresholds.

### 7.4. Configuration & Utilities
*The source of constants.*
*   `configs/default_config.yaml`: `default_dpi`.
*   `configs/default.mplstyle`: `figure.figsize` and `figure.dpi`.
*   `src/services/config_service.py`: Provider of these constants.