from PySide6.QtCore import QObject


class BaseTool(QObject):
    """
    A base class for all tools that can be active on the canvas.
    Inherits from QObject for Qt's signal/slot mechanism.
    Methods that should be abstract raise NotImplementedError.
    """

    def __init__(self, model, canvas):
        super().__init__()
        self.model = model
        self.canvas = canvas

    def activate(self):
        """Called when the tool becomes active."""
        raise NotImplementedError

    def deactivate(self):
        """Called when the tool becomes inactive."""
        raise NotImplementedError

    def on_mouse_press(self, event):
        """Handles the mouse press event from the Matplotlib canvas."""
        raise NotImplementedError

    def on_mouse_move(self, event):
        """Handles the mouse move event from the Matplotlib canvas."""
        raise NotImplementedError

    def on_mouse_release(self, event):
        """Handles the mouse release event from the Matplotlib canvas."""
        raise NotImplementedError
