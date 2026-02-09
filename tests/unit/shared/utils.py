from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject

from src.shared.utils import Debouncer


# Fixture for a simple QObject to use as parent, if needed
@pytest.fixture
def q_object_parent():
    return QObject()

class TestDebouncer:
    def test_debouncer_single_call(self, qtbot, q_object_parent):
        """
        Test that a single call to debounce triggers the debounced signal
        after the delay.
        """
        debouncer = Debouncer(delay_ms=100, parent=q_object_parent)
        mock_slot = MagicMock()
        debouncer.debounced.connect(mock_slot)

        debouncer.debounce("test_arg", kwarg="test_kwarg")
        mock_slot.assert_not_called() # Should not be called immediately

        qtbot.wait(150) # Wait longer than the debounce delay
        mock_slot.assert_called_once_with(("test_arg",), {"kwarg": "test_kwarg"})

    def test_debouncer_multiple_rapid_calls(self, qtbot, q_object_parent):
        """
        Test that multiple rapid calls to debounce only trigger the debounced signal
        once with the arguments of the last call.
        """
        debouncer = Debouncer(delay_ms=100, parent=q_object_parent)
        mock_slot = MagicMock()
        debouncer.debounced.connect(mock_slot)

        debouncer.debounce("first_call")
        debouncer.debounce("second_call", value=2)
        debouncer.debounce("last_call", final=True)
        mock_slot.assert_not_called() # Should not be called immediately

        qtbot.wait(150) # Wait longer than the debounce delay
        mock_slot.assert_called_once_with(("last_call",), {"final": True})

    def test_debouncer_calls_separated_by_delay(self, qtbot, q_object_parent):
        """
        Test that calls separated by more than the delay each trigger their own signal.
        """
        debouncer = Debouncer(delay_ms=100, parent=q_object_parent)
        mock_slot = MagicMock()
        debouncer.debounced.connect(mock_slot)

        debouncer.debounce("call_1")
        qtbot.wait(150)
        mock_slot.assert_called_once_with(("call_1",), {})
        mock_slot.reset_mock()

        debouncer.debounce("call_2")
        qtbot.wait(150)
        mock_slot.assert_called_once_with(("call_2",), {})

    def test_debouncer_no_calls_after_debounce(self, qtbot, q_object_parent):
        """
        Test that no signal is emitted if no debounce calls are made.
        """
        debouncer = Debouncer(delay_ms=100, parent=q_object_parent)
        mock_slot = MagicMock()
        debouncer.debounced.connect(mock_slot)

        qtbot.wait(150) # Just wait
        mock_slot.assert_not_called()

# Note: RateLimiter is not a QObject and uses threading.Timer, so it's tested differently.
# However, the prompt only asks for Debouncer utility test stub for now.
