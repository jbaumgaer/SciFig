import pytest
from unittest.mock import MagicMock
from src.services.commands.command_manager import CommandManager
from src.services.commands.base_command import BaseCommand
from src.shared.events import Events


class MockCommand(BaseCommand):
    """A minimal command mock for testing the CommandManager."""
    def __init__(self):
        self.execute_called = 0
        self.undo_called = 0

    def execute(self):
        self.execute_called += 1

    def undo(self):
        self.undo_called += 1


@pytest.fixture
def command_manager(mock_application_model, mock_event_aggregator):
    """Provides a CommandManager instance."""
    return CommandManager(model=mock_application_model, event_aggregator=mock_event_aggregator)


class TestCommandManager:
    """
    Unit tests for CommandManager.
    Verifies undo/redo stack logic and dirty state management.
    """

    def test_execute_command_triggers_execution_and_dirty_state(self, command_manager, mock_application_model, mock_event_aggregator):
        """Verifies that executing a command updates the stack and model state."""
        cmd = MockCommand()
        
        command_manager.execute_command(cmd)
        
        assert cmd.execute_called == 1
        assert len(command_manager._undo_stack) == 1
        assert len(command_manager._redo_stack) == 0
        
        # Verify model and event aggregator
        mock_application_model.set_dirty.assert_called_with(True)
        mock_event_aggregator.publish.assert_any_call(Events.PROJECT_IS_DIRTY_CHANGED, is_dirty=True)

    def test_undo_moves_command_to_redo_stack(self, command_manager, mock_application_model, mock_event_aggregator):
        """Verifies that undo reverses the command and updates stacks."""
        cmd = MockCommand()
        command_manager.execute_command(cmd)
        
        command_manager.undo()
        
        assert cmd.undo_called == 1
        assert len(command_manager._undo_stack) == 0
        assert len(command_manager._redo_stack) == 1
        
        # Since undo stack is empty, model should be clean
        mock_application_model.set_dirty.assert_called_with(False)
        mock_event_aggregator.publish.assert_any_call(Events.PROJECT_IS_DIRTY_CHANGED, is_dirty=False)

    def test_redo_executes_previously_undone_command(self, command_manager, mock_application_model):
        """Verifies that redo re-executes the command and updates stacks."""
        cmd = MockCommand()
        command_manager.execute_command(cmd) # execute_called = 1
        command_manager.undo()               # undo_called = 1
        
        command_manager.redo()
        
        assert cmd.execute_called == 2
        assert len(command_manager._undo_stack) == 1
        assert len(command_manager._redo_stack) == 0
        mock_application_model.set_dirty.assert_called_with(True)

    def test_new_command_clears_redo_stack(self, command_manager):
        """Verifies branching history (new command wipes forward history)."""
        cmd1 = MockCommand()
        cmd2 = MockCommand()
        cmd3 = MockCommand()
        
        command_manager.execute_command(cmd1)
        command_manager.undo()
        assert len(command_manager._redo_stack) == 1
        
        # Executing a new command should clear the redo stack
        command_manager.execute_command(cmd2)
        assert len(command_manager._redo_stack) == 0

    def test_undo_empty_stack_is_safe(self, command_manager):
        """Ensures undoing on an empty stack does not raise errors."""
        # Should not raise exception
        command_manager.undo()
        assert len(command_manager._redo_stack) == 0

    def test_redo_empty_stack_is_safe(self, command_manager):
        """Ensures redoing on an empty stack does not raise errors."""
        # Should not raise exception
        command_manager.redo()
        assert len(command_manager._undo_stack) == 0

    def test_sequential_undos_logic(self, command_manager, mock_application_model):
        """Verifies that model only becomes clean when ALL commands are undone."""
        cmd1 = MockCommand()
        cmd2 = MockCommand()
        
        command_manager.execute_command(cmd1)
        command_manager.execute_command(cmd2)
        
        # Undo first command (cmd2)
        command_manager.undo()
        assert len(command_manager._undo_stack) == 1
        # Model should still be dirty because cmd1 is still in undo stack
        # Note: Current implementation only calls set_dirty(False) if stack is empty.
        # It doesn't call set_dirty(True) again during undo if stack NOT empty, 
        # but it shouldn't have changed from True anyway.
        
        # Undo second command (cmd1)
        command_manager.undo()
        assert len(command_manager._undo_stack) == 0
        mock_application_model.set_dirty.assert_called_with(False)
