from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from datetime import datetime

# Вставьте ваш токен API
API_TOKEN = '7321264104:AAEzuNE85aE8YvBvWCU7gP5SRuMuQchogiM'
CHANNEL_ID = '@ensecrets'  # Замените на ID вашего канала

# Этапы для добавления сообщения в бота
TEXT, DATE = range(2)

# Массив для хранения сообщений и времени их отправки
scheduled_messages = []
bot_active = False
job_queue = None  # Храним ссылку на очередь задач

# Клавиатура с кнопками
def get_main_keyboard():
    keyboard = [
        ["Добавить сообщение", "Старт бот", "Стоп бот"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Функция для отправки стартового сообщения с клавиатурой
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Добро пожаловать! Выберите действие:", 
        reply_markup=get_main_keyboard()
    )

# Начало процесса добавления сообщения
def add_message_start(update: Update, context: CallbackContext):
    update.message.reply_text("Введите текст сообщения, которое хотите отправить:", reply_markup=get_main_keyboard())
    return TEXT

# Получаем текст сообщения от пользователя
def get_message_text(update: Update, context: CallbackContext):
    context.user_data['message_text'] = update.message.text
    update.message.reply_text("Теперь введите дату и время отправки сообщения в формате: YYYY-MM-DD HH:MM. Например, 2024-09-10 14:30.", reply_markup=get_main_keyboard())
    return DATE

# Получаем дату и время, затем добавляем сообщение в массив
def get_message_time(update: Update, context: CallbackContext):
    try:
        publish_time_str = update.message.text
        publish_time = datetime.strptime(publish_time_str, "%Y-%m-%d %H:%M")
        message_text = context.user_data['message_text']

        # Добавляем сообщение в массив
        scheduled_messages.append({"text": message_text, "publish_time": publish_time})
        update.message.reply_text(f"Сообщение добавлено! Оно будет отправлено {publish_time_str}: {message_text}", reply_markup=get_main_keyboard())
        print(f"[INFO] Сообщение добавлено для отправки в {publish_time_str}: {message_text}")
        return ConversationHandler.END
    except ValueError:
        # Если формат даты и времени неправильный, отправляем подсказку снова
        update.message.reply_text("Ошибка: неверный формат времени. Пожалуйста, введите дату и время в формате YYYY-MM-DD HH:MM. Например: 2024-09-10 14:30.", reply_markup=get_main_keyboard())
        return DATE

# Прерываем процесс добавления
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Добавление сообщения отменено.', reply_markup=get_main_keyboard())
    return ConversationHandler.END

# Функция для отправки сообщений
def send_scheduled_messages(context: CallbackContext):
    global bot_active
    if bot_active:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"[INFO] Текущая дата и время: {current_time}")
        
        if scheduled_messages:
            for message in scheduled_messages:
                message_time = message["publish_time"].strftime("%Y-%m-%d %H:%M")
                if message_time <= current_time:
                    context.bot.send_message(chat_id=CHANNEL_ID, text=message["text"])
                    print(f"[INFO] Сообщение отправлено: {message['text']} в {message_time}")
                    scheduled_messages.remove(message)  # Удаляем сообщение после отправки
                else:
                    print(f"[INFO] Сообщение ожидает отправки в {message_time}: {message['text']}")
        else:
            print("[INFO] Нет сообщений для отправки.")
        
        # Запускаем проверку каждые 30 секунд
        context.job_queue.run_once(send_scheduled_messages, when=30)

# Функция для запуска бота
def start_bot(update: Update, context: CallbackContext):
    global bot_active, job_queue
    if bot_active:
        update.message.reply_text("Бот уже запущен!", reply_markup=get_main_keyboard())
    else:
        bot_active = True
        update.message.reply_text("Бот запущен! Проверка сообщений начата.", reply_markup=get_main_keyboard())
        print("[INFO] Бот запущен. Начинаем проверку сообщений.")
        job_queue = context.job_queue.run_once(send_scheduled_messages, when=0)

# Функция для остановки бота
def stop_bot(update: Update, context: CallbackContext):
    global bot_active, job_queue
    if bot_active:
        bot_active = False
        update.message.reply_text("Бот остановлен.", reply_markup=get_main_keyboard())
        print("[INFO] Бот остановлен.")
        
        # Отменяем все запланированные задачи в очереди
        if job_queue is not None:
            job_queue.schedule_removal()
            print("[INFO] Очередь задач остановлена.")
    else:
        update.message.reply_text("Бот уже остановлен.", reply_markup=get_main_keyboard())

# Основная функция для запуска бота
def main():
    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Добавляем команду /start для отображения клавиатуры с кнопками
    dp.add_handler(CommandHandler("start", start))

    # Добавляем ConversationHandler для добавления сообщения через кнопки
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Добавить сообщение$'), add_message_start)],
        states={
            TEXT: [MessageHandler(Filters.text & ~Filters.command, get_message_text)],
            DATE: [MessageHandler(Filters.text & ~Filters.command, get_message_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)

    # Обработчик текстовых сообщений (для кнопок "Старт бот" и "Стоп бот")
    dp.add_handler(MessageHandler(Filters.regex('^Старт бот$'), start_bot))
    dp.add_handler(MessageHandler(Filters.regex('^Стоп бот$'), stop_bot))

    # Запуск polling
    updater.start_polling()
    print("[INFO] Бот запущен и ожидает команды...")
    updater.idle()

if __name__ == "__main__":
    main()
