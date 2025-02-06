from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from src.bot.bot_commands.constants import *
from src.bot.bot_db_connector import BotDbConnector
from src.bot.bot_commands.user_command_handler import UserCommandHandler
from src.interests import INTERESTS


# Обработка колбэков и фолбэков
class CallbackHandler:
    # Выбор категории интересов
    @staticmethod
    async def show_categories(update: Update, context: CallbackContext):
        keyboard = [
            [InlineKeyboardButton("< В ГЛАВНОЕ МЕНЮ", callback_data=CALLBACK_MAIN_MENU)]
        ]
        for category in INTERESTS.keys():
            keyboard.append([InlineKeyboardButton(category, callback_data=f"{CALLBACK_SHOW_CATEGORY}{category}")])

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
    @staticmethod
    async def show_interests(update: Update, context: CallbackContext):
        query = update.callback_query
        user_id = query.from_user.id
        category = context.user_data.get(CONTEXT_CATEGORY)

        # Получаем уже выбранные интересы пользователя
        user_interests = BotDbConnector.get_user_interests(user_id)

        keyboard = [
            [InlineKeyboardButton("<< В ГЛАВНОЕ МЕНЮ", callback_data=CALLBACK_MAIN_MENU)],
            [InlineKeyboardButton("< К СПИСКУ КАТЕГОРИЙ", callback_data=CALLBACK_BACK_TO_CATEGORIES)]
        ]

        # Добавляем интересы
        for interest in INTERESTS[category]:
            if interest in user_interests:
                # Если интерес уже выбран, добавляем кнопку для отмены выбора
                keyboard.append([InlineKeyboardButton(
                    f"{interest} [отменить выбор]",
                    callback_data=f"{CALLBACK_UNSELECT}{interest}"
                )])
            else:
                # Если интерес не выбран, оставляем обычную кнопку
                keyboard.append([InlineKeyboardButton(
                    interest,
                    callback_data=f"{CALLBACK_INTEREST}{interest}"
                )])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Выберите интересы в категории {category}:",
            reply_markup=reply_markup
        )

    # Обработчик для ввода города
    @staticmethod
    async def handle_location_input(update: Update, context: CallbackContext):
        location = update.message.text
        user_id = update.effective_user.id
        interests = BotDbConnector.get_user_interests(user_id)

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
    @staticmethod
    async def cancel_museum_search(update: Update, context: CallbackContext):
        await update.message.reply_text("Поиск музеев отменен.")
        return ConversationHandler.END

    # Обработка отмены выбора интереса (в меню /select_interests)
    @staticmethod
    async def handle_unselect_interest(update: Update, context: CallbackContext):
        query = update.callback_query
        interest_name = query.data.replace(CALLBACK_UNSELECT, "")
        user_id = query.from_user.id

        # Удаляем интерес
        interest_id = BotDbConnector.get_interest_id(interest_name)
        if interest_id is None:
            await query.answer(f"Интерес '{interest_name}' не найден.")
            return

        BotDbConnector.remove_interest(user_id, interest_id)

        # Показываем подтверждение
        await query.answer(f"Интерес '{interest_name}' больше не выбран.")

        # Обновляем список интересов
        await CallbackHandler.show_interests(update, context)

    # Обработка удаления интереса (в меню /remove_interest)
    @staticmethod
    async def handle_remove_interest(update: Update, context: CallbackContext):
        query = update.callback_query

        if query.data == "cancel_remove":
            await query.edit_message_text("Операция удаления отменена.")
            return

        interest_name = query.data.replace(CALLBACK_REMOVE, "")
        user_id = query.from_user.id

        # Получаем ID интереса через функцию из bot_db_functions
        interest_id = BotDbConnector.get_interest_id(interest_name)
        if interest_id is None:
            await query.answer(f"Интерес '{interest_name}' не найден.")
            return

        # Удаляем интерес через функцию из bot_db_functions
        BotDbConnector.remove_interest(user_id, interest_id)
        await query.edit_message_text(f"Интерес '{interest_name}' успешно удален.")

    # Обработка выбора интереса
    @staticmethod
    async def handle_interest_selection(update: Update, context: CallbackContext):
        query = update.callback_query
        interest = query.data.replace(CALLBACK_INTEREST, "")
        user_id = query.from_user.id

        # Добавляем интерес
        interest_id = BotDbConnector.get_interest_id(interest)
        if interest_id is None:
            await query.answer(f"Интерес '{interest}' не найден.")
            return

        BotDbConnector.add_interest(user_id, interest_id)
        await query.answer(f"Вы выбрали: {interest}")

        # Обновляем список интересов с текущей категорией
        await CallbackHandler.show_interests(update, context)

    # Общий обработчик callback-запросов
    @staticmethod
    async def handle_callback(update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        if query.data.startswith(CALLBACK_SHOW_CATEGORY):
            category = query.data.replace(CALLBACK_SHOW_CATEGORY, "")
            context.user_data[CONTEXT_CATEGORY] = category
            await CallbackHandler.show_interests(update, context)
        elif query.data.startswith(CALLBACK_INTEREST):
            await CallbackHandler.handle_interest_selection(update, context)
        elif query.data == CALLBACK_BACK_TO_CATEGORIES:
            await CallbackHandler.show_categories(update, context)
        elif query.data == CALLBACK_MAIN_MENU:
            await UserCommandHandler.help_command(update, context)
        elif query.data.startswith(CALLBACK_UNSELECT):
            await CallbackHandler.handle_unselect_interest(update, context)
        elif query.data.startswith(CALLBACK_REMOVE):
            await CallbackHandler.handle_remove_interest(update, context)
        elif query.data == CALLBACK_CANCEL_REMOVE:
            await query.edit_message_text("Операция удаления отменена.")