"""FSM States for BotGenerator conversation flow."""

from aiogram.fsm.state import State, StatesGroup


class BotCreationStates(StatesGroup):
    """States for bot creation flow."""
    WAITING_FOR_DESCRIPTION = State()  # Waiting for bot description
    WAITING_FOR_TOKEN = State()  # Waiting for bot token
