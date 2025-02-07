import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from src.bot.bot_commands.callback_handler import CallbackHandler
from src.bot.bot_commands.constants import *
from src.bot.bot_db_connector import BotDbConnector

# Состояния для ConversationHandler
LOCATION_INPUT = 1

logger = logging.getLogger(__name__)

# Обработка команд пользователя
class UserCommandHandler:
    # Функция для команды /start
    @staticmethod
    async def start(update: Update, context: CallbackContext):
        logger.debug(f"Старт комманд")
        user_id = update.effective_user.id
        logger.debug(f"TG user id: {user_id}")
        BotDbConnector.add_user(user_id)  # Сохраняем пользователя в БД
        await update.message.reply_text(START_TEXT)

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
    @staticmethod
    async def select_interests(update: Update, context: CallbackContext):
        await CallbackHandler.show_categories(update, context)

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

        if not interests:
            await update.message.reply_text("У вас пока нет выбранных интересов.")
            return

        # Формируем список интересов
        interests_list = "\n".join(f"• {interest}" for interest in interests)
        await update.message.reply_text(
            f"Ваши выбранные интересы:\n{interests_list}"
        )


    # Обработчик команды /museums_for_me
    @staticmethod
    async def museums_for_me(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        interests = BotDbConnector.get_user_interests(user_id)

        # Если интересов нет, предлагаем выбрать их
        if not interests:
            await update.message.reply_text(
                "У вас пока нет выбранных интересов. Пожалуйста, сначала выберите интересы "
                f"с помощью команды /{COMMAND_SELECT_INTERESTS}, чтобы я мог вам что-то порекомендовать."
            )
            return ConversationHandler.END  # Завершаем диалог

        # Если интересы есть, запрашиваем населенный пункт
        await update.message.reply_text(
            "Пожалуйста, введите название населенного пункта РФ, по которому осуществить поиск:"
        )
        return LOCATION_INPUT  # Переходим в состояние ожидания ввода города


    # Функция для обработки введенного сообщения
    @staticmethod
    async def handle_message(update: Update, context: CallbackContext):
        await update.message.reply_text("Я не понимаю, что вы имеете в виду. "
                                        "Пожалуйста, используйте одну из доступных команд.")

