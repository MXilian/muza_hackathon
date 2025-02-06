from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from src.bot.bot_handler import (
    start,
    help_command,
    privacy_command,
    show_categories,
    handle_callback,
    handle_message,
    error_handler, remove_interest,
)
import os

from src.db.db_setup import reinit_db

# Главная точка входа
def main():
    reinit_db()

    bot_token = os.getenv("BOT_TOKEN")
    application = ApplicationBuilder().token(bot_token).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("privacy", privacy_command))
    application.add_handler(CommandHandler("interests", show_categories))
    application.add_handler(CommandHandler("remove_interest", remove_interest))  # исправлено имя

    # Обработчики callback'ов
    application.add_handler(CallbackQueryHandler(
        handle_callback,
        pattern=r"^(category_|interest_|back_to_categories|remove_|cancel_remove)"
    ))  # единый обработчик

    # Альтернативный вариант с разделением:
    # application.add_handler(CallbackQueryHandler(handle_callback, pattern=r"^(category_|interest_|back_to_categories)"))
    # application.add_handler(CallbackQueryHandler(handle_remove_interest, pattern=r"^(remove_|cancel_remove)"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Webhook setup
    port = int(os.getenv('PORT', 5000))
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{bot_token}"
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=bot_token,
        webhook_url=webhook_url,
    )

if __name__ == "__main__":
    main()