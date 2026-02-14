import threading
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal


class Debouncer(QObject):
    """
    A utility class to debounce function calls or signal emissions.

    When called multiple times within the specified delay, only the last call
    will result in the function being executed after the delay.
    This is particularly useful for UI events like text input or slider changes
    where rapid changes can lead to performance issues if every change
    triggers an expensive operation.
    """

    debounced = Signal(
        object
    )  # Signal emitted after debounce period, carrying the last argument

    def __init__(self, delay_ms: int = 300, parent: Optional[QObject] = None):
        super().__init__(parent)
        # TODO: Check if I even pass a parent
        self._delay_ms = delay_ms
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._last_args = None
        self._last_kwargs = None

    def debounce(self, *args, **kwargs):
        """
        Call this method to debounce a function execution.
        The function will be executed after `delay_ms` has passed since the last call.
        """
        self._last_args = args
        self._last_kwargs = kwargs
        self._timer.stop()  # Reset the timer on each call
        self._timer.start(self._delay_ms)

    def _on_timeout(self):
        """
        Executed when the timer times out. Emits the debounced signal.
        """
        if self._last_args is not None:
            # Emit a signal that carries the arguments.
            # The receiver can then unpack these arguments and call the target function.
            self.debounced.emit(self._last_args)  # Emitting args directly
        self._last_args = None
        self._last_kwargs = None


class RateLimiter:
    """
    A utility class to rate-limit function calls.

    Ensures that a function is not called more frequently than a specified interval.
    Unlike Debouncer, it executes the function immediately on the first call,
    then ignores subsequent calls until the interval has passed.
    """

    def __init__(self, interval_ms: int):
        self._interval_s = interval_ms / 1000.0
        self._timer = None
        self._lock = threading.Lock()
        self._is_ready = True

    def _reset_ready_state(self):
        with self._lock:
            self._is_ready = True
            self._timer = None

    def limit(self, func, *args, **kwargs):
        """
        Call this method to rate-limit a function execution.
        The function will be executed immediately if the interval has passed.
        """
        with self._lock:
            if self._is_ready:
                self._is_ready = False
                self._timer = threading.Timer(self._interval_s, self._reset_ready_state)
                self._timer.start()
                func(*args, **kwargs)
            else:
                pass  # Ignore call if not ready
