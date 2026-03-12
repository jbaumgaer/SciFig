import pytest
from unittest.mock import ANY
from src.shared.events import Events
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_types import ArtistType
from src.models.plots.plot_properties import PlotProperties

"""
Style & Theming Stack Integration Tests.
Verifies the 'Theme Hydration' logic using the StyleService.
"""

def test_theme_hydration_on_request(style_stack, node_stack):
    """
    Scenario: A new sparse PlotNode is created. StyleService receives an 
    INITIALIZE_PLOT_THEME_REQUESTED event and populates the node's properties.
    """
    style_s = style_stack.service
    model = node_stack.model
    ea = style_stack.ea
    
    # 1. Load a real style (using the project's default)
    style_s.load_style("configs/default.mplstyle")
    
    # 2. Create a sparse node
    node = PlotNode(name="Sparse")
    model.add_node(node)
    assert node.plot_properties is None
    
    # 3. Act: Request hydration
    ea.publish(Events.INITIALIZE_PLOT_THEME_REQUESTED, node_id=node.id, plot_type=ArtistType.LINE)
    
    # 4. Assert: StyleService published the CHANGE_PLOT_NODE_PROPERTY_REQUESTED event
    ea.publish.assert_any_call(
        Events.CHANGE_PLOT_NODE_PROPERTY_REQUESTED,
        node_id=node.id,
        path="plot_properties",
        value=ANY
    )
    
    # 5. Sociable Assert: NodeController (in node_stack) should have reacted and updated the model
    # Wait, the node_stack uses the SAME event aggregator as style_stack? 
    # Yes, they both share core_stack.ea.
    
    assert isinstance(node.plot_properties, PlotProperties)
    assert node.plot_properties.coords.facecolor == "white" # From default.mplstyle

def test_sparse_hydration_from_template(style_stack):
    """
    Scenario: Reconstruct a property tree from a sparse dictionary (e.g. from a template).
    Verify: Missing values are filled from the current theme.
    """
    style_s = style_stack.service
    style_s.load_style("configs/default.mplstyle")
    
    sparse_overrides = {
        "artists": [{"artist_type": "line", "visuals": {"color": "red"}}]
    }
    
    # Act
    props = style_s.create_properties_from_sparse(sparse_overrides)
    
    # Assert
    assert props.artists[0].visuals.color == "red"
    # Verify that un-specified fields were filled from default.mplstyle
    assert props.coords.facecolor == "white" 
    assert props.coords.xaxis.label.color == "black"
