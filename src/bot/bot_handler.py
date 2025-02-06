import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
)
import logging

from src.bot.bot_db_functions import BotDbFunctions
from src.interests import INTERESTS

logger = logging.getLogger(__name__)

# Функция для команды /start
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    BotDbFunctions.add_user(user_id)  # Сохраняем пользователя в БД
    await update.message.reply_text(
        "Привет! Я бот проекта Muza. Я помогу собрать информацию о ваших "
        "культурных интересах. Используйте /interests чтобы указать свои интересы "
        "и /remove_interest чтобы удалить выбранные интересы."
        "Используется /help для получения полного списка доступных команд."
    )

# Функция для команды /help
async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/select_interests - Указать свои интересы\n"
        "/remove_interest - Удалить выбранные интересы\n"
        "/show_my_interests - Показать ваши выбранные интересы\n"
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

    # Добавляем кнопку возврата в главное меню
    keyboard.append([InlineKeyboardButton("<< В ГЛАВНОЕ МЕНЮ", callback_data="main_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    # Если вызываем из callback (назад), редактируем сообщение
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(
            text="Выберите категорию интересов:",
            reply_markup=reply_markup
        )
    else:
        # Если вызываем из команды /interests, отправляем новое сообщение
        await update.message.reply_text(
            "Выберите категорию интересов:",
            reply_markup=reply_markup
        )

# Показ интересов выбранной категории
async def show_interests(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    # Определяем категорию из callback_data или контекста
    if query.data.startswith("category_"):
        category = query.data.replace("category_", "")
        context.user_data['current_category'] = category  # Сохраняем категорию
    else:
        category = context.user_data.get('current_category')
        if not category:
            await query.edit_message_text("Ошибка: категория не найдена.")
            return

    user_interests = BotDbFunctions.get_user_interests(user_id)

    keyboard = [
        [InlineKeyboardButton("<< НАЗАД К КАТЕГОРИЯМ", callback_data="back_to_categories")]
    ]

    # Добавляем только неуказанные интересы
    for interest in INTERESTS[category]:
        if interest not in user_interests:
            keyboard.append([InlineKeyboardButton(interest, callback_data=f"interest_{interest}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"Выберите интересы в категории {category}:",
        reply_markup=reply_markup
    )


# Функция для команды /remove_interest
async def remove_interest(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Получаем интересы пользователя через функцию из bot_db_functions
    interests = BotDbFunctions.get_user_interests(user_id)

    if not interests:
        await update.message.reply_text("У вас пока нет сохраненных интересов.")
        return

    # Создаем клавиатуру с кнопками для удаления интересов
    keyboard = []
    for interest_name in interests:
        keyboard.append([InlineKeyboardButton(interest_name, callback_data=f"remove_{interest_name}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel_remove")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите интерес для удаления:", reply_markup=reply_markup)


# Функция для команды /show_my_interests
async def show_my_interests(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    interests = BotDbFunctions.get_user_interests(user_id)

    if not interests:
        await update.message.reply_text("У вас пока нет выбранных интересов.")
        return

    # Формируем список интересов
    interests_list = "\n".join(f"• {interest}" for interest in interests)
    await update.message.reply_text(
        f"Ваши выбранные интересы:\n{interests_list}"
    )


# Обработка выбора интереса для удаления
async def handle_remove_interest(update: Update, context: CallbackContext):
    query = update.callback_query

    if query.data == "cancel_remove":
        await query.edit_message_text("Операция удаления отменена.")
        return

    interest_name = query.data.replace("remove_", "")
    user_id = query.from_user.id

    # Получаем ID интереса через функцию из bot_db_functions
    interest_id = BotDbFunctions.get_interest_id(interest_name)
    if interest_id is None:
        await query.answer(f"Интерес '{interest_name}' не найден.")
        return

    # Удаляем интерес через функцию из bot_db_functions
    BotDbFunctions.remove_interest(user_id, interest_id)
    await query.edit_message_text(f"Интерес '{interest_name}' успешно удален.")


# Обработка выбора интереса
async def handle_interest_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    interest = query.data.replace("interest_", "")
    user_id = query.from_user.id

    # Добавляем интерес
    interest_id = BotDbFunctions.get_interest_id(interest)
    if interest_id is None:
        await query.answer(f"Интерес '{interest}' не найден.")
        return

    BotDbFunctions.add_interest(user_id, interest_id)
    await query.answer(f"Вы выбрали: {interest}")

    # Ждем немного, чтобы пользователь успел увидеть уведомление
    await asyncio.sleep(0.5)

    # Обновляем список интересов с текущей категорией
    await show_interests(update, context)

# Обработчик callback-запросов
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("category_"):
        await show_interests(update, context)
    elif query.data.startswith("interest_"):
        await handle_interest_selection(update, context)
    elif query.data == "back_to_categories":
        await show_categories(update, context)
    elif query.data == "main_menu":
        await help_command(update, context)
    elif query.data.startswith("remove_"):
        await handle_remove_interest(update, context)
    elif query.data == "cancel_remove":
        await query.edit_message_text("Операция удаления отменена.")

# Обработка текстовых сообщений
async def handle_message(update: Update, context: CallbackContext):
    await update.message.reply_text("Я не понимаю, что вы имеете в виду. Пожалуйста, используйте одну из доступных команд.")

# Обработчик ошибок
async def error_handler(update, context: CallbackContext):
    logger.error(f"Ошибка: {context.error}")