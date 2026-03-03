from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator

class MacroCommand(BaseCommand):
    """
    A generic command that executes a list of sub-commands as a single atomic action.
    This command does not publish its own events, allowing specialized subclasses 
    to handle orchestration and batch notifications.
    """

    def __init__(
        self, 
        description: str, 
        commands: list[BaseCommand], 
        event_aggregator: EventAggregator
    ):
        super().__init__(description, event_aggregator)
        self.commands = commands

    def execute(self, publish: bool = True):
        """
        Executes all sub-commands. 
        Intermediate sub-commands are executed with publish=False to avoid redundant redraws.
        """
        for cmd in self.commands:
            # Sub-commands within a macro should generally NOT publish individual events
            cmd.execute(publish=False)
            
        # The MacroCommand itself doesn't publish anything. 
        # Specialized subclasses (like ApplyDataToNodeCommand) will handle the final publication.

    def undo(self, publish: bool = True):
        """Reverses all sub-commands in reverse order."""
        for cmd in reversed(self.commands):
            cmd.undo(publish=False)
