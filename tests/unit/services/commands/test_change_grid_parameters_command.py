import pytest
from unittest.mock import MagicMock
from src.services.commands.change_grid_parameters_command import ChangeGridParametersCommand
from src.models.application_model import ApplicationModel
from src.models.nodes.grid_node import GridNode
from src.models.layout.layout_config import GridConfig, Margins, Gutters

@pytest.fixture
def mock_event_aggregator():
    return MagicMock()

@pytest.fixture
def mock_layout_manager():
    return MagicMock()

@pytest.fixture
def model(mock_event_aggregator):
    m = ApplicationModel(event_aggregator=mock_event_aggregator, figure_size=(20, 20))
    # Add a root grid
    GridNode(parent=m.scene_root, id="root_grid", rows=1, cols=1)
    return m

def test_change_grid_parameters_execute(model, mock_event_aggregator, mock_layout_manager):
    """Verifies that the command synchronizes config values to the GridNode."""
    grid = model.get_active_grid()
    
    new_config = GridConfig(
        rows=3, cols=3, 
        row_ratios=[1,1,1], col_ratios=[1,1,1], 
        margins=Margins(2,2,2,2), 
        gutters=Gutters([1,1], [1,1])
    )
    
    command = ChangeGridParametersCommand(model, mock_event_aggregator, mock_layout_manager, MagicMock(), new_config)
    command.execute()
    
    assert grid.rows == 3
    assert grid.margins.top == 2
    assert grid.gutters.hspace == [1, 1]
    mock_layout_manager.sync_layout.assert_called_once()

def test_change_grid_parameters_undo(model, mock_event_aggregator, mock_layout_manager):
    """Verifies that undo restores the previous GridNode state."""
    grid = model.get_active_grid()
    grid.rows = 5
    
    old_config = GridConfig(5, 5, [1]*5, [1]*5, Margins(0,0,0,0), Gutters([],[]))
    new_config = GridConfig(2, 2, [1,1], [1,1], Margins(1,1,1,1), Gutters([0.5], [0.5]))
    
    command = ChangeGridParametersCommand(model, mock_event_aggregator, mock_layout_manager, old_config, new_config)
    
    command.execute()
    assert grid.rows == 2
    
    command.undo()
    assert grid.rows == 5
    assert mock_layout_manager.sync_layout.call_count == 2 # Once for execute, once for undo
