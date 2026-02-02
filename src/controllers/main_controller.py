from src.models import ApplicationModel
from src.models.nodes import PlotNode


class MainController:
    """
    Manages application-level logic and orchestrates the other components.
    Connects main window UI actions to model-updating logic.
    """

    def __init__(self, model: ApplicationModel, view):  # view is a MainWindow
        self.model = model
        self.view = view

        # Connect UI element signals to controller slots
        self.view.new_layout_action.triggered.connect(self.create_new_layout)

    def create_new_layout(self):
        """
        Clears the scene and populates it with new PlotNodes in a grid layout.
        """
        # The dialog implementation will be added in a future step.
        # For now, we will hardcode a 2x2 layout for demonstration.
        print("Creating a default 2x2 layout.")
        rows, cols = 2, 2

        self.model.clear_scene()

        margin, gutter = 0.1, 0.08
        plot_width = (1 - 2 * margin - (cols - 1) * gutter) / cols
        plot_height = (1 - 2 * margin - (rows - 1) * gutter) / rows

        for r in range(rows):
            for c in range(cols):
                left = margin + c * (plot_width + gutter)
                bottom = margin + (rows - 1 - r) * (plot_height + gutter)

                plot_node = PlotNode(name=f"Subplot {r*cols + c + 1}")
                plot_node.geometry = (left, bottom, plot_width, plot_height)


                # model.add_node emits the signal, so no need for an extra emit here
                self.model.add_node(plot_node)
