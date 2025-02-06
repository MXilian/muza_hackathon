from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, ConversationHandler,
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
        "Привет! Я бот проекта Muza.\nЯ помогу собрать информацию о ваших "
        "культурных интересах, и на их основании предложу вам релевантную "
        "подборку музеев выбранного города. "
        "\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/select_interests - Указать свои интересы\n"
        "/remove_interest - Удалить выбранные интересы\n"
        "/show_my_interests - Показать ваши выбранные интересы\n"
        "/museums_for_me - Найти музеи по вашим интересам\n"
        "/privacy - Политика конфиденциальности\n"
        "/help - Показать список доступных команд"
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
        "/help - Показать список доступных команд"
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


# Состояния для ConversationHandler
LOCATION_INPUT = 1

# Обработчик команды /museums_for_me
async def museums_for_me(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    interests = BotDbFunctions.get_user_interests(user_id)

    # Если интересов нет, предлагаем выбрать их
    if not interests:
        await update.message.reply_text(
            "У вас пока нет выбранных интересов. Пожалуйста, сначала выберите интересы "
            "с помощью команды /select_interests, чтобы я мог вам что-то порекомендовать."
        )
        return ConversationHandler.END  # Завершаем диалог

    # Если интересы есть, запрашиваем населенный пункт
    await update.message.reply_text(
        "Пожалуйста, введите название населенного пункта РФ, по которому осуществить поиск:"
    )
    return LOCATION_INPUT  # Переходим в состояние ожидания ввода города


# Функция для команды /select_interests
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
    category = context.user_data.get('current_category')

    # Получаем уже выбранные интересы пользователя
    user_interests = BotDbFunctions.get_user_interests(user_id)

    keyboard = [
        [InlineKeyboardButton("<< НАЗАД К КАТЕГОРИЯМ", callback_data="back_to_categories")]
    ]

    # Добавляем интересы
    for interest in INTERESTS[category]:
        if interest in user_interests:
            # Если интерес уже выбран, добавляем кнопку для отмены выбора
            keyboard.append([InlineKeyboardButton(
                f"{interest} [отменить выбор]",
                callback_data=f"unselect_{interest}"
            )])
        else:
            # Если интерес не выбран, оставляем обычную кнопку
            keyboard.append([InlineKeyboardButton(
                interest,
                callback_data=f"interest_{interest}"
            )])

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


# Обработчик для ввода города
async def handle_location_input(update: Update, context: CallbackContext):
    location = update.message.text
    user_id = update.effective_user.id
    interests = BotDbFunctions.get_user_interests(user_id)

    # Вызываем функцию filter_museums (пока заглушка)
    await update.message.reply_text(
        f"Ищу музеи в городе {location} по вашим интересам: {', '.join(interests)}..."
    )

    # Здесь будет вызов функции filter_museums(location, interests)
    # Например:
    # museums = filter_museums(location, interests)
    # await update.message.reply_text(museums)

    return ConversationHandler.END  # Завершаем диалог


# Обработчик для отмены поиска музеев
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Поиск музеев отменен.")
    return ConversationHandler.END


#  Обработка отмены выбора интереса (в меню /select_interests)
async def handle_unselect_interest(update: Update, context: CallbackContext):
    query = update.callback_query
    interest_name = query.data.replace("unselect_", "")
    user_id = query.from_user.id

    # Удаляем интерес
    interest_id = BotDbFunctions.get_interest_id(interest_name)
    if interest_id is None:
        await query.answer(f"Интерес '{interest_name}' не найден.")
        return

    BotDbFunctions.remove_interest(user_id, interest_id)

    # Показываем подтверждение
    await query.answer(f"Интерес '{interest_name}' больше не выбран.")

    # Обновляем список интересов
    await show_interests(update, context)


# Обработка удаления интереса (в меню /remove_interest)
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
    elif query.data.startswith("unselect_"):
        await handle_unselect_interest(update, context)
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