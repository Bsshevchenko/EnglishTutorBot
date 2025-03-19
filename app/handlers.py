import re
from aiogram import types, Dispatcher, Router, F
from aiogram.filters import Command
from llm_api import generate_exercise
from prompts import exercise_prompt, check_answers_prompt
from storage import user_exercises

router = Router()

async def start_command(message: types.Message):
    await message.answer(
        "👋 Привет! Отправь задание в формате:\n<code>Intermediate, Past Simple, multiple-choice</code>",
        parse_mode='HTML'
    )

async def generate_exercise_handler(message: types.Message):
    user_id = message.from_user.id
    try:
        level, topic, ex_type = map(str.strip, message.text.split(','))
    except:
        await message.answer(
            "❌ Неверный формат ввода. Используй: <code>Intermediate, Past Simple, multiple-choice</code>",
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


    user_exercises[user_id] = cleaned_result

    await message.answer(cleaned_result, parse_mode='HTML')
    await message.answer(
        "✏️ Отправь свои ответы в формате: <code>1c, 2b, 3a</code>",
        parse_mode='HTML'
    )

async def check_answers_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_exercises:
        await message.answer(
            "❌ Сначала получи задание! Отправь: <code>Intermediate, Past Simple, multiple-choice</code>",
            parse_mode='HTML'
        )
        return

    exercise_text = user_exercises[user_id]
    user_answers = message.text.strip()

    wait_msg = await message.answer("⏳ Проверяю твои ответы...", parse_mode='HTML')

    prompt = check_answers_prompt(exercise_text, user_answers)
    result = generate_exercise(prompt)

    await wait_msg.delete()

    await message.answer(result, parse_mode='HTML')

    del user_exercises[user_id]


def register_handlers(dp: Dispatcher):
    router.message.register(start_command, Command("start"))
    router.message.register(generate_exercise_handler, F.text.regexp(r'^[A-Za-z]+,\s*[A-Za-z ]+,\s*[A-Za-z-]+$'))
    router.message.register(check_answers_handler, F.text.regexp(r'^(\d[a-d],?\s*)+$'))
    dp.include_router(router)