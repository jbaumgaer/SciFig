import pytest
from unittest.mock import MagicMock
from src.services.commands.apply_grid_command import ApplyGridCommand
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.grid_node import GridNode
from src.models.layout.layout_config import GridConfig, Margins, Gutters
from src.shared.events import Events

@pytest.fixture
def mock_event_aggregator():
    return MagicMock()

@pytest.fixture
def mock_layout_manager():
    return MagicMock()

@pytest.fixture
def model(mock_event_aggregator):
    return ApplicationModel(event_aggregator=mock_event_aggregator, figure_size=(20, 20))

def test_apply_grid_command_execute(model, mock_event_aggregator, mock_layout_manager):
    """Verifies that executing the command moves plots into a new GridNode."""
    p1 = PlotNode(id="p1", name="P1", parent=model.scene_root)
    p2 = PlotNode(id="p2", name="P2", parent=model.scene_root)
    
    config = GridConfig(2, 1, [1,1], [1], Margins(0,0,0,0), Gutters([],[]))
    command = ApplyGridCommand(model, mock_event_aggregator, mock_layout_manager, config)
    
    command.execute()
    
    # 1. Verify GridNode created
    grids = [n for n in model.scene_root.children if isinstance(n, GridNode)]
    assert len(grids) == 1
    grid = grids[0]
    
    # 2. Verify plots moved to GridNode
    assert p1.parent == grid
    assert p2.parent == grid
    assert p1.grid_position is not None
    assert p2.grid_position is not None
    
    # 3. Verify sync triggered
    mock_layout_manager.sync_layout.assert_called_once()

def test_apply_grid_command_undo(model, mock_event_aggregator, mock_layout_manager):
    """Verifies that undoing the command restores the original flat hierarchy."""
    p1 = PlotNode(id="p1", parent=model.scene_root)
    original_parent = model.scene_root
    
    config = GridConfig(1, 1, [1], [1], Margins(0,0,0,0), Gutters([],[]))
    command = ApplyGridCommand(model, mock_event_aggregator, mock_layout_manager, config)
    
    command.execute()
    command.undo()
    
    # 1. Verify Plot moved back to root
    assert p1.parent == original_parent
    assert p1.grid_position is None
    
    # 2. Verify GridNode was removed
    grids = [n for n in model.scene_root.children if isinstance(n, GridNode)]
    assert len(grids) == 0
