class BaseCommand:
    """
    An abstract base class for all commands in the application.
    A command represents a single, reversible action that modifies the model.
    """

    def execute(self):
        """Applies the forward action of the command."""
        raise NotImplementedError

    def undo(self):
        """Reverses the action of the command."""
        raise NotImplementedError
