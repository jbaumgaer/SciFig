import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
from unittest.mock import MagicMock

import matplotlib.figure
import pytest

from src.controllers.canvas_controller import CanvasController
from src.controllers.layout_controller import LayoutController
from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.models.application_model import ApplicationModel
from src.models.layout.free_layout_engine import FreeLayoutEngine
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.nodes.scene_node import SceneNode
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import (
    PlotProperties,
    TextProperties,
    FontProperties,
    Cartesian2DProperties,
    AxisProperties,
    TickProperties,
    LineArtistProperties,
    LineProperties,
    SpineProperties,
)
from src.models.plots.plot_types import (
    AutolimitMode,
    CoordinateSystem,
    SpinePosition,
    TickDirection,
)
from src.services.commands.command_manager import CommandManager
from src.services.config_service import ConfigService
from src.services.coordinate_service import CoordinateService
from src.services.data_service import DataService
from src.services.event_aggregator import EventAggregator
from src.services.layout_manager import LayoutManager
from src.services.property_service import PropertyService
from src.services.style_service import StyleService
from src.services.tool_service import ToolService
from src.services.tools.selection_tool import SelectionTool
from src.shared.constants import ToolName


# --- Stack Definitions (Dataclasses) ---

@dataclass
class CoreStack:
    """The bare minimum for state and communication."""
    ea: EventAggregator
    model: ApplicationModel
    config: ConfigService

@dataclass
class TransactionalStack(CoreStack):
    """Adds the ability to perform undoable actions."""
    command_manager: CommandManager

@dataclass
class NodeStack(TransactionalStack):
    """Handles node manipulation and property changes."""
    controller: NodeController
    property_service: PropertyService

@dataclass
class LayoutStack(TransactionalStack):
    """Handles recursive grid and free-form layout logic."""
    manager: LayoutManager
    controller: LayoutController
    grid_engine: GridLayoutEngine
    free_engine: FreeLayoutEngine

@dataclass
class ProjectStack(TransactionalStack):
    """Handles project lifecycle and I/O."""
    controller: ProjectController
    data_service: DataService

@dataclass
class StyleStack(CoreStack):
    """Handles plot theming and property hydration."""
    service: StyleService

@dataclass
class InteractionStack(CoreStack):
    """Handles tools and coordinate transformations (Headless)."""
    tool_service: ToolService
    coord_service: CoordinateService
    canvas_controller: CanvasController


# --- Constants and Helpers for Baseline Testing ---
DEFAULT_FIG_SIZE = (20.0, 15.0)

def _get_default_integration_config():
    """Returns the baseline configuration for all integration tests."""
    return {
        "figure": {
            "default_width": DEFAULT_FIG_SIZE[0],
            "default_height": DEFAULT_FIG_SIZE[1],
            "default_dpi": 100,
            "default_facecolor": "white"
        },
        "ui": {
            "default_layout_mode": "free_form"
        },
        "layout": {
            "default_grid_rows": 1,
            "default_grid_cols": 1,
            "grid_margin_top": 1.0,
            "grid_margin_bottom": 1.0,
            "grid_margin_left": 1.0,
            "grid_margin_right": 1.0,
            "grid_hspace": [0.5],
            "grid_wspace": [0.5],
            "max_recent_files": 10
        },
        "paths": {
            "layout_templates_dir": "templates/layouts"
        }
    }

def _apply_overrides(config_dict, overrides):
    """
    Applies overrides to a config dictionary. 
    Supports dot-notation keys (e.g., 'figure.default_width').
    """
    if not overrides:
        return config_dict

    for key_path, value in overrides.items():
        keys = key_path.split(".")
        current = config_dict
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value
    return config_dict


# --- Base Fixtures ---

@pytest.fixture
def mock_figure():
    """Provides a mock matplotlib figure."""
    return MagicMock(spec=matplotlib.figure.Figure)

@pytest.fixture
def integration_config(request):
    """
    Provides a real ConfigService with baseline values and optional overrides.

    Supports arbitrary parametrization of any config key:
    @pytest.mark.parametrize("integration_config", [{"figure.default_width": 50.0}], indirect=True)
    """
    # Start with the baseline
    config_data = _get_default_integration_config()
    
    # Apply overrides if provided via request.param
    overrides = getattr(request, "param", {})
        
    config_data = _apply_overrides(config_data, overrides)

    config = ConfigService()
    config._config = config_data
    config._initialized = True # Mark as initialized for integration tests
    return config


# --- Stack Fixtures ---

@pytest.fixture
def core_stack(integration_config):
    """
    Provides the CoreStack.
    Always uses the size defined in the integration_config to ensure 
    consistency across the entire sub-assembly.
    """
    ea = EventAggregator()
    # Wrap publish in a spy so we can verify communication
    ea.publish = MagicMock(side_effect=ea.publish)

    # Extraction from Config ensures the Model and Config are in sync
    fig_w = integration_config.get("figure.default_width")
    fig_h = integration_config.get("figure.default_height")

    model = ApplicationModel(
        event_aggregator=ea,
        figure_size=(fig_w, fig_h)
    )
    return CoreStack(ea=ea, model=model, config=integration_config)


@pytest.fixture
def transactional_stack(core_stack):
    """Provides the TransactionalStack."""
    cmd_mgr = CommandManager(model=core_stack.model, event_aggregator=core_stack.ea)
    return TransactionalStack(
        **vars(core_stack),
        command_manager=cmd_mgr
    )

@pytest.fixture
def node_stack(transactional_stack):
    """Provides the NodeStack for integration tests."""
    prop_service = PropertyService()
    controller = NodeController(
        model=transactional_stack.model,
        command_manager=transactional_stack.command_manager,
        event_aggregator=transactional_stack.ea,
        property_service=prop_service
    )
    return NodeStack(
        **vars(transactional_stack),
        controller=controller,
        property_service=prop_service
    )

@pytest.fixture
def layout_stack(transactional_stack):
    """Provides the LayoutStack for integration tests."""
    grid_engine = GridLayoutEngine()
    free_engine = FreeLayoutEngine()
    prop_service = PropertyService()
    
    manager = LayoutManager(
        application_model=transactional_stack.model,
        free_engine=free_engine,
        grid_engine=grid_engine,
        config_service=transactional_stack.config,
        event_aggregator=transactional_stack.ea
    )
    
    controller = LayoutController(
        model=transactional_stack.model,
        event_aggregator=transactional_stack.ea,
        command_manager=transactional_stack.command_manager,
        layout_manager=manager,
        property_service=prop_service
    )
    
    return LayoutStack(
        **vars(transactional_stack),
        manager=manager,
        controller=controller,
        grid_engine=grid_engine,
        free_engine=free_engine
    )

@pytest.fixture
def project_stack(transactional_stack):
    """Provides the ProjectStack for integration tests."""
    data_service = DataService(
        model=transactional_stack.model, 
        event_aggregator=transactional_stack.ea
    )
    
    config = transactional_stack.config
    template_dir = Path(config.get_required("paths.layout_templates_dir"))
    max_recent_files = config.get_required("layout.max_recent_files")
    
    controller = ProjectController(
        lifecycle=transactional_stack.model,
        command_manager=transactional_stack.command_manager,
        template_dir=template_dir,
        max_recent_files=max_recent_files,
        event_aggregator=transactional_stack.ea
    )
    
    return ProjectStack(
        **vars(transactional_stack),
        controller=controller,
        data_service=data_service
    )

@pytest.fixture
def style_stack(core_stack):
    """Provides the StyleStack for integration tests."""
    service = StyleService(event_aggregator=core_stack.ea)
    return StyleStack(
        **vars(core_stack),
        service=service
    )

@pytest.fixture
def interaction_stack(core_stack):
    """Provides the InteractionStack for integration tests (Headless)."""
    
    coord_service = CoordinateService()
    tool_service = ToolService(event_aggregator=core_stack.ea)
    
    # Initialize and register the real selection tool
    selection_tool = SelectionTool(
        model=core_stack.model,
        canvas_widget=None, # Headless
        event_aggregator=core_stack.ea
    )
    tool_service.add_tool(selection_tool)
    tool_service.set_active_tool(ToolName.SELECTION.value)
    
    # Mock canvas widget as it requires real Qt/Matplotlib components
    mock_canvas = MagicMock()
    
    canvas_controller = CanvasController(
        view=mock_canvas,
        model=core_stack.model,
        tool_service=tool_service,
        event_aggregator=core_stack.ea
    )
    
    return InteractionStack(
        **vars(core_stack),
        tool_service=tool_service,
        coord_service=coord_service,
        canvas_controller=canvas_controller
    )


# --- Domain Model Fixtures ---

@pytest.fixture
def sample_plot_properties():
    """Provides a complete, versioned PlotProperties tree for integration tests."""
    font = FontProperties(
        family="Arial", 
        style="normal", 
        variant="normal", 
        weight="normal", 
        stretch="normal", 
        size=10
    )
    label = TextProperties(text="Axis Label", color="black", font=font)
    ticks = TickProperties(
        major_size=5.0,
        minor_size=2.0,
        major_width=1.0,
        minor_width=0.5,
        major_pad=3.0,
        minor_pad=3.0,
        direction=TickDirection.OUT,
        color="black",
        labelcolor="black",
        labelsize=10,
        minor_visible=True,
        minor_ndivs=2
    )
    axis = AxisProperties(
        ticks=ticks, 
        margin=0.05,
        autolimit_mode=AutolimitMode.DATA,
        use_offset=True,
        offset_threshold=4,
        scientific_limits=(-4, 5),
        label=label, 
        limits=(0.0, 10.0)
    )
    
    return PlotProperties(
        titles={"center": TextProperties(text="Plot Title", color="black", font=font)},
        coords=Cartesian2DProperties(
            xaxis=axis,
            yaxis=axis,
            spines={
                "left": SpineProperties(True, "black", 1.0, SpinePosition.LEFT),
                "bottom": SpineProperties(True, "black", 1.0, SpinePosition.BOTTOM),
            },
            facecolor="white",
            axis_below=True,
            prop_cycle=["C0", "C1"]
        ),
        legend={},
        artists=[
            LineArtistProperties(
                visible=True,
                zorder=1,
                visuals=LineProperties(
                    linewidth=1.0, 
                    linestyle="-", 
                    color="C0", 
                    marker="None", 
                    markerfacecolor="C0", 
                    markeredgecolor="black", 
                    markeredgewidth=0.5, 
                    markersize=5.0
                ),
            )
        ],
    )

@pytest.fixture
def hydrated_plot_node(sample_plot_properties):
    """Provides a PlotNode with initialized properties."""
    node = PlotNode(name="Hydrated Plot")
    node.plot_properties = sample_plot_properties
    return node
