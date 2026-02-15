import logging
from collections import defaultdict
from typing import Callable

from src.shared.events import Events


class EventAggregator:
    """
    A centralized event bus for decoupled communication between application components.

    This service allows objects to publish events and subscribe to them without
    having direct references to each other, following the Publish-Subscribe pattern.
    """

    def __init__(self):
        """Initializes the EventAggregator."""
        self._subscribers: dict[Events, list[Callable]] = defaultdict(list)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("EventAggregator initialized.")

    def subscribe(self, event: Events, handler: Callable[..., any]):
        """
        Subscribes a handler function to a specific event.

        Args:
            event: The event to subscribe to, as defined in the Events enum.
            handler: The callable function to be executed when the event is published.
                     This handler should accept the arguments passed during publication.
        """
        if not isinstance(event, Events):
            self.logger.error(f"Attempted to subscribe to invalid event type: {type(event)}")
            return

        self._subscribers[event].append(handler)
        self.logger.debug(f"Handler {handler.__name__} subscribed to event {event.name}")

    def publish(self, event: Events, *args: any, **kwargs: any):
        """
        Publishes an event, triggering all subscribed handlers.

        Args:
            event: The event to publish, as defined in the Events enum.
            *args: Positional arguments to pass to the event handlers.
            **kwargs: Keyword arguments to pass to the event handlers.
        """
        if not isinstance(event, Events):
            self.logger.error(f"Attempted to publish invalid event type: {type(event)}")
            return

        if event not in self._subscribers:
            self.logger.debug(f"Published event {event.name} with no subscribers.")
            return

        self.logger.info(f"Publishing event: {event.name} with args: {args}, kwargs: {kwargs}")
        for handler in self._subscribers[event]:
            try:
                handler(*args, **kwargs)
            except Exception:
                self.logger.exception(
                    f"Error in handler {handler.__name__} for event {event.name}"
                )
