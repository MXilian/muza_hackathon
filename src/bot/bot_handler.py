import os

from telegram.ext import *

from src.bot.bot_commands.callback_handler import CallbackHandler
from src.bot.bot_commands.constants import *
from src.bot.bot_commands.user_command_handler import UserCommandHandler, LOCATION_INPUT


# Обработка команд пользователя
class BotHandler:
    # Инициализация телеграм бота
    @staticmethod
    async def initialize_bot():
        bot_token = os.getenv("BOT_TOKEN")
        application = ApplicationBuilder().token(bot_token).build()

        # Регистрация ConversationHandler для /museums_for_me
        museums_for_me_handler = ConversationHandler(
            entry_points=[CommandHandler(COMMAND_MUSEUMS_FOR_ME, UserCommandHandler.museums_for_me)],
            states={
                LOCATION_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, CallbackHandler.handle_location_input)],
            },
            fallbacks=[CommandHandler("cancel", CallbackHandler.cancel_museum_search)],
        )

        # Регистрация команд
        application.add_handler(museums_for_me_handler)
        application.add_handler(CommandHandler("start", UserCommandHandler.start))
        application.add_handler(CommandHandler("help", UserCommandHandler.help_command))
        application.add_handler(CommandHandler("privacy", UserCommandHandler.privacy_command))
        application.add_handler(CommandHandler("select_interests", UserCommandHandler.select_interests))
        application.add_handler(CommandHandler("remove_interest", UserCommandHandler.remove_interest))
        application.add_handler(CommandHandler("show_my_interests", UserCommandHandler.show_my_interests))

        # Обработчики callback'ов
        application.add_handler(CallbackQueryHandler(
            CallbackHandler.handle_callback,
            pattern=r"^(category_|interest_|back_to_categories|remove_|unselect_|cancel_remove)"
        ))  # единый обработчик

        # Альтернативный вариант с разделением:
        # application.add_handler(CallbackQueryHandler(handle_callback, pattern=r"^(category_|interest_|back_to_categories)"))
        # application.add_handler(CallbackQueryHandler(handle_remove_interest, pattern=r"^(remove_|cancel_remove)"))

        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, UserCommandHandler.handle_message))
        application.add_error_handler(UserCommandHandler.error_handler)

        # Webhook setup
        port = int(os.getenv('PORT', 5000))
        webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{bot_token}"
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=bot_token,
            webhook_url=webhook_url,
        )