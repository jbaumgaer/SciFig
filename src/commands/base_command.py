import logging


class BaseCommand:
    """
    An abstract base class for all commands in the application.
    A command represents a single, reversible action that modifies the model.
    """

    def __init__(self, description: str):
        self.description = description
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Command initialized: {self.description}")

    def execute(self):
        """Applies the forward action of the command."""
        raise NotImplementedError

    def undo(self):
        """Reverses the action of the command."""
        raise NotImplementedError
