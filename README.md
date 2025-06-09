# EnglishTutorBot

EnglishTutorBot — это Telegram-бот, который генерирует короткие упражнения по английской грамматике с помощью модели LLM. Бот спрашивает у пользователя уровень и тему, затем создаёт вопросы с несколькими вариантами ответов и проверяет результаты.

## Features
- Интерактивный Telegram-бот на базе **aiogram**
- Использует Groq API (LLM) для генерации упражнений
- Поддерживает разные уровни сложности и темы
- Предоставляет мгновенную обратную связь с пояснениями

## Requirements
- Python 3.10+
- Зависимости из `requirements.txt`
- Токен Telegram-бота и ключ Groq API

## Installation
1. Клонируйте репозиторий:
   ```bash
   git clone <repo-url>
   cd EnglishTutorBot
   ```
2. (Опционально) создайте виртуальное окружение и активируйте его:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Создайте файл `.env` в корне проекта и добавьте переменные:
   ```
   TELEGRAM_TOKEN=<ваш токен бота>
   GROQ_API_KEY=<ваш API-ключ>
   ```

## Running the bot
Выполните точку входа:
```bash
python app/main.py
```
Бот начнёт опрашивать Telegram и реагировать на команды, например `/start`.

## Project structure
```
app/
├── handlers.py   # обработчики Telegram и FSM
├── llm_api.py    # обёртка над Groq API
├── main.py       # точка входа
├── prompts.py    # шаблоны подсказок для LLM
├── states.py     # (не используется) пример состояний FSM
└── storage.py    # (не используется) задел для хранилища
```

## License
MIT
