# bot_handler.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
)
from bot_db_functions import add_user, find_interests, add_interests  # Импортируем функции для работы с БД
import pandas as pd
import logging

from src.config import INTERESTS

logger = logging.getLogger(__name__)

# Функция для команды /start
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    add_user(user_id)  # Сохраняем пользователя в БД
    await update.message.reply_text(
        "Привет! Я бот проекта Muza. Я помогу собрать информацию о ваших "
        "культурных интересах. Используйте /interests чтобы указать свои интересы "
        "или /help для получения справки."
    )

# Функция для команды /help
async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/interests - Указать свои интересы\n"
        "/privacy - Политика конфиденциальности\n"
        "/help - Показать эту справку"
    )

# Функция для команды /privacy
async def privacy_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Наш бот собирает только ваш Telegram ID и информацию об интересах "
        "для формирования рекомендаций музеев. Персональные данные "
        "(имя, фамилия, телефон и др.) не запрашиваются и не сохраняются. "
        "При работе с AI-моделью передаются только ваши интересы в обезличенном виде, "
        "без привязки к личной идентификации."
    )

# Показ категорий интересов
async def show_categories(update: Update, context: CallbackContext):
    keyboard = []
    for category in INTERESTS.keys():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"category_{category}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите категорию интересов:", reply_markup=reply_markup)

# Показ интересов выбранной категории
async def show_interests(update: Update, context: CallbackContext):
    query = update.callback_query
    category = query.data.replace("category_", "")
    keyboard = []
    for interest in INTERESTS[category]:
        keyboard.append([InlineKeyboardButton(interest, callback_data=f"interest_{interest}")])
    keyboard.append([InlineKeyboardButton("Назад к категориям", callback_data="back_to_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Выберите интересы в категории {category}:", reply_markup=reply_markup)

# Обработка выбора интереса
async def handle_interest_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "back_to_categories":
        await show_categories(update, context)
        return
    interest = query.data.replace("interest_", "")
    user_id = query.from_user.id
    # Сохраняем выбранный интерес
    add_interests(pd.DataFrame({"tg_id": [user_id], "interest_id": [find_interests(user_id, [interest])]}))
    await query.answer(f"Вы выбрали: {interest}")

# Обработчик callback-запросов
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data.startswith("category_"):
        await show_interests(update, context)
    elif query.data.startswith("interest_") or query.data == "back_to_categories":
        await handle_interest_selection(update, context)

# Обработка текстовых сообщений
async def handle_message(update: Update, context: CallbackContext):
    await update.message.reply_text("Я не понимаю, что вы имеете в виду. Пожалуйста, используйте одну из доступных команд.")

# Обработчик ошибок
async def error_handler(update, context: CallbackContext):
    logger.error(f"Ошибка: {context.error}")