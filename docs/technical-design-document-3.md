# Technical Design Document 3: Themed Layout Orchestration

## Epic: Themed Figure and Grid Layout

This epic focuses on centralizing the source of truth for figure-level layout defaults (margins, gutters, and padding) within the `StyleService`. By treating layout configuration as a themeable property, we ensure consistency across different journal styles and remove service-level coupling between the layout and style systems.

---

### Feature 1: StyleService Expansion for Figure Layout
**Description:** Extend the `StyleService` to act as the "Mandatory Factory" for layout-related dataclasses. This removes redundant configuration in `ConfigService` and ensures that switching themes (e.g., from Nature to Science) automatically updates figure margins and plot spacing.

**Planned Implementation:**

1.  **Modify `StyleService` (`src/services/style_service.py`):**
    *   **Task:** Add figure layout keys to `REQUIRED_KEYS`:
        *   `figure.subplot.left`, `figure.subplot.right`, `figure.subplot.bottom`, `figure.subplot.top` (Absolute Margins).
        *   `figure.subplot.wspace`, `figure.subplot.hspace` (Absolute Gutters).
        *   `figure.constrained_layout.h_pad`, `figure.constrained_layout.w_pad`, `figure.constrained_layout.hspace`, `figure.constrained_layout.wspace` (Constrained Pads).
    *   **Task:** Implement `create_themed_grid_config(rows, cols) -> GridConfig`:
        *   Resolves the above keys from `_current_style`.
        *   Returns a fully populated `GridConfig` with nested `Margins` and `Gutters` objects.
    *   **Task:** Subscribe to `Events.INITIALIZE_LAYOUT_THEME_REQUESTED`.
    *   **Task:** Implement `_on_initialize_layout_theme_requested`:
        *   Generates the themed `GridConfig` and publishes `Events.LAYOUT_CONFIG_CHANGED`.

2.  **Enrich `GridConfig` Dataclass (`src/models/layout/layout_config.py`):**
    *   **Task:** Add fields for constrained layout parameters: `h_pad: float`, `w_pad: float`, `constrained_hspace: float`, `constrained_wspace: float`.
    *   **Task:** Update `to_dict` and `from_dict` to include these new fields.

**Testing Plan:**
*   **Unit Tests (`tests/unit/services/test_style_service.py`):** Verify `create_themed_grid_config` correctly maps `.mplstyle` keys to the `GridConfig` hierarchy.
*   **Integration Tests:** Load a custom style and verify that the layout-related events carry the correct themed values.

---

### Feature 2: Stateless Grid Engine with Absolute-to-Relative Conversion
**Description:** Refactor the `GridLayoutEngine` to be strictly stateless and mathematically correct. The engine will no longer pull from services; it will rely entirely on the provided `GridConfig` and perform internal conversion of absolute figure fractions to Matplotlib-relative values.

**Planned Implementation:**

1.  **Modify `GridLayoutEngine` (`src/models/layout/grid_layout_engine.py`):**
    *   **Task:** Remove `config_service` from `__init__`.
    *   **Task:** Implement absolute-to-relative conversion logic in `_apply_fixed_layout`:
        *   `avg_subplot_w = (plot_area_width - (cols-1)*abs_gutter_w) / cols`.
        *   `gs_wspace = abs_gutter_w / avg_subplot_w`.
    *   **Task:** Update `_apply_constrained_layout` to use pads provided in the `GridConfig` instead of pulling from `ConfigService`.
    *   **Task:** Fix the "Zero Plot" bug: Return `grid_config.margins` and `grid_config.gutters` when the plot list is empty.

2.  **Update `LayoutManager` (`src/services/layout_manager.py`):**
    *   **Task:** Refactor `_create_minimal_grid_config` to publish `INITIALIZE_LAYOUT_THEME_REQUESTED` instead of manually constructing a config from `ConfigService`.

**Testing Plan:**
*   **Unit Tests (`tests/unit/models/layout/test_grid_layout_engine.py`):** 
    *   Verify that absolute gutters in `GridConfig` result in correct `0.375` (not `0.390`) plot widths in a 2x2 grid.
    *   Verify that empty plot lists preserve the input margins.
*   **Regression Tests:** Run existing `FreeLayoutEngine` tests to ensure no impact on other layout modes.

---

### Feature 3: Event-Driven Layout Initialization
**Description:** Standardize how layouts are initialized and reset using the event system, matching the pattern used for `PlotProperties`.

**Planned Implementation:**

1.  **Modify `src/shared/events.py`:**
    *   **Task:** Register `INITIALIZE_LAYOUT_THEME_REQUESTED`.

2.  **Update `ProjectController` / `LayoutController`:**
    *   **Task:** Use the initialization event when creating a new project or switching to grid mode for the first time.

**Risks & Mitigations:**
*   **Risk:** `GridSpec` behavior when `avg_subplot_width` is near zero.
*   **Mitigation:** Add guard clauses in the conversion logic to return `0.0` or a safe minimum if denominators are too small.
*   **Risk:** Backward compatibility with old project files.
*   **Mitigation:** `GridConfig.from_dict` will provide defaults for the new constrained padding fields if they are missing from older serialized dictionaries.
