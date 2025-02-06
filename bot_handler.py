import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)
from config import INTERESTS
from db_handler import setup_database, add_user, save_interests

# Функция для команды /start
def start(update: Update, context: CallbackContext):
    # Проверяем/создаем базу данных
    setup_database()
    # Сохраняем текущега тг-юзера в БД
    user_id = update.effective_user.id
    add_user(user_id)
    # Отвечаем юзеру
    update.message.reply_text(
        "Привет! Я бот проекта Muza. Я помогу собрать информацию о ваших "
        "культурных интересах. Используйте /interests чтобы указать свои интересы "
        "или /help для получения справки."
    )

# Функция для команды /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/interests - Указать свои интересы\n"
        "/privacy - Политика конфиденциальности\n"
        "/help - Показать эту справку"
    )

# Функция для команды /help
def privacy_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Наш бот собирает только ваш Telegram ID и информацию об интересах "
        "для формирования рекомендаций музеев. Персональные данные "
        "(имя, фамилия, телефон и др.) не запрашиваются и не сохраняются. "
        "При работе с AI-моделью передаются только ваши интересы в обезличенном виде, "
        "без привязки к личной идентификации."
    )

def show_categories(update: Update, context: CallbackContext):
    keyboard = []
    for category in INTERESTS.keys():
        keyboard.append([InlineKeyboardButton(
            category,
            callback_data=f"category_{category}"
        )])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Выберите категорию интересов:",
        reply_markup=reply_markup
    )

def show_interests(update: Update, context: CallbackContext):
    """Показывает интересы выбранной категории"""
    query = update.callback_query
    category = query.data.replace("category_", "")
    keyboard = []
    for interest in INTERESTS[category]:
        keyboard.append([InlineKeyboardButton(
            interest,
            callback_data=f"interest_{interest}"
        )])
    keyboard.append([InlineKeyboardButton(
        "Назад к категориям",
        callback_data="back_to_categories"
    )])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        f"Выберите интересы в категории {category}:",
        reply_markup=reply_markup
    )

def handle_interest_selection(update: Update, context: CallbackContext):
    """Обработка выбора интереса"""
    query = update.callback_query
    if query.data == "back_to_categories":
        keyboard = []
        for category in INTERESTS.keys():
            keyboard.append([InlineKeyboardButton(
                category,
                callback_data=f"category_{category}"
            )])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            "Выберите категорию интересов:",
            reply_markup=reply_markup
        )
        return
    interest = query.data.replace("interest_", "")
    user_id = query.from_user.id
    # Сохраняем выбранный интерес
    save_interests(user_id, [interest])
    query.answer(f"Вы выбрали: {interest}")

def handle_callback(update: Update, context: CallbackContext):
    """Обработчик callback-запросов"""
    query = update.callback_query
    if query.data.startswith("category_"):
        show_interests(update, context)
    elif query.data.startswith("interest_") or query.data == "back_to_categories":
        handle_interest_selection(update, context)

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
    dp.add_handler(CommandHandler("interests", show_categories))
    dp.add_handler(CommandHandler("privacy", privacy_command))

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