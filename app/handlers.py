import re
from aiogram import types, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from llm_api import generate_exercise
from prompts import exercise_prompt, check_answers_prompt

router = Router()

class ExerciseState(StatesGroup):
    waiting_for_exercise = State()
    waiting_for_answers = State()

async def start_command(message: types.Message, state: FSMContext):
    await message.answer(
        "👋 Привет! Я твой персональный репетитор английского.\n\n"
        "Чтобы получить упражнение, отправь запрос в формате:\n"
        "<code>Уровень, Тема, Тип задания</code>\n\n"
        "📌 Например:\n"
        "<code>Intermediate, Past Simple, multiple-choice</code>\n\n"
        "🔎 Расшифровка:\n"
        "<b>Уровень:</b> Beginner, Intermediate, Advanced\n"
        "<b>Тема:</b> Например, Past Simple, Present Continuous, Vocabulary\n"
        "<b>Тип задания:</b> multiple-choice (выбор ответа из вариантов)",
        parse_mode='HTML'
    )
    await state.set_state(ExerciseState.waiting_for_exercise)

async def generate_exercise_handler(message: types.Message, state: FSMContext):
    try:
        level, topic, ex_type = map(str.strip, message.text.split(','))
    except:
        await message.answer(
            "❌ Неверный формат ввода.\n\n"
            "Используй формат:\n"
            "<code>Intermediate, Past Simple, multiple-choice</code>",
            parse_mode='HTML'
        )
        return

    wait_msg = await message.answer("⏳ Генерирую задание...", parse_mode='HTML')

    prompt = exercise_prompt(level, topic, ex_type)
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

async def incorrect_format_exercise(message: types.Message):
    await message.answer(
        "❌ Некорректный запрос.\n\n"
        "Чтобы получить упражнение, введи запрос в формате:\n"
        "<code>Intermediate, Past Simple, multiple-choice</code>",
        parse_mode='HTML'
    )

async def check_answers_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    exercise_text = user_data.get('exercise')
    user_answers = message.text.strip()

    wait_msg = await message.answer("⏳ Проверяю твои ответы...", parse_mode='HTML')

    prompt = check_answers_prompt(exercise_text, user_answers)
    result = generate_exercise(prompt)

    await wait_msg.delete()

    await message.answer(result, parse_mode='HTML')

    # Циклически возвращаем в состояние ожидания следующего упражнения
    await message.answer(
        "🔄 Хочешь ещё упражнение?\n\n"
        "Отправь запрос в формате:\n"
        "<code>Intermediate, Past Simple, multiple-choice</code>",
        parse_mode='HTML'
    )
    await state.set_state(ExerciseState.waiting_for_exercise)

async def incorrect_answers_format(message: types.Message):
    await message.answer(
        "❌ Неверный формат ответов.\n\n"
        "Отправь ответы в формате:\n"
        "<code>1c, 2b, 3a</code>",
        parse_mode='HTML'
    )

async def no_new_task_allowed(message: types.Message):
    await message.answer(
        "❌ Сначала закончи текущее упражнение!\n\n"
        "Отправь ответы в формате:\n"
        "<code>1c, 2b, 3a</code>",
        parse_mode='HTML'
    )

def register_handlers(dp: Dispatcher):
    router.message.register(start_command, Command("start"))

    # Генерация упражнения
    router.message.register(
        generate_exercise_handler,
        ExerciseState.waiting_for_exercise,
        F.text.regexp(r'^[A-Za-z]+,\s*[A-Za-z ]+,\s*[A-Za-z-]+$')
    )

    router.message.register(
        incorrect_format_exercise,
        ExerciseState.waiting_for_exercise
    )

    # Проверка ответов
    router.message.register(
        check_answers_handler,
        ExerciseState.waiting_for_answers,
        F.text.regexp(r'^(\d[a-d],\s*){2}\d[a-d]$')
    )

    router.message.register(
        incorrect_answers_format,
        ExerciseState.waiting_for_answers,
        F.text
    )

    # Запрет нового задания до окончания текущего
    router.message.register(
        no_new_task_allowed,
        ExerciseState.waiting_for_answers,
        F.text.regexp(r'^[A-Za-z]+,\s*[A-Za-z ]+,\s*[A-Za-z-]+$')
    )

    dp.include_router(router)
