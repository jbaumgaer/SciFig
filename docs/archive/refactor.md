# Refactoring Roadmap: An Incremental Approach to the v2 Architecture

This document provides a detailed, step-by-step guide for refactoring the application from v1 to v2. The core principle is to perform the refactor in **isolated, incremental phases**. Each phase must result in a fully functional application, allowing for safe, continuous integration and testing. This is achieved by temporarily allowing v1 and v2 systems to coexist, connected by "shims".

---

## Phase 1: Model Coexistence (The Shim Phase)

**Goal:** Introduce the new Scene Graph model (`v2`) to live *alongside* the old `ArtistModel` list (`v1`). The application will still functionally rely on the `v1` model, but the `v2` model will be built in parallel.

1.  **Create v2 Node Classes:**
    -   In a new directory `src/models/nodes/`, implement `SceneNode`, `GroupNode`, and `PlotNode` as planned.

2.  **Establish Model Coexistence in `ApplicationModel`:**
    -   **File:** `src/models/application_model.py`
    -   **Keep:** The existing `self.artists: list[ArtistModel]` and related methods (`add_artist`, `get_selected_artist`, etc.). These are the `v1` components.
    -   **Add:** The new `v2` model root: `self.scene_root = GroupNode(name='root')`.
    -   **Create a Synchronization Shim:** Modify the existing `v1` methods to update the `v2` model in the background.
        -   In `add_artist(artist_model)`, after `self.artists.append(artist_model)`, add logic to create a corresponding `PlotNode` and add it to `self.scene_root`.
        -   In `clear_artists()`, after clearing the `v1` list, clear the `v2` tree: `self.scene_root.children.clear()`.
        -   In `update_artist_geometry(index, new_geometry)`, after updating the `v1` model, find the corresponding `v2` node by index and update its geometry as well.

3.  **Verification:**
    -   Run the application. It should work exactly as before. The `v2` model is being built and modified transparently, but is not yet used by any other part of the application.

**Result of Phase 1:** A fully functional app. The `v2` model structure has been introduced and is kept in sync with the `v1` state, ready for the next phase.

---

## Phase 2: The Renderer Switch

**Goal:** Switch the rendering logic to use the new `v2` Scene Graph model, while controllers and other components continue to use the `v1` model.

1.  **Implement the `Renderer` Class:**
    -   **File:** `src/views/renderer.py`
    -   Create the `Renderer` class with a `render(figure, root_node)` method that recursively traverses the `v2` scene graph and draws the corresponding Matplotlib artists.

2.  **Implement a Feature Flag for Rendering:**
    -   **File:** `main.py`
    -   At the top, add a global flag: `USE_V2_RENDERER = True`.
    -   Remove the old `redraw_canvas` function.
    -   Create a new `redraw_logic` function or lambda that acts as a switchboard.
    -   Instantiate `v1_renderer_func = ...` (the old `redraw_canvas` logic) and `v2_renderer = Renderer()`.
    -   Connect the `model.modelChanged` signal to a new callback:
        ```python
        def redraw_callback():
            if USE_V2_RENDERER:
                v2_renderer.render(view.canvas_widget.figure, model.scene_root)
            else:
                # The old logic, adapted to be callable
                v1_redraw_logic(view.canvas_widget.figure, model)
            view.canvas_widget.figure_canvas.draw()
        ```

3.  **Verification:**
    -   Run the app with `USE_V2_RENDERER = True`. The application's appearance and behavior should be identical to Phase 1.
    -   Flip the flag to `False` and re-run to confirm that the old rendering path still works. This allows for direct comparison to catch any visual regressions.

**Result of Phase 2:** A fully functional app whose rendering is now powered by the `v2` scene graph. The core interaction logic is untouched.

---

## Phase 3: Controller & Selection Coexistence

**Goal:** Introduce the `v2` Tool-based controllers and selection model, while using a shim to keep the `v1` selection model in sync for legacy components.

1.  **Implement Tool Infrastructure:**
    -   Create the `src/controllers/tools/` directory, the `BaseTool` abstract class, and the `SelectionTool`.
    -   Create the `ToolManager` class in `src/controllers/tool_manager.py`.

2.  **Implement Dual Selection Model:**
    -   **File:** `src/controllers/tools/selection_tool.py`
    -   The `SelectionTool`'s `on_mouse_press` will use the `v2` hit-testing: `node = model.get_node_at(position)`.
    -   **File:** `src/models/application_model.py`
    -   Create a new `v2` selection method: `set_selection(nodes: list[SceneNode])`. This method will:
        1.  Update the new `self.selection` property.
        2.  Emit a new `selectionChanged` signal.
        3.  **Shim Logic:** Find the index of the selected node in the `v2` tree and use that index to call the old `set_selected_artist(index)`. This keeps the `v1` selection state in sync.

3.  **Activate the New Controller System:**
    -   **File:** `main.py`
    -   Instantiate `ToolManager`, add `SelectionTool` to it, and set it as the default. Pass the manager to `CanvasController`.
    -   **File:** `src/controllers/canvas_controller.py`
    -   Gut the logic from `on_press`, etc. They should now only delegate the event to `self.tool_manager.get_active_tool()`.

4.  **Update Renderer Highlight:**
    -   The rendering logic for the selection highlight (in the new `Renderer` class) must be updated to read from the `v2` `model.selection` list instead of the `v1` `model.get_selected_artist()`.

**Result of Phase 3:** A fully functional app where user interaction is now handled by the extensible `Tool` system. The `v2` selection model is now the primary one, with the `v1` selection being updated solely for compatibility with components that are not yet migrated.

---

## Phase 4: Migrating Views & Deprecating the v1 Model

**Goal:** Build `v2`-native UI components, migrate functionality to them, and finally remove the now-obsolete `v1` model and shims.

1.  **Implement `PropertiesView`:**
    -   Create the `PropertiesView` widget and dock it in the `MainWindow`.
    -   It will connect **only** to the new `model.selectionChanged` signal. It will be completely unaware of the `v1` model.

2.  **Introduce the Command System:**
    -   Create the `src/commands/` directory, `BaseCommand`, `CommandManager`, and `ChangePropertyCommand`.
    -   The `PropertiesView` will be the *first* component to use this system. When a property is edited in the `PropertiesView` UI, it will not modify the model. Instead, it will create the appropriate `Command` and pass it to the `CommandManager` for execution.

3.  **Migrate Functionality and Deprecate:**
    -   Incrementally add functionality to `PropertiesView` until it is a feature-complete replacement for `PlotConfigDialog`.
    -   Once parity is achieved, delete `src/views/dialogs.py`.
    -   This is the final step: Go to `src/models/application_model.py` and delete `self.artists`, `_selected_artist_index`, and all `v1`-related methods and shims. The application is now fully on the `v2` architecture.

**Result of Phase 4:** A fully functional app running entirely on the new, extensible, and robust v2 architecture. The refactor is complete.