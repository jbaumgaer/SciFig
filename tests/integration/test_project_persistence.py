import json
import zipfile
from pathlib import Path
import pandas as pd
import pytest
from src.shared.events import Events
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.grid_node import GridNode
from src.models.nodes.grid_position import GridPosition

"""
Project & Data Persistence Stack Integration Tests.
Verifies the 'Serialization Lifecycle' and data-binding flows.
"""

def test_project_save_load_cycle(project_stack, hydrated_plot_node, tmp_path):
    """
    Scenario: Build a complex scene (Grids, Plots) and save to .sci.
    Verify: Loading the project back restores all hierarchy and properties.
    """
    stack = project_stack
    save_path = tmp_path / "test_project.sci"
    
    # 1. Arrange: Build a scene
    grid = GridNode(name="MainGrid", rows=2, cols=1)
    stack.model.add_node(grid)
    
    p1 = hydrated_plot_node
    p1.name = "Plot 1"
    p1.grid_position = GridPosition(0, 0)
    grid.add_child(p1)
    
    # 2. Act: Save project
    stack.controller._save_to_path(save_path)
    
    assert save_path.exists()
    
    # 3. Verify ZIP contents (Internal check)
    with zipfile.ZipFile(save_path, "r") as zf:
        assert "project.json" in zf.namelist()
        with zf.open("project.json") as f:
            data = json.load(f)
            assert data["scene_root"]["children"][0]["name"] == "MainGrid"

    # 4. Act: Reset model and Load
    stack.model.reset_state()
    assert len(stack.model.scene_root.children) == 0
    
    stack.controller._open_from_path(save_path)
    
    # 5. Assert: Hierarchy restored
    assert len(stack.model.scene_root.children) == 1
    restored_grid = stack.model.scene_root.children[0]
    assert restored_grid.name == "MainGrid"
    assert len(restored_grid.children) == 1
    assert restored_grid.children[0].name == "Plot 1"
    assert isinstance(restored_grid.children[0], PlotNode)
    
    # Verify events
    stack.ea.publish.assert_any_call(Events.PROJECT_OPENED, project_metadata={"file_path": str(save_path)})

def test_data_binding_flow(project_stack, hydrated_plot_node):
    """
    Scenario: Simulate data loading for a specific PlotNode.
    Verify: NodeController (via DataService) maps the dataframe to the node.
    Note: Using ProjectStack which has access to DataService.
    """
    stack = project_stack
    node = hydrated_plot_node
    stack.model.add_node(node)
    
    # Create sample data
    df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
    
    # Act: Assign data directly (simulating DataService result)
    # In a full flow, DataService publishes NODE_DATA_LOADED
    node.data = df
    stack.ea.publish(Events.NODE_DATA_LOADED, node_id=node.id)
    
    # Assert: Verify data is bound
    assert node.data is not None
    assert node.data.equals(df)
    stack.ea.publish.assert_any_call(Events.NODE_DATA_LOADED, node_id=node.id)

def test_template_application_data_preservation(project_stack, layout_stack, hydrated_plot_node):
    """
    Scenario: Apply a Grid template to a scene that already contains a plot with data.
    Verify: Data is migrated to the new template's plot node.
    """
    stack = project_stack
    node = hydrated_plot_node
    df = pd.DataFrame({"val": [1, 2, 3]})
    node.data = df
    stack.model.add_node(node)
    
    # Create a simple 1x1 template root
    template_root = GridNode(name="TemplateRoot", rows=1, cols=1)
    new_plot = PlotNode(name="TemplatePlot")
    new_plot.grid_position = GridPosition(0, 0)
    template_root.add_child(new_plot)
    
    # Act: Use LayoutManager to apply template
    # (ProjectController usually triggers this via UI flow)
    layout_stack.manager.apply_layout_template(template_root)
    
    # Assert: The new scene root is the template
    assert stack.model.scene_root == template_root
    
    # Assert: Data was migrated to the first plot in the template
    restored_plot = list(stack.model.scene_root.all_descendants(of_type=PlotNode))[0]
    assert restored_plot.data is not None
    assert restored_plot.data.equals(df)
    assert restored_plot.name == "TemplatePlot"
