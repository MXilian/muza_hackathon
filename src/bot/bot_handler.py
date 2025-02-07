import logging
import os

from telegram import Update
from telegram.ext import *

from src.bot.bot_commands.callback_handler import CallbackHandler
from src.bot.bot_commands.constants import *
from src.bot.bot_commands.user_command_handler import UserCommandHandler, LOCATION_INPUT

logger = logging.getLogger(__name__)

# Обработка команд пользователя
class BotHandler:
    # Общий обработчик callback-запросов
    @staticmethod
    async def handle_callback(update: Update, context: CallbackContext):
        query = update.callback_query
        logger.error(f"Получен callback: {query.data}")
        await query.answer()

        if query.data.startswith(CALLBACK_SHOW_CATEGORY):
            await CallbackHandler.show_interests(update, context)
        elif query.data.startswith(CALLBACK_INTEREST):
            logger.error(f"on: {CALLBACK_INTEREST}")
            await CallbackHandler.handle_interest_selection(update, context)
        elif query.data == CALLBACK_BACK_TO_CATEGORIES:
            await UserCommandHandler.show_categories(update, context)
        elif query.data == CALLBACK_MAIN_MENU:
            await UserCommandHandler.help_command(update, context)
        elif query.data.startswith(CALLBACK_UNSELECT):
            await CallbackHandler.handle_unselect_interest(update, context)
        elif query.data.startswith(CALLBACK_REMOVE):
            await CallbackHandler.handle_remove_interest(update, context)
        elif query.data == CALLBACK_CANCEL_REMOVE:
            await query.edit_message_text("Операция удаления отменена.")


    # Инициализация телеграм бота
    @staticmethod
    def initialize_bot():
        bot_token = os.getenv("BOT_TOKEN")
        application = ApplicationBuilder().token(bot_token).build()

        # Регистрация ConversationHandler для команды /museums_for_me
        museums_for_me_handler = ConversationHandler(
            entry_points=[CommandHandler(COMMAND_MUSEUMS_FOR_ME, UserCommandHandler.museums_for_me)],
            states={
                LOCATION_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, CallbackHandler.handle_location_input)],
            },
            fallbacks=[CommandHandler("cancel", CallbackHandler.cancel_museum_search)],
        )

        # Регистрация команд
        application.add_handler(museums_for_me_handler)
        application.add_handler(CommandHandler(COMMAND_START, UserCommandHandler.start_command))
        application.add_handler(CommandHandler(COMMAND_HELP, UserCommandHandler.help_command))
        application.add_handler(CommandHandler(COMMAND_PRIVACY, UserCommandHandler.privacy_command))
        application.add_handler(CommandHandler(COMMAND_SELECT_INTERESTS, UserCommandHandler.show_categories))
        application.add_handler(CommandHandler(COMMAND_REMOVE_INTEREST, UserCommandHandler.remove_interest))
        application.add_handler(CommandHandler(COMMAND_SHOW_MY_INTERESTS, UserCommandHandler.show_my_interests))

        # Обработчик callback'ов
        application.add_handler(CallbackQueryHandler(
            BotHandler.handle_callback,
            pattern=".*"
        ))

        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, UserCommandHandler.handle_message))
        application.add_error_handler(CallbackHandler.error_handler)

        # Webhook setup
        port = int(os.getenv('PORT', 5000))
        webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{bot_token}"
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=bot_token,
            webhook_url=webhook_url,
        )