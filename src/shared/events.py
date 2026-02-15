from enum import Enum, auto
from pathlib import Path
from typing import Optional


class Events(Enum):
    """
    A centralized enumeration of all events used in the application's
    EventAggregator system. This is structured to guide the refactoring from
    generic events to a more specific, ideal event system.
    """

    # --- Generic Events (To Be Phased Out) ---
    # These are broad events that will be replaced by the more specific events
    # defined in the "Ideal Event System" section. They are kept for now to
    # guide the refactoring process of individual components.

    MODEL_CHANGED = auto()
    # Replaced by: PROJECT_IS_DIRTY_CHANGED, and specific NODE_* and SCENE_GRAPH_* events.

    NODE_PROPERTY_CHANGED_REQUEST = auto()
    # Replaced by: RENAME_NODE_REQUESTED, CHANGE_NODE_VISUAL_PROPERTY_REQUESTED, etc.

    SCENE_GRAPH_CHANGED_NOTIFICATION = auto()
    # Replaced by: NODE_ADDED_TO_SCENE, NODE_REMOVED_FROM_SCENE, etc.

    # --- Ideal Event System (Specific & Symmetric) ---

    # === NOTIFICATION EVENTS (System -> View & System -> System) ===
    # Announce that a state change has *already occurred*.

    # --- Events that replace MODEL_CHANGED ---
    PROJECT_OPENED = auto()  # Payload: project_metadata: dict
    PROJECT_WAS_RESET = auto()
    PROJECT_IS_DIRTY_CHANGED = auto()  # Payload: is_dirty: bool
    # Note: Redraws previously triggered by MODEL_CHANGED should now listen to
    # the specific visual change events (e.g., NODE_POSITION_CHANGED).

    # --- Events that replace SCENE_GRAPH_CHANGED_NOTIFICATION ---
    NODE_ADDED_TO_SCENE = auto()  # Payload: parent_id: str, new_node_id: str, index: int
    NODE_REMOVED_FROM_SCENE = auto()  # Payload: parent_id: str, removed_node_id: str
    NODE_REPARENTED_IN_SCENE = auto()  # Payload: node_id: str, new_parent_id: str, new_index: int
    NODE_ORDER_CHANGED_IN_SCENE = auto()  # Payload: parent_id: str, new_ordered_child_ids: list[str]

    # --- Events for specific property changes (also replaces MODEL_CHANGED) ---
    NODE_RENAMED = auto()  # Payload: node_id: str, new_name: str
    NODE_POSITION_CHANGED = auto()  # Payload: node_id: str, new_position: tuple
    NODE_SIZE_CHANGED = auto()  # Payload: node_id: str, new_size: tuple
    NODE_VISIBILITY_CHANGED = auto()  # Payload: node_id: str, is_visible: bool
    PLOT_PROPERTY_CHANGED = auto()  # Payload: node_id: str, property_name: str, new_value: any

    # --- UI Interaction Notifications ---
    PATH_PROVIDED_FOR_OPEN = auto()  # Payload: path: Optional[Path]
    PATH_PROVIDED_FOR_SAVE_AS = auto()  # Payload: path: Optional[Path]
    TEMPLATE_PROVIDED_FOR_NEW = auto()  # Payload: template_name: Optional[str]

    # --- Other Notification Events ---
    SELECTION_CHANGED = auto()  # Payload: selected_node_ids: list[str]
    LAYOUT_CONFIG_CHANGED = auto()  # Payload: new_config: dict
    ACTIVE_TOOL_DID_CHANGE = auto()  # Payload: new_tool_name: str
    RECENT_PROJECTS_LIST_UPDATED = auto()  # Payload: file_list: list[str]

    # === REQUEST EVENTS (View -> System) ===
    # Request that an action be performed by the system.

    # --- Project & File Requests ---
    NEW_PROJECT_REQUESTED = auto()
    NEW_PROJECT_FROM_TEMPLATE_REQUESTED = auto()
    OPEN_PROJECT_REQUESTED = auto()
    OPEN_RECENT_PROJECT_REQUESTED = auto()  # Payload: file_path: Path
    SAVE_PROJECT_REQUESTED = auto()
    SAVE_PROJECT_AS_REQUESTED = auto()

    # --- Edit & History Requests ---
    UNDO_REQUESTED = auto()
    REDO_REQUESTED = auto()

    # --- Symmetric requests that replace NODE_PROPERTY_CHANGED_REQUEST ---
    RENAME_NODE_REQUESTED = auto()  # Payload: node_id: str, new_name: str
    CHANGE_NODE_POSITION_REQUESTED = auto()  # Payload: node_id: str, new_position: tuple
    CHANGE_NODE_SIZE_REQUESTED = auto()  # Payload: node_id: str, new_size: tuple
    CHANGE_NODE_VISIBILITY_REQUESTED = auto()  # Payload: node_id: str, is_visible: bool
    CHANGE_PLOT_PROPERTY_REQUESTED = auto()  # Payload: node_id: str, property_name: str, new_value: any

    # --- Symmetric requests for Scene Graph changes ---
    GROUP_NODES_REQUESTED = auto()  # Payload: node_ids: list[str]
    UNGROUP_NODE_REQUESTED = auto()  # Payload: node_id: str

    # --- Plot Data & Mapping Requests ---
    DATA_FILE_SELECT_REQUESTED = auto()  # Payload: node_id: str
    APPLY_DATA_FILE_REQUESTED = auto()  # Payload: node_id: str, file_path: Path
    CHANGE_PLOT_TYPE_REQUESTED = auto()  # Payload: node_id: str, new_plot_type: str
    MAP_DATA_COLUMN_REQUESTED = auto()  # Payload: node_id: str, channel: str, column_name: str
    CHANGE_AXIS_LIMITS_REQUESTED = auto()  # Payload: node_id: str, xlim: tuple, ylim: tuple

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
    PROMPT_FOR_OPEN_PATH_REQUESTED = auto()
    PROMPT_FOR_SAVE_AS_PATH_REQUESTED = auto()
    PROMPT_FOR_TEMPLATE_SELECTION_REQUESTED = auto()
