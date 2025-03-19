import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def generate_exercise(prompt):
    try:
        logging.info(f"Отправляем в Groq API: {prompt}")

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-specdec",  # ✅ Заменяем модель на Mixtral-8x7b
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            logging.error(f"Ошибка Groq API: {response.text}")
            return "❌ Ошибка при запросе к LLM. Попробуй позже."

    except Exception as e:
        logging.error(f"Ошибка генерации: {e}")
        return "❌ Ошибка при запросе к LLM. Попробуй позже."
