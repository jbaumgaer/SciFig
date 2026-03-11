from enum import Enum, auto


class Events(Enum):
    """
    A centralized enumeration of all events used in the application's
    EventAggregator system. This defines specific, granular events for a
    robust, decoupled, and event-driven architecture.
    """

    # === NOTIFICATION EVENTS (System -> View & System -> System) ===
    # Announce that a state change has *already occurred*.

    # --- Project Lifecycle & Status ---
    PROJECT_OPENED = auto()  # Payload: project_metadata: dict
    PROJECT_WAS_RESET = auto()
    PROJECT_IS_DIRTY_CHANGED = auto()  # Payload: is_dirty: bool
    WINDOW_TITLE_DATA_READY = auto()  # Payload: title: str, is_dirty: bool

    # --- Node Property Changes ---
    NODE_RENAMED = auto()  # Payload: node_id: str, new_name: str
    NODE_VISIBILITY_CHANGED = auto()  # Payload: node_id: str, is_visible: bool
    NODE_LOCKED_CHANGED = auto()  # Payload: node_id: str, is_locked: bool
    NODE_POSITION_CHANGED = auto()  # Payload: node_id: str, new_position: tuple
    NODE_SIZE_CHANGED = auto()  # Payload: node_id: str, new_size: tuple

    # --- Generic Path-Based Property Changes (NEW) ---
    PLOT_COMPONENT_CHANGED = auto()  # Payload: node_id: str, path: str, new_value: Any
    GRID_COMPONENT_CHANGED = auto()  # Payload: node_id: str, path: str, new_value: Any
    PLOT_COMPONENT_RECONCILED = auto()# Payload: node_id: str, path: str, new_value: Any (Sync only, no redraw)

    SUB_COMPONENT_SELECTED = auto()  # Payload: node_id: str, path: str
    TEMPLATE_LOADED = auto()  # Payload: root_node: SceneNode

    # --- Node Data & Structure Changes ---
    SCENE_GRAPH_CHANGED = auto()  # Payload: new_scene_graph: dict
    NODE_DATA_FILE_PATH_UPDATED = (
        auto()
    )  # Payload: node_id: str, new_path: Optional[Path]
    NODE_DATA_LOADED = auto()  # Payload: node_id: str
    NODE_ADDED_TO_SCENE = (
        auto()
    )  # Payload: parent_id: str, new_node_id: str, index: int
    NODE_REMOVED_FROM_SCENE = auto()  # Payload: parent_id: str, removed_node_id: str
    NODE_REPARENTED_IN_SCENE = (
        auto()
    )  # Payload: node_id: str, new_parent_id: str, new_index: int
    NODE_ORDER_CHANGED_IN_SCENE = (
        auto()
    )  # Payload: parent_id: str, new_ordered_child_ids: list[str]
    SWITCH_SIDEPANEL_TAB = auto()  # Payload: tab_key: str

    # --- Layout Changes ---
    LAYOUT_CONFIG_CHANGED = auto()  # Payload: new_config: dict
    FIGURE_SIZE_CHANGED = auto()  # New: Figure dimensions in physical CM changed
    ACTIVE_LAYOUT_MODE_CHANGED = auto()  # Payload: mode: str (LayoutMode.value)
    APPLY_GRID_REQUESTED = auto()  # New: Request to apply a GridConfig to the model
    UI_LAYOUT_MODE_CHANGED = auto()  # Payload: mode: str (LayoutMode.value)

    # --- Other Notification Events ---
    SELECTION_CHANGED = auto()  # Payload: selected_node_ids: list[str]
    ACTIVE_TOOL_CHANGED = auto()  # Payload: tool_name: str
    RECENT_PROJECTS_LIST_UPDATED = auto()  # Payload: file_list: list[str]
    GRID_CONFIG_PARAMETERS_CHANGED = auto()  # Payload: new_grid_config: dict

    # === REQUEST EVENTS (View -> System) ===
    # Request that an action be performed by the system.

    # --- Project & File Requests ---
    NEW_PROJECT_REQUESTED = auto()
    NEW_PROJECT_FROM_TEMPLATE_REQUESTED = auto()
    OPEN_PROJECT_REQUESTED = auto()
    OPEN_RECENT_PROJECT_REQUESTED = auto()  # Payload: file_path: Path
    SAVE_PROJECT_REQUESTED = auto()
    SAVE_PROJECT_AS_REQUESTED = auto()
    UNDO_REQUESTED = auto()
    REDO_REQUESTED = auto()
    WINDOW_TITLE_REQUESTED = auto()

    # --- Node Property Change Requests ---
    CHANGE_PLOT_TYPE_REQUESTED = auto()  # Payload: node_id: str, new_plot_type: str
    RENAME_NODE_REQUESTED = auto()  # Payload: node_id: str, new_name: str
    CHANGE_NODE_VISIBILITY_REQUESTED = auto()  # Payload: node_id: str, is_visible: bool
    CHANGE_NODE_LOCKED_REQUESTED = auto()  # Payload: node_id: str, is_locked: bool
    CHANGE_NODE_POSITION_REQUESTED = auto()# Payload: node_id: str, new_position: tuple
    CHANGE_NODE_SIZE_REQUESTED = auto()  # Payload: node_id: str, new_size: tuple

    # --- Generic Path-Based Property Change Requests ---
    CHANGE_PLOT_COMPONENT_REQUESTED = auto() # Payload: node_id: str, path: str, value: any
    PLOT_COMPONENT_RECONCILIATION_REQUESTED = auto() # Payload: node_id: str, path: str, value: any
    INITIALIZE_PLOT_THEME_REQUESTED = auto() # Payload: node_id: str, plot_type: ArtistType
    HYDRATE_PLOT_PROPERTIES_REQUESTED = auto()  # Payload: node_id: str, overrides: dict

    # --- Node Data & Structure Requests ---
    SELECT_DATA_FILE_FOR_NODE_REQUESTED = auto()  # Payload: node_id: str
    APPLY_DATA_TO_NODE_REQUESTED = auto()  # Payload: node_id: str, file_path: Path
    GROUP_NODES_REQUESTED = auto()  # Payload: node_ids: list[str]
    UNGROUP_NODE_REQUESTED = auto()  # Payload: node_id: str
    DELETE_NODES_REQUESTED = auto()  # Payload: node_ids: list[str]
    DATA_FILE_SELECT_REQUESTED = auto()  # Payload: node_id: str
    APPLY_DATA_FILE_REQUESTED = auto()  # Payload: node_id: str, file_path: Path
    ADD_PLOT_REQUESTED = auto()  # Payload: geometry: Rect
    BATCH_CHANGE_PLOT_GEOMETRY_REQUESTED = auto()  # Payload: geometries: dict[str, Rect]
    UPDATE_INTERACTION_PREVIEW_REQUESTED = auto()  # Payload: geometries: list[Rect], style: str
    CLEAR_INTERACTION_PREVIEW_REQUESTED = auto()

    # --- Layout Requests ---
    TOGGLE_LAYOUT_MODE_REQUESTED = auto()  # Payload: is_grid_mode: bool
    ALIGN_PLOTS_REQUESTED = auto()  # Payload: alignment_mode: str
    DISTRIBUTE_PLOTS_REQUESTED = auto()  # Payload: distribution_mode: str
    CHANGE_GRID_PARAMETER_REQUESTED = auto()  # Payload: param_name: str, new_value: any
    INFER_GRID_PARAMETERS_REQUESTED = auto()
    OPTIMIZE_LAYOUT_REQUESTED = auto()

    # --- Tooling Requests ---
    ACTIVATE_TOOL_REQUESTED = auto()  # Payload: tool_name: str

    # --- UI Interaction Requests ---
    REQUEST_RECENT_PROJECTS_LIST = auto()
    SUBPLOT_SELECTION_IN_UI_CHANGED = auto()  # Payload: node_id: str
    SHOW_ADD_PLOT_DIALOG_REQUESTED = auto()  # Payload: center_pos: tuple[float, float]
    PROMPT_FOR_OPEN_PATH_REQUESTED = auto()
    PROMPT_FOR_SAVE_AS_PATH_REQUESTED = auto()
    PROMPT_FOR_TEMPLATE_SELECTION_REQUESTED = auto()
    PROMPT_FOR_OPEN_PATH_FOR_NODE_DATA_REQUESTED = auto()  # Payload: node_id: str

    # === UI Interaction Notifications (Responses to UI Requests) ===
    # These events provide the results of a UI interaction back to the system.
    PATH_PROVIDED_FOR_OPEN = auto()  # Payload: path: Optional[Path]
    PATH_PROVIDED_FOR_SAVE_AS = auto()  # Payload: path: Optional[Path]
    TEMPLATE_PROVIDED_FOR_NEW = auto()  # Payload: template_name: Optional[str]
    PATH_PROVIDED_FOR_NODE_DATA_OPEN = (
        auto()
    )  # Payload: node_id: str, path: Optional[Path]
