import pytest
from src.shared.events import Events
from src.models.nodes.plot_node import PlotNode
from src.services.commands.group_nodes_command import GroupNodesCommand

"""
Transactional Node Stack Integration Tests.
Verifies the 'Transactional Integrity' of the Scene Graph using 
the NodeController, PropertyService, and CommandManager.
"""

def assert_domain_fidelity(node, initial_dict):
    """
    Compares a node's state to an initial dictionary, 
    ignoring version numbers which are expected to increment even on undo.
    """
    current_dict = node.to_dict()
    # Remove version keys for deep domain comparison
    for d in [current_dict, initial_dict]:
        d.pop("property_version", None)
        d.pop("geometry_version", None)
        # Recursively handle children if needed
        for child in d.get("children", []):
            child.pop("property_version", None)
            child.pop("geometry_version", None)
            
    assert current_dict == initial_dict

def test_property_change_transaction(node_stack, hydrated_plot_node):
    """
    Scenario: Use NodeController to change a plot's property.
    Verify: Model updates, Command is created, and Events are published.
    """
    stack = node_stack
    node = hydrated_plot_node
    stack.model.add_node(node)
    
    # --- Action 1: Simple Property (name) ---
    stack.controller._on_rename_node_request(node.id, "New Name")
    
    assert node.name == "New Name"
    assert len(stack.command_manager._undo_stack) == 1
    # Verify event publication (EA is a spy)
    stack.ea.publish.assert_any_call(
        Events.PLOT_NODE_PROPERTY_CHANGED, 
        node_id=node.id, 
        path="name", 
        new_value="New Name"
    )

    # --- Action 2: Nested Property (axis limits) ---
    new_limits = (10.0, 20.0)
    stack.controller._on_generic_property_change_request(node.id, "coords.xaxis.limits", new_limits)
    
    assert node.plot_properties.coords.xaxis.limits == new_limits
    assert len(stack.command_manager._undo_stack) == 2
    stack.ea.publish.assert_any_call(
        Events.PLOT_NODE_PROPERTY_CHANGED, 
        node_id=node.id, 
        path="coords.xaxis.limits", 
        new_value=new_limits
    )

def test_undo_redo_fidelity(node_stack, hydrated_plot_node):
    """
    Scenario: Perform a sequence of complex changes, then undo and redo.
    Verify: Domain data is restored perfectly, despite version increments.
    """
    stack = node_stack
    node = hydrated_plot_node
    stack.model.add_node(node)
    
    initial_state = node.to_dict()
    
    # Perform changes
    stack.controller._on_rename_node_request(node.id, "Changed")
    stack.controller._on_node_visibility_request(node.id, False)
    stack.controller._on_generic_property_change_request(node.id, "coords.facecolor", "red")
    
    assert node.name == "Changed"
    
    # Undo all
    stack.command_manager.undo() # undo facecolor
    stack.command_manager.undo() # undo visibility
    stack.command_manager.undo() # undo name
    
    # Use helper to ignore versioning increments
    assert_domain_fidelity(node, initial_state)
    
    # Redo all
    stack.command_manager.redo()
    stack.command_manager.redo()
    stack.command_manager.redo()
    
    assert node.name == "Changed"
    assert node.visible is False
    assert node.plot_properties.coords.facecolor == "red"

def test_bypass_pattern_integrity(node_stack, hydrated_plot_node):
    """
    Scenario: Use NodeController.reconcile_node_property (the 'Bypass' path).
    Verify: Model updates silently without affecting history.
    """
    stack = node_stack
    node = hydrated_plot_node
    stack.model.add_node(node)
    
    initial_undo_size = len(stack.command_manager._undo_stack)
    
    # Act: Reconcile a property (simulating a Matplotlib sync)
    stack.controller.reconcile_node_property(node.id, "visible", False)
    
    assert node.visible is False
    # History must remain untouched
    assert len(stack.command_manager._undo_stack) == initial_undo_size
    
    # Verify specialized event publication
    stack.ea.publish.assert_any_call(
        Events.PLOT_NODE_PROPERTY_RECONCILED, 
        node_id=node.id, 
        path="visible", 
        new_value=False
    )

def test_group_lifecycle(node_stack):
    """
    Scenario: Select multiple PlotNodes and use a command to group them.
    Note: Tests the underlying GroupNodesCommand directly as the controller 
    implementation is still a stub.
    """
    
    stack = node_stack
    p1 = PlotNode(name="P1")
    p2 = PlotNode(name="P2")
    stack.model.add_node(p1)
    stack.model.add_node(p2)
    
    # Act: Execute Group Command
    cmd = GroupNodesCommand(stack.model, stack.ea, [p1.id, p2.id], group_name="TestGroup")
    stack.command_manager.execute_command(cmd)
    
    # Verify Structure
    assert len(stack.model.scene_root.children) == 1
    group = stack.model.scene_root.children[0]
    assert group.name == "TestGroup"
    assert len(group.children) == 2
    
    # Verify Undo
    stack.command_manager.undo()
    assert len(stack.model.scene_root.children) == 2
    assert p1.parent == stack.model.scene_root
    assert p2.parent == stack.model.scene_root
