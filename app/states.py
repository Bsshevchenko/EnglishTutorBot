from aiogram.fsm.state import StatesGroup, State

class ExerciseState(StatesGroup):
    waiting_for_answers = State()
