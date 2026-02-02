import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit  # Correct import for QLineEdit

# Import core application components
from main import setup_application
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    PlotMapping,
    PlotProperties,
)


@pytest.fixture
def app_context(qtbot):
    """
    A pytest fixture that sets up the entire application stack and provides
    access to its core components. This is an integration-level fixture.
    """
    context = setup_application()

    # The qtbot.addWidget function ensures that the widget is properly closed
    # at the end of the test, preventing test interference.
    qtbot.addWidget(context["view"])

    # Add a default plot to the scene for testing
    default_plot = PlotNode()
    default_plot.plot_properties = PlotProperties(
        title="Default Title",
        xlabel="",
        ylabel="",
        plot_mapping=PlotMapping(x=None, y=[]),
        axes_limits=AxesLimits(xlim=(None, None), ylim=(None, None)),
    )
    context["model"].add_node(default_plot)

    return context


def test_properties_view_updates_model_on_title_change(app_context, qtbot):
    """
    An integration test to verify that changing the 'Title' QLineEdit in the
    PropertiesView correctly updates the title property in the model.
    """
    # Arrange: Get components from the application context
    model = app_context["model"]
    view = app_context["view"]

    # Find the PlotNode we added in the fixture
    plot_node = model.scene_root.children[0]

    # 1. Select the plot node to trigger the PropertiesView to build its UI
    model.set_selection([plot_node])

    # 2. Find the 'Title' QLineEdit in the PropertiesView using its object name
    title_edit = view.properties_view.findChild(
        QLineEdit, "title_edit"
    )  # Use QLineEdit directly
    assert (
        title_edit is not None
    ), "Could not find the 'title_edit' QLineEdit in the PropertiesView"

    # 3. Simulate user typing a new title and pressing Enter
    new_title = "My Test Title"
    title_edit.clear()
    qtbot.keyClicks(title_edit, new_title)
    qtbot.keyPress(title_edit, Qt.Key_Enter)

    # Assert: Check that the model's plot_properties were updated
    assert plot_node.plot_properties.title == new_title
