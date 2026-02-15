import logging

from src.models import ApplicationModel
from src.services.commands.base_command import BaseCommand


class CommandManager:
    """
    Manages the execution, undo, and redo of commands.
    The model itself is responsible for emitting signals when its state changes.
    TODO: The command manager somehow doesn't undo things like plot changes anymore
    """

    def __init__(self, model: ApplicationModel):
        self.model = model
        self._undo_stack: list[BaseCommand] = []
        self._redo_stack: list[BaseCommand] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("CommandManager initialized.")

    def execute_command(self, command: BaseCommand):
        """
        Executes a new command and adds it to the undo stack.
        This clears the redo stack.
        """
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()
        self.model.modelChanged.emit() 
        self.logger.info(
            f"Executed {type(command).__name__}, "
            f"Undo stack size: {len(self._undo_stack)}"
        )

    def undo(self):
        """
        Undoes the most recent command and moves it to the redo stack.
        """
        if not self._undo_stack:
            self.logger.info("Undo stack is empty. Nothing to undo.")
            return

        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        self.model.modelChanged.emit() 
        self.logger.info(
            f"Undid {type(command).__name__}, Redo stack size: {len(self._redo_stack)}"
        )

    def redo(self):
        """
        Redoes the most recently undone command.
        """
        if not self._redo_stack:
            self.logger.info("Redo stack is empty. Nothing to redo.")
            return

        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        self.model.modelChanged.emit() 
        self.logger.info(
            f"Redid {type(command).__name__}, Undo stack size: {len(self._undo_stack)}"
        )
