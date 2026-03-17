from typing import Optional, Any
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events

class MacroCommand(BaseCommand):
    """
    A generic command that executes a list of sub-commands as a single atomic action.
    Supports an optional completion event to notify the system after the batch is done.
    """

    def __init__(
        self, 
        description: str, 
        commands: list[BaseCommand], 
        event_aggregator: EventAggregator,
        completion_event: Optional[Events] = None,
        completion_kwargs: Optional[dict[str, Any]] = None
    ):
        super().__init__(description, event_aggregator)
        self.commands = commands
        self.completion_event = completion_event
        self.completion_kwargs = completion_kwargs or {}

    def execute(self, publish: bool = True):
        """
        Executes all sub-commands. 
        Intermediate sub-commands are executed with publish=False to avoid redundant redraws.
        """
        for cmd in self.commands:
            cmd.execute(publish=False)
            
        if publish and self.completion_event:
            self._event_aggregator.publish(self.completion_event, **self.completion_kwargs)

    def undo(self, publish: bool = True):
        """Reverses all sub-commands in reverse order."""
        for cmd in reversed(self.commands):
            cmd.undo(publish=False)

        if publish and self.completion_event:
            self._event_aggregator.publish(self.completion_event, **self.completion_kwargs)
