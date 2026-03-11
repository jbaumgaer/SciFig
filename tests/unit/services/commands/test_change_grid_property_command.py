import pytest
from unittest.mock import MagicMock
from src.services.commands.change_grid_property_command import ChangeGridPropertyCommand
from src.models.nodes.grid_node import GridNode
from src.services.property_service import PropertyService
from src.shared.events import Events

@pytest.fixture
def mock_event_aggregator():
    return MagicMock()

@pytest.fixture
def mock_property_service():
    return PropertyService() # Real service is stateless and easy to use

def test_change_grid_property_execute(mock_event_aggregator, mock_property_service):
    """Verifies that the command updates the grid and publishes events."""
    grid = GridNode(rows=1, cols=1)
    grid.rows = 1
    
    command = ChangeGridPropertyCommand(
        grid_node=grid,
        path="rows",
        new_value=5,
        event_aggregator=mock_event_aggregator,
        property_service=mock_property_service
    )
    
    command.execute()
    
    assert grid.rows == 5
    mock_event_aggregator.publish.assert_any_call(
        Events.GRID_COMPONENT_CHANGED,
        node_id=grid.id,
        path="rows",
        new_value=5
    )
    mock_event_aggregator.publish.assert_any_call(Events.SCENE_GRAPH_CHANGED)

def test_change_grid_property_undo(mock_event_aggregator, mock_property_service):
    """Verifies that undo restores the previous value."""
    grid = GridNode(rows=2, cols=2)
    command = ChangeGridPropertyCommand(
        grid, "rows", 5, mock_event_aggregator, mock_property_service
    )
    
    command.execute()
    assert grid.rows == 5
    
    command.undo()
    assert grid.rows == 2
    
    # Verify undo published event with None for new_value (standard for reverts)
    mock_event_aggregator.publish.assert_any_call(
        Events.GRID_COMPONENT_CHANGED,
        node_id=grid.id,
        path="rows",
        new_value=None
    )
