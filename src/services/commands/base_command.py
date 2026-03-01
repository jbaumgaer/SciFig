import logging

from src.services.event_aggregator import EventAggregator


class BaseCommand:
    """
    An abstract base class for all commands in the application.
    A command represents a single, reversible action that modifies the model.
    """

    def __init__(self, description: str, event_aggregator: EventAggregator):
        self.description = description
        self._event_aggregator = event_aggregator
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Command initialized: {self.description}")

    def execute(self):
        """Applies the forward action of the command."""
        raise NotImplementedError

    def undo(self):
        """Reverses the action of the command."""
        raise NotImplementedError
