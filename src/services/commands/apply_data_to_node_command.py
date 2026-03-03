from typing import Any
import pandas as pd
from src.models.nodes.plot_node import PlotNode
from src.services.commands.macro_command import MacroCommand
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events

class ApplyDataToNodeCommand(MacroCommand):
    """
    A specialized command that batches property and data updates into a single transaction.
    Triggers exactly one redraw at the end.
    """

    def __init__(
        self, 
        node: PlotNode, 
        commands: list[BaseCommand],
        event_aggregator: EventAggregator
    ):
        description = f"Apply data and mapping to node '{node.name}'"
        super().__init__(description, commands, event_aggregator)
        self.node = node

    def execute(self, publish: bool = True):
        """
        Executes sub-commands silently and publishes a single notification 
        at the end to trigger a redraw.
        """
        # Execute all property changes silently
        super().execute(publish=False)

        # Publish exactly one event to notify the system (and trigger the renderer)
        if publish:
            self._event_aggregator.publish(
                Events.PLOT_COMPONENT_CHANGED, 
                node_id=self.node.id,
                path="data",
                new_value=self.node.data
            )

    def undo(self, publish: bool = True):
        """
        Reverses all sub-commands silently and publishes a single notification 
        at the end to trigger a redraw.
        """
        # Revert all changes silently
        super().undo(publish=False)

        # Trigger a final redraw
        if publish:
            self._event_aggregator.publish(
                Events.PLOT_COMPONENT_CHANGED, 
                node_id=self.node.id,
                path="data",
                new_value=self.node.data
            )
