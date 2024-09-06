import asyncio
from telegram import Bot

API_TOKEN = '7302196363:AAGySzGIkc9lR09EEfZo3ECAo2NdgFwahBs'
bot = Bot(token=API_TOKEN)

async def send_test_message():
    try:
        await bot.send_message(chat_id='@ensecrets', text='Тестовое сообщение')
        print("Сообщение отправлено успешно!")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Запуск асинхронной функции
asyncio.run(send_test_message())