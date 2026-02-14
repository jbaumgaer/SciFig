from PySide6.QtCore import Signal, QPointF

class CanvasEvents:
    @property
    def file_dropped(self) -> Signal: ... # Emits (str, QPointF)

    @property
    def mouse_press_event(self) -> Signal: ... # Emits a Matplotlib event object

    @property
    def mouse_move_event(self) -> Signal: ...

    @property
    def mouse_release_event(self) -> Signal: ...