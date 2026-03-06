import pytest
import logging
from unittest.mock import MagicMock
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


@pytest.fixture
def aggregator():
    """Provides a fresh, real EventAggregator instance."""
    return EventAggregator()


class TestEventAggregator:
    """
    Unit tests for the EventAggregator service.
    Verifies the decoupled communication mechanism via the pub-sub pattern.
    """

    # --- Subscription & Publication ---

    def test_publish_triggers_subscribed_handler(self, aggregator):
        """Verifies that a basic subscription results in a call upon publication."""
        handler = MagicMock()
        handler.__name__ = "mock_handler"
        aggregator.subscribe(Events.SELECTION_CHANGED, handler)
        
        aggregator.publish(Events.SELECTION_CHANGED, ["id1", "id2"])
        
        handler.assert_called_once_with(["id1", "id2"])

    def test_publish_notifies_multiple_subscribers(self, aggregator):
        """Verifies that all handlers for a specific event are executed."""
        handler1 = MagicMock()
        handler1.__name__ = "mock_handler_1"
        handler2 = MagicMock()
        handler2.__name__ = "mock_handler_2"
        
        aggregator.subscribe(Events.PROJECT_OPENED, handler1)
        aggregator.subscribe(Events.PROJECT_OPENED, handler2)
        
        aggregator.publish(Events.PROJECT_OPENED, "test.sci")
        
        handler1.assert_called_once_with("test.sci")
        handler2.assert_called_once_with("test.sci")

    # --- Argument Passing ---

    def test_publish_passes_positional_and_keyword_arguments(self, aggregator):
        """Verifies correct forwarding of complex payloads to handlers."""
        handler = MagicMock()
        handler.__name__ = "mock_handler"
        aggregator.subscribe(Events.CHANGE_PLOT_COMPONENT_REQUESTED, handler)
        
        aggregator.publish(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED, 
            node_id="p1", 
            path="coords.xaxis.margin", 
            value=0.2
        )
        
        handler.assert_called_once_with(
            node_id="p1", 
            path="coords.xaxis.margin", 
            value=0.2
        )

    # --- Isolation & Error Handling ---

    def test_publish_to_no_subscribers_is_safe(self, aggregator):
        """Ensures that publishing an event with no listeners doesn't raise errors."""
        # This should execute without exception
        aggregator.publish(Events.SAVE_PROJECT_REQUESTED)

    def test_handler_exception_isolation(self, aggregator, caplog):
        """
        Verifies that a failure in one handler does not prevent other handlers 
        from executing.
        """
        handler_ok = MagicMock()
        handler_ok.__name__ = "handler_ok"
        handler_fail = MagicMock(side_effect=Exception("Handler failure"))
        handler_fail.__name__ = "handler_fail"
        
        aggregator.subscribe(Events.SELECTION_CHANGED, handler_fail)
        aggregator.subscribe(Events.SELECTION_CHANGED, handler_ok)
        
        # Publish with logging captured
        with caplog.at_level(logging.ERROR):
            aggregator.publish(Events.SELECTION_CHANGED, ["p1"])
        
        # Verify both were called despite the error in the first one
        handler_fail.assert_called_once()
        handler_ok.assert_called_once()
        
        # Verify the error was logged
        assert "Error in handler" in caplog.text
        assert "Handler failure" in caplog.text

    # --- Validation Logic ---

    def test_invalid_event_type_logs_error(self, aggregator, caplog):
        """Verifies that using non-enum types for events is caught and logged."""
        handler = MagicMock()
        handler.__name__ = "mock_handler"
        
        with caplog.at_level(logging.ERROR):
            # 1. Test invalid subscribe
            aggregator.subscribe("NOT_AN_ENUM", handler)
            assert "Attempted to subscribe to invalid event type" in caplog.text
            
            # 2. Test invalid publish
            aggregator.publish("NOT_AN_ENUM")
            assert "Attempted to publish invalid event type" in caplog.text

    # --- State Tracking ---

    def test_publish_count_increment(self, aggregator):
        """Verifies that the internal event counter tracks publications correctly."""
        # Subscribe a dummy handler so publish logic runs fully
        handler = MagicMock()
        handler.__name__ = "dummy"
        aggregator.subscribe(Events.SELECTION_CHANGED, handler)

        # Initial state: count not set until first publish
        aggregator.publish(Events.SELECTION_CHANGED, [])
        assert aggregator._publish_count == 1
        
        aggregator.publish(Events.SELECTION_CHANGED, [])
        assert aggregator._publish_count == 2
