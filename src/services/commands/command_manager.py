import logging

from src.models import ApplicationModel
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


class CommandManager:
    """
    Manages the execution, undo, and redo of commands.
    It is also responsible for managing the application's 'dirty' state
    and publishing changes via the EventAggregator.
    """

    def __init__(self, model: ApplicationModel, event_aggregator: EventAggregator):
        self.model = model
        self._event_aggregator = event_aggregator
        self._undo_stack: list[BaseCommand] = []
        self._redo_stack: list[BaseCommand] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("CommandManager initialized.")

    def execute_command(self, command: BaseCommand):
        """
        Executes a new command, adds it to the undo stack, and marks the model
        as dirty. This clears the redo stack.
        """
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()
        
        self.model.set_dirty(True)
        self._event_aggregator.publish(Events.PROJECT_IS_DIRTY_CHANGED, is_dirty=True)

        self.logger.info(
            f"Executed {type(command).__name__}, "
            f"Undo stack size: {len(self._undo_stack)}"
        )

    def undo(self):
        """
        Undoes the most recent command and moves it to the redo stack.
        If the undo stack becomes empty, the model is considered clean.
        """
        if not self._undo_stack:
            self.logger.info("Undo stack is empty. Nothing to undo.")
            return

        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        
        if not self._undo_stack:
            self.model.set_dirty(False)
            self._event_aggregator.publish(Events.PROJECT_IS_DIRTY_CHANGED, is_dirty=False)

        self.logger.info(
            f"Undid {type(command).__name__}, Redo stack size: {len(self._redo_stack)}"
        )

    def redo(self):
        """
        Redoes the most recently undone command and marks the model as dirty.
        """
        if not self._redo_stack:
            self.logger.info("Redo stack is empty. Nothing to redo.")
            return

        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        
        self.model.set_dirty(True)
        self._event_aggregator.publish(Events.PROJECT_IS_DIRTY_CHANGED, is_dirty=True)

        self.logger.info(
            f"Redid {type(command).__name__}, Undo stack size: {len(self._undo_stack)}"
        )
