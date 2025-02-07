from src.bot.bot_handler import *
from src.db.db_setup import *


# Главная точка входа
async def main():
    reinit_db()
    BotHandler.initialize_bot()

if __name__ == "__main__":
    main()