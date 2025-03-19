import re
from aiogram import types, Dispatcher, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BotCommand
from llm_api import generate_exercise
from prompts import exercise_prompt, check_answers_prompt

router = Router()

class ExerciseState(StatesGroup):
    choosing_level = State()
    entering_topic = State()
    waiting_for_answers = State()

async def set_commands(bot):
    commands = [
        BotCommand(command="start", description="🚀 Перезапустить бота"),
        BotCommand(command="level", description="📚 Сменить уровень"),
    ]
    await bot.set_my_commands(commands)

async def start_command(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Beginner")],
            [KeyboardButton(text="Intermediate")],
            [KeyboardButton(text="Advanced")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "👋 Привет! Я твой персональный репетитор английского.\n\n"
        "Выбери свой уровень английского:",
        reply_markup=kb
    )
    await state.set_state(ExerciseState.choosing_level)

async def choose_level(message: types.Message, state: FSMContext):
    level = message.text.strip()

    if level not in ["Beginner", "Intermediate", "Advanced"]:
        await message.answer("❌ Пожалуйста, выбери уровень с помощью кнопок.")
        return

    await state.update_data(level=level)

    await message.answer(
        f"✅ Ты выбрал уровень: <b>{level}</b>\n\n"
        "Теперь введи тему упражнения.\n\n"
        "📌 Например:\n<code>Past Simple</code>, <code>Present Continuous</code>, <code>Vocabulary</code>",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ExerciseState.entering_topic)

async def generate_exercise_handler(message: types.Message, state: FSMContext):
    topic = message.text.strip()
    user_data = await state.get_data()
    level = user_data['level']

    wait_msg = await message.answer("⏳ Генерирую задание...", parse_mode='HTML')

    prompt = exercise_prompt(level, topic, "multiple-choice")
    llm_result = generate_exercise(prompt)

    await wait_msg.delete()

    cleaned_result = re.sub(r'<think>.*?</think>', '', llm_result, flags=re.DOTALL | re.IGNORECASE).strip()
    cleaned_result = re.split(r'Answers:', cleaned_result, flags=re.IGNORECASE)[0].strip()
    cleaned_result = re.split(r'Explanations:', cleaned_result, flags=re.IGNORECASE)[0].strip()

    await state.update_data(exercise=cleaned_result)

    await message.answer(cleaned_result, parse_mode='HTML')
    await message.answer(
        "✏️ Отправь свои ответы в формате: <code>1c, 2b, 3a</code>",
        parse_mode='HTML'
    )

    await state.set_state(ExerciseState.waiting_for_answers)

async def check_answers_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    exercise_text = user_data.get('exercise')
    user_answers = message.text.strip()

    wait_msg = await message.answer("⏳ Проверяю твои ответы...", parse_mode='HTML')

    prompt = check_answers_prompt(exercise_text, user_answers)
    result = generate_exercise(prompt)

    await wait_msg.delete()

    await message.answer(result, parse_mode='HTML')

    await message.answer(
        "📌 Введи следующую тему для упражнения:\n"
        "Например: <code>Past Simple</code>, <code>Vocabulary</code>",
        parse_mode='HTML'
    )
    await state.set_state(ExerciseState.entering_topic)

async def incorrect_answers_format(message: types.Message):
    await message.answer(
        "❌ Неверный формат ответов.\n\n"
        "Отправь ответы в формате:\n"
        "<code>1c, 2b, 3a</code>",
        parse_mode='HTML'
    )

async def incorrect_topic_format(message: types.Message):
    await message.answer(
        "❌ Некорректная тема.\n\n"
        "Введи тему упражнения, например:\n<code>Past Simple</code>, <code>Vocabulary</code>",
        parse_mode='HTML'
    )

async def level_command(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Beginner")],
            [KeyboardButton(text="Intermediate")],
            [KeyboardButton(text="Advanced")]
        ],
        resize_keyboard=True
    )
    await message.answer("📚 Выбери новый уровень:", reply_markup=kb)
    await state.set_state(ExerciseState.choosing_level)

async def not_allowed_input(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ExerciseState.waiting_for_answers.state:
        await incorrect_answers_format(message)
    elif current_state == ExerciseState.entering_topic.state:
        await incorrect_topic_format(message)
    elif current_state == ExerciseState.choosing_level.state:
        await message.answer("❌ Выбери уровень с помощью кнопок.")

def register_handlers(dp: Dispatcher):
    router.message.register(start_command, CommandStart())
    router.message.register(level_command, Command("level"))

    router.message.register(
        choose_level,
        ExerciseState.choosing_level,
        F.text.in_(["Beginner", "Intermediate", "Advanced"])
    )

    router.message.register(
        generate_exercise_handler,
        ExerciseState.entering_topic,
        F.text
    )

    router.message.register(
        check_answers_handler,
        ExerciseState.waiting_for_answers,
        F.text.regexp(r'^(\d[a-d],\s*){2}\d[a-d]$')
    )

    router.message.register(
        not_allowed_input,
        ExerciseState.waiting_for_answers
    )

    router.message.register(
        incorrect_topic_format,
        ExerciseState.entering_topic
    )

    router.message.register(
        choose_level,
        ExerciseState.choosing_level
    )

    dp.include_router(router)
