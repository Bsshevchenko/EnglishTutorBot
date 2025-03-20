import re
from aiogram import types, Dispatcher, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, CallbackQuery
)
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
        "👋 Привет! Выбери свой уровень английского:",
        reply_markup=kb
    )
    await state.set_state(ExerciseState.choosing_level)

async def choose_level(message: types.Message, state: FSMContext):
    level = message.text.strip()
    if level not in ["Beginner", "Intermediate", "Advanced"]:
        await message.answer("❌ Выбери уровень с помощью кнопок.")
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
    data = await state.get_data()
    level = data['level']

    wait_msg = await message.answer("⏳ Генерирую задание...", parse_mode='HTML')

    prompt = exercise_prompt(level, topic, "multiple-choice")
    llm_result = generate_exercise(prompt)

    await wait_msg.delete()

    cleaned_result = re.sub(r'<think>.*?</think>', '', llm_result, flags=re.DOTALL).strip()
    questions = re.findall(r"\d️⃣.*?(?:a\)|b\)|c\)|d\)).*?(?:\n|$)", cleaned_result, re.DOTALL)

    await state.update_data(exercise=cleaned_result, user_answers={})

    await message.answer(cleaned_result, parse_mode='HTML')

    # Генерируем кнопки ответов
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{i+1}{opt}", callback_data=f"{i+1}{opt}")
            for opt in ['a', 'b', 'c', 'd']
        ] for i in range(len(questions))
    ])

    await message.answer("🔘 Выбери ответы на вопросы:", reply_markup=markup)
    await state.set_state(ExerciseState.waiting_for_answers)

async def handle_answer_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_answers = data.get('user_answers', {})

    selected = callback.data  # Например: "1a"
    question_num, chosen_option = selected[0], selected[1]

    user_answers[question_num] = chosen_option
    await state.update_data(user_answers=user_answers)

    # Пересобираем клавиатуру с подсветкой выбранных ответов
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{i+1}{opt} {'✅' if user_answers.get(str(i+1)) == opt else ''}",
                callback_data=f"{i+1}{opt}"
            )
            for opt in ['a', 'b', 'c', 'd']
        ] for i in range(3)
    ])

    await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer(f"✅ Ответ {question_num}{chosen_option} принят!")

    # Проверяем, что выбраны ответы на все вопросы
    if len(user_answers) == 3:
        await check_all_answers(callback.message, state)


async def check_all_answers(message: types.Message, state: FSMContext):
    data = await state.get_data()
    exercise_text = data['exercise']
    user_answers_dict = data['user_answers']

    user_answers = ', '.join([f"{k}{v}" for k, v in sorted(user_answers_dict.items())])

    wait_msg = await message.answer("⏳ Проверяю ответы...", parse_mode='HTML')

    prompt = check_answers_prompt(exercise_text, user_answers)
    result = generate_exercise(prompt)

    await wait_msg.delete()

    await message.answer(result, parse_mode='HTML')

    # Сбрасываем ответы
    await state.update_data(user_answers={})

    await message.answer(
        "📌 Введи следующую тему для упражнения:\n"
        "Например: <code>Past Simple</code>, <code>Vocabulary</code>",
        parse_mode='HTML'
    )
    await state.set_state(ExerciseState.entering_topic)

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

async def incorrect_input(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ExerciseState.entering_topic:
        await message.answer("❌ Введи корректную тему, например: <code>Past Simple</code>", parse_mode='HTML')

def register_handlers(dp: Dispatcher):
    router.message.register(start_command, CommandStart())
    router.message.register(level_command, Command("level"))

    router.message.register(choose_level, ExerciseState.choosing_level, F.text.in_(["Beginner", "Intermediate", "Advanced"]))
    router.message.register(generate_exercise_handler, ExerciseState.entering_topic, F.text)

    router.callback_query.register(handle_answer_callback, ExerciseState.waiting_for_answers)

    router.message.register(incorrect_input)

    dp.include_router(router)
