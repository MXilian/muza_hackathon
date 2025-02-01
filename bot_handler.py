import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from db_handler import setup_database

# Функция для команды /start
def start(update: Update, context: CallbackContext):
    # Проверяем/создаем базу данных
    setup_database()

    # Отвечаем пользователю
    update.message.reply_text(
        "Привет! Я Telegram-бот, который пока еще нуждается в дальнейшей настройке :D"
    )

# Функция для команды /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("Список доступных команд:\n/start - Запуск бота\n/help - Справка")


# Главная точка входа
def main():
    # Получаем токен из переменной окружения
    bot_token = os.getenv("BOT_TOKEN")

    # Создаем объект Updater для работы с ботом
    updater = Updater(bot_token)

    # Регистрируем обработчики команд
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    # Запускаем Webhook
    port = int(os.getenv('PORT', 5000))
    updater.start_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=bot_token,
        webhook_url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{bot_token}"
    )
    updater.idle()

if __name__ == "__main__":
    main()