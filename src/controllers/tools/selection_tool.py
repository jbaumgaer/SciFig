from src.models import ApplicationModel

from .base_tool import BaseTool


class SelectionTool(BaseTool):
    """
    A tool for selecting, deselecting, and (eventually) moving nodes.
    """

    def __init__(self, model: ApplicationModel, canvas):
        super().__init__(model, canvas)

    def activate(self):
        print("SelectionTool activated")

    def deactivate(self):
        print("SelectionTool deactivated")

    def on_mouse_press(self, event):
        """Handles single clicks to select or deselect nodes."""
        # Ignore clicks outside of any axes
        if event.xdata is None or event.ydata is None:
            # Deselect if clicking outside
            self.model.set_selection([])
            return

        # Use v2 hit-testing
        fig_coords = self.canvas.figure.transFigure.inverted().transform(
            (event.x, event.y)
        )
        node_hit = self.model.get_node_at(fig_coords)

        if event.dblclick:
            # The double-click logic to open the dialog is still in the old
            # CanvasController for now. We will migrate it later.
            pass
        else:
            if node_hit:
                self.model.set_selection([node_hit])
            else:
                self.model.set_selection([])

    def on_mouse_move(self, event):
        # To be implemented later (for dragging)
        pass

    def on_mouse_release(self, event):
        # To be implemented later (for dragging)
        pass
