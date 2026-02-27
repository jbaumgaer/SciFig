# Technical Design Document 2 (Revised): Hierarchical Theming, Headless Architecture, and Dynamic UI

## Epic Overview
This epic transitions the application from a flat, coupled property model to a **Strict Hierarchical Tree**. It enforces a "No Defaults" policy where all visual attributes are injected via the `StyleService`. 
Crucially, this revision addresses the architectural violations currently breaking the system: it strictly enforces a **Headless Model** (stripping Matplotlib from the data layer) and implements a **Sanitized Interaction Layer** to decouple UI/Tools from backend rendering events.

### Completed Prerequisites (Do Not Re-implement)
*   **Hierarchical Dataclasses:** `plot_properties.py` atoms (`FontProperties`, `LineProperties`, etc.) are established.
*   **Style Injection:** `StyleService` is functional, validating against `REQUIRED_KEYS` and acting as the sole factory.
*   **Path-Based Commands:** `ChangePlotPropertyCommand` correctly handles recursive traversal, wildcards, and versioning.
*   **Event Infrastructure:** Generic path events (`CHANGE_PLOT_COMPONENT_REQUESTED`, `PLOT_COMPONENT_CHANGED`, `SUB_COMPONENT_SELECTED`) exist in `events.py`.

---

## Outstanding Implementation Plan

### Feature 1: Enforcing the Headless Model (`PlotNode`)
**Problem:** `PlotNode` is currently broken. It holds live Matplotlib `Axes` references, uses stale property classes (`AxesLimits`), and relies on backend rendering for hit-testing, violating the MVP Passive View mandate.

**Implementation Steps:**
1.  **Modify `src/models/nodes/plot_node.py`:**
    *   **Purge Backend:** Remove `import matplotlib` and delete the `self.axes` attribute.
    *   **Restore Serialization:** Rewrite `from_dict` and `to_dict` to exclusively use the new recursive `PlotProperties.from_dict()` and `to_dict()` methods. Remove manual reconstruction of legacy classes.
    *   **Headless Hit-Testing:** Refactor `hit_test(pos)`. It must no longer use `self.axes.get_window_extent()`. Instead, perform a purely mathematical bounds check against `self.geometry` (which is stored in normalized 0-1 figure coordinates).
2.  **Modify `src/models/plots/plot_properties.py` (Cleanup):**
    *   Uncomment and properly type the commented-out fields in `TextProperties` (e.g., `rotation`, `va`, `ha`) and `AxisProperties` to ensure full visual control is restored.

### Feature 2: Renderer as the "Artist Registry"
**Problem:** Because the Model is now headless, it can no longer manage the lifecycle of Matplotlib objects. The `Renderer` must take ownership.

**Implementation Steps:**
1.  **Modify `src/ui/renderers/renderer.py`:**
    *   **Registry Implementation:** Add `self._axes_registry: dict[str, matplotlib.axes.Axes]` to map `node.id` to the live axes.
    *   **Lifecycle Management:** In `_render_plots`, query the registry by `node.id`. If missing, create the axes via the `CoordSyncStrategy` and store it.
    *   **Garbage Collection:** Subscribe the `Renderer` to `Events.NODE_REMOVED_FROM_SCENE`. When a node is deleted, the Renderer must remove the `Axes` from the Matplotlib `Figure` and delete it from the `_axes_registry` to prevent memory leaks and "zombie" plots.
    *   **Strategy Cleanup:** Move hardcoded property hacks (like `set_limits` overrides) into the respective `CoordSyncStrategy` to ensure `_sync_component` remains a generic recursive loop.

### Feature 3: Sanitized Interaction Layer
**Problem:** `CanvasController` passes Matplotlib `MouseEvent` and `PickEvent` objects directly to the `ToolService`, coupling the entire interactive layer to the Matplotlib backend.

**Implementation Steps:**
1.  **Modify `src/ui/widgets/canvas_widget.py`:**
    *   Remove business logic from `mouseDoubleClickEvent` and `wheelEvent`. The widget should strictly handle Illustrator-style Qt viewport navigation (panning/zooming the artboard, not the data).
    *   Implement a `map_to_figure(qt_pos) -> tuple[float, float]` helper to safely translate screen pixels into 0-1 figure coordinates.
2.  **Modify `src/controllers/canvas_controller.py`:**
    *   **The Translator:** Intercept `button_press_event` from Matplotlib. Use `canvas_widget.map_to_figure()` to get coordinates, query the headless model (`get_node_at`), and pass backend-neutral data `(node_id, fig_coords, button)` to the `ToolService`.
    *   **Pick Sanitization:** Intercept Matplotlib's `pick_event`. Extract `node_id` and the `gid` (the property path) from the artist. Publish `Events.SUB_COMPONENT_SELECTED(node_id, path)`.
    *   **Logic Extraction:** Move the data mapping logic out of `on_data_ready`. It should trigger an `ApplyDataCommand` that utilizes the `StyleService` to generate valid properties.
3.  **Modify `src/services/tools/selection_tool.py`:**
    *   Update method signatures to accept primitive coordinates and `node_id` instead of Matplotlib events.
    *   Handle `path` selection updates seamlessly, completely detached from the GUI.

### Feature 4: Path-Aware Recursive UI Factory
**Problem:** The `PlotPropertiesUIFactory` is completely stale, trying to build massive, static forms for deprecated property models.

**Implementation Steps:**
1.  **Modify `src/ui/factories/plot_properties_ui_factory.py`:**
    *   **Breadcrumb Navigation:** Implement a header widget reflecting the `selected_path` (e.g., `Plot 1 > X-Axis > Label`). Clicking a parent segment must publish a `SUB_COMPONENT_SELECTED` event for that parent path.
    *   **Atom Builders:** Create modular generator functions:
        *   `build_text_ui(path)`: Yields QLineEdit (text), QComboBox (font), QPushButton (color picker).
        *   `build_line_ui(path)`: Yields QSlider (width), QComboBox (style), QPushButton (color).
    *   **Recursive Dispatch:** Rewrite `build_widgets(node, path)`. It must traverse `node.plot_properties` using the `path`. Using `is_dataclass` and `type()`, it dispatches layout generation to the specific Atom Builder matching that type.
    *   **Generic Data Binding:** Every generated widget is instantiated with its absolute `path`. On `editingFinished` or `clicked`, it publishes `CHANGE_PLOT_COMPONENT_REQUESTED(node.id, path, new_value)`.

### Feature 5: Controller & Event Pruning (Legacy Cleanup)
**Problem:** The codebase is littered with handlers for granular events that bypass the new architectural systems.

**Implementation Steps:**
1.  **Modify `src/controllers/node_controller.py`:**
    *   Delete all legacy property handlers (`_handle_generic_property_change_request`, `_handle_limit_editing_request`, etc.).
    *   This controller should now only handle structural scene requests (Rename, Visibility, Lock, Data Loading).
2.  **Modify `src/core/composition_root.py`:**
    *   Delete subscriptions to `PLOT_TITLE_CHANGED`, `PLOT_XLABEL_CHANGED`, etc.
    *   Ensure `SCENE_GRAPH_CHANGED`, `PLOT_COMPONENT_CHANGED`, and `LAYOUT_CONFIG_CHANGED` are the primary triggers for `_redraw_canvas_callback`. (The `Renderer`'s version gating will ensure this is performant).
3.  **Modify `src/shared/events.py`:**
    *   Delete the legacy property Enums (e.g., `PLOT_TITLE_CHANGED`) to finalize the deprecation and prevent future regressions.

---

### Data & Event Flow Example (Click to Edit)

1.  **User Clicks X-Axis Label:**
    *   Matplotlib detects hit on artist with `gid="coords.xaxis.label"`.
    *   `CanvasController` catches `pick_event`, extracts `gid`.
    *   `CanvasController` publishes `SUB_COMPONENT_SELECTED(node_id, "coords.xaxis.label")`.
2.  **State Update & UI Build:**
    *   `ApplicationModel` sets `selected_path = "coords.xaxis.label"`.
    *   `PlotPropertiesUIFactory` reads path, identifies `TextProperties` dataclass.
    *   Factory clears UI panel, renders `Text Atom Builder` (Text, Font, Color inputs).
3.  **User Edits Text:**
    *   User types "Time (s)" into QLineEdit.
    *   QLineEdit publishes `CHANGE_PLOT_COMPONENT_REQUESTED(node_id, "coords.xaxis.label.text", "Time (s)")`.
    *   `ChangePlotPropertyCommand` executes, updates nested dataclass, increments `_version`.
    *   `Renderer` detects version bump, syncs the new text to the specific Matplotlib title object.
