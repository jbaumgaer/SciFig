# Technical Design Document 2: Ribbon Bar Implementation

## Epic: Ribbon-Style User Interface

This epic transitions the application from a sidebar-centric model to a modern, icon-driven "Ribbon" interface. This improves discoverability of scientific plotting tools and provides a more intuitive workflow for figure assembly, styling, and layout.

---

### Feature 1: Ribbon Bar UI Construction (Passive View)
**Description:** Construct the visual hierarchy of the Ribbon Bar using a `QTabWidget` containing specialized `QToolBar`s. This phase focuses purely on the "Passive View"—building the widgets, setting layouts, and applying icons/labels without connecting them to application logic or events.

**Planned Implementation:**

1.  **Modify `configs/default_config.yaml`:**
    *   **Task:** Add a `ribbon` section under `paths` to define icon resources for all new buttons:
        *   `insert.plots.line` (Line), `insert.plots.scatter` (Scatter), `insert.plots.bar` (Bar), `insert.plots.area` (Area), `insert.plots.pie` (Pie), `insert.plots.histogram` (to be created), `insert.plots.candlestick` (Candlestick), `insert.plots.contour` (to be created), `insert.plots.waterfall` (to be created), `insert.plots.stairs` (to be created), `insert.arrows.arrow_right` (Arrow_Right), `insert.arrows.arrow_bottom_right` (Arrow_Bottom_Right), `insert.shapes.square` (Square), `insert.shapes.rectangle` (Rectangle), `insert.shapes.circle` (Circle), `insert.shapes.pentagon` (Pentagon), `insert.shapes.Hexagon` (Hexagon), `insert.text.text_field` (Text_Field), `insert.text.text` (Text), `insert.text.bullet_list` (Bullet_List), `insert.text.numbered_list` (Numbered_List), `insert.text.check_list` (Check_List), `insert.symbol` (to be created, make a big omega), `insert.formula` (to be created, make a pi) 
        *   `layout.margins` (to be created in the same style as the one from the layout screenshot), `layout.format`  (to be created in the same style as the one from the layout screenshot).
        *   `design.nature` (placeholder preview), `design.science` (placeholder preview), `design.cell` (placeholder preview), `design.colors` (to be created in the same style as the one from the design screenshot), `design.fonts` (Fonts).

2.  **Create `RibbonBar` Widget (`src/ui/widgets/ribbon_bar.py`):**
    *   **Task:** Implement `RibbonBar` inheriting from `QTabWidget`.
    *   **Task:** Configure the tab widget: `self.setTabPosition(QTabWidget.North)`, `self.setDocumentMode(True)`.
    *   **Task:** Implement `add_ribbon_tab(self, name: str, toolbar: QToolBar)` to host toolbars.
    *   **Task:** Apply CSS/styling to ensure toolbars are non-floatable and buttons use `Qt.ToolButtonTextUnderIcon` with a larger `iconSize` (e.g., 32x32).

3.  **Create `RibbonBarBuilder` (`src/ui/builders/ribbon_bar_builder.py`):**
    *   **Task:** Implement `_build_insert_tab()`: Creates a `QToolBar` with groups for "Plots" (Line, Scatter, Bar, etc.), "Shapes" (Square, Circle etc.), "Text" (Text, Lists etc.) and "Arrows" (Right, Bottom Right).
    *   **Task:** Implement `_build_design_tab()`: Creates a `QToolBar` featuring a placeholder `GalleryWidget` for Journal Templates, and "Variant" controls for Colors and Fonts.
    *   **Task:** Implement `_build_layout_tab()`: Creates a `QToolBar` with "Page Setup" (Margins, Format) and "Arrange" (Align, Distribute, Grid Toggle).
    *   **Task:** Implement `build() -> tuple[RibbonBar, RibbonActions]`: Orchestrates the creation and returns the widget and an action container.

4.  **Modify `MainWindow` (`src/ui/windows/main_window.py`):**
    *   **Task:** Update `__init__` to accept `ribbon_bar` and `ribbon_actions`.
    *   **Task:** Add the `ribbon_bar` to the top area using a `QVBoxLayout` above the central widget or `self.addToolBar(Qt.TopToolBarArea, ribbon_bar)`.

5.  **Modify `CompositionRoot` (`src/core/composition_root.py`):**
    *   **Task:** Instantiate `RibbonBarBuilder` and pass the results to the `MainWindow` assembly.

**Testing Plan:**
*   **Unit Tests (`tests/ui/builders/test_ribbon_bar_builder.py`):** Verify `build()` produces a `RibbonBar` with three tabs and specific action labels/icons.
*   **Integration Tests:** Launch the app and verify the Ribbon Bar appears at the top, tabs switch correctly, and icons render at the expected size.

---

### Feature 2: Event Integration & Core Logic Binding
**Description:** Bind the UI actions from Feature 1 to the application's core logic via the `EventAggregator`. This phase connects the Ribbon to existing plot creation, layout management, and command execution services.

**Planned Implementation:**

1.  **Modify `src/shared/events.py`:**
    *   **Task:** Register new request events: `INSERT_PLOT_REQUESTED`, `APPLY_DESIGN_TEMPLATE_REQUESTED`, `PROMPT_FOR_MARGINS_REQUESTED`, `PROMPT_FOR_FIGURE_FORMAT_REQUESTED`.

2.  **Update `RibbonBarBuilder`:**
    *   **Task:** Connect all `QAction.triggered` signals to `event_aggregator.publish()`.
    *   **Task:** Ensure `INSERT_PLOT_REQUESTED` carries the `ArtistType` payload.

3.  **Update `ProjectController` (`src/controllers/project_controller.py`):**
    *   **Task:** Subscribe to `Events.INSERT_PLOT_REQUESTED`.
    *   **Task:** Implement `handle_insert_plot(self, plot_type: ArtistType)`:
        *   Create a `PlotNode` with default styles for the type.
        *   Execute an `AddNodeCommand`.

4.  **Update `LayoutController` (`src/controllers/layout_controller.py`):**
    *   **Task:** Subscribe to alignment and distribution events from the Layout tab.
    *   **Task:** Ensure "Grid Toggle" in the Ribbon correctly triggers `Events.TOGGLE_LAYOUT_MODE_REQUESTED`.

**Testing Plan:**
*   **Unit Tests (`tests/controllers/test_project_controller.py`):** Mock `EventAggregator` and verify that `INSERT_PLOT_REQUESTED` triggers the creation of the correct node type.
*   **Integration Tests:** Click "Line Plot" in the Ribbon and verify a new plot appears on the canvas. Verify that "Align Left" in the Ribbon correctly aligns selected plots.

---

### Feature 3: Implementation of Advanced Ribbon Tools (Unimplemented Logic)
**Description:** Implement the underlying services and logic for Ribbon features that currently have no backend support, such as Journal Style Templates, Global Color Schemes, and Fine-Grained Margin Control.

**Planned Implementation:**

1.  **Design Tab: Style Registry (`src/services/style_service.py`):**
    *   **Task:** Implement a library of journal-specific specifications (e.g., `Nature`: 89mm width, `Science`: 2.25in width, specific fonts/DPI).
    *   **Task:** Implement `ApplyJournalStyleCommand` to update global figure properties.

2.  **Design Tab: Global Color & Font Management:**
    *   **Task:** Implement `ThemeManager` to handle application-wide color palette shifts (e.g., "Colorblind Friendly", "Pastel", "High Contrast").
    *   **Task:** Connect the Ribbon's Font dropdown to a service that updates `matplotlib.rcParams` and triggers a full scene refresh.

3.  **Layout Tab: Margin & Format Dialogs:**
    *   **Task:** Implement `MarginPromptDialog` and `FormatPromptDialog` (simple UI windows for numerical input).
    *   **Task:** Update `LayoutManager` to accept these parameters and trigger a `Shadow Optimization` cycle to reposition all plots accordingly.

**Testing Plan:**
*   **Unit Tests:** Verify `StyleService` correctly loads "Nature" specifications.
*   **Integration Tests:** Apply the "Nature" style via the Ribbon and verify the figure size and default font family update correctly in the `ApplicationModel`.

**Risks & Mitigations:**
*   **Risk:** Ribbon consumes too much vertical space on small screens.
*   **Mitigation:** Ensure the Ribbon can be collapsed (minimized) to show only tabs, or use a responsive layout.
*   **Risk:** Matplotlib font management can be inconsistent across OSs.
*   **Mitigation:** Fallback to standard system fonts (Arial/Helvetica) if specific journal fonts are missing.
