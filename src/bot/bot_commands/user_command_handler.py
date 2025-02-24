from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackContext

from src.bot.bot_commands.constants import *
from src.bot.bot_db_connector import BotDbConnector
from src.interests import INTERESTS
from src.utils.logger import log

# Состояния для ConversationHandler
LOCATION_INPUT = 1


# Обработка команд пользователя
class UserCommandHandler:
    # Функция для команды /start
    @staticmethod
    async def start_command(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        BotDbConnector.add_user(user_id)  # Сохраняем пользователя в БД
        await update.message.reply_text(START_TEXT)
        # Сразу показываем категории интересов
        await UserCommandHandler.show_categories(update, context)

    # Функция для команды /help
    @staticmethod
    async def help_command(update: Update, context: CallbackContext):
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(HELP_TEXT)
        else:
            await update.message.reply_text(HELP_TEXT)

    # Функция для команды /privacy
    @staticmethod
    async def privacy_command(update: Update, context: CallbackContext):
        await update.message.reply_text(PRIVACY_TEXT)

    # Функция для команды /select_interests
    # Выбор категории интересов
    @staticmethod
    async def show_categories(update: Update, context: CallbackContext):
        keyboard = [
            [InlineKeyboardButton("< В ГЛАВНОЕ МЕНЮ", callback_data=CALLBACK_MAIN_MENU)]
        ]
        for category in INTERESTS.keys():
            keyboard.append([InlineKeyboardButton(category, callback_data=f"{CALLBACK_SHOW_CATEGORY}{category}")])

        user_id = update.effective_user.id
        log(f'[show_categories] user_id: {user_id}')
        if user_id:
            interests = BotDbConnector.get_user_interests(user_id)
            if interests:
                keyboard.append([InlineKeyboardButton("✅ Готово", callback_data=CALLBACK_MUSEUMS_FOR_ME)])

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

    # Функция для команды /remove_interest
    @staticmethod
    async def remove_interest(update: Update, context: CallbackContext):
        user_id = update.effective_user.id

        # Получаем интересы пользователя через функцию из bot_db_functions
        interests = BotDbConnector.get_user_interests(user_id)

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

    # Функция
    # для команды /show_my_interests
    @staticmethod
    async def show_my_interests(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        interests = BotDbConnector.get_user_interests(user_id)

        # Формируем текст сообщения
        message_text = (
            "У вас пока нет выбранных интересов."
            if not interests
            else f"Ваши выбранные интересы:\n" + "\n".join(f"• {i}" for i in interests)
        )

        # Определяем контекст вызова: колбэк или команда
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(text=message_text)
        else:
            await update.message.reply_text(message_text)

    # Обработчик команды /museums_for_me
    @staticmethod
    async def museums_for_me(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        interests = BotDbConnector.get_user_interests(user_id)

        # Если интересов нет, предлагаем выбрать их, иначе запрашиваем населенный пункт
        text = "Пожалуйста, напишите название города, по которому осуществить поиск (города России, например: Москва):" \
            if interests else \
            "У вас пока нет выбранных интересов. Пожалуйста, сначала выберите интересы "
        f"с помощью команды /{COMMAND_SELECT_INTERESTS}, чтобы я мог вам что-то порекомендовать."

        # В зависимости от контекста вызова выбираем способ вывода текста
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(text)
        else:
            await update.message.reply_text(text)

        # Переходим в состояние ожидания ввода города либо завершаем диалог
        return LOCATION_INPUT if interests else ConversationHandler.END

    # Функция для обработки введенного сообщения
    @staticmethod
    async def handle_message(update: Update, context: CallbackContext):
        await update.message.reply_text("Я не понимаю, что вы имеете в виду. "
                                        "Пожалуйста, используйте одну из доступных команд.")
