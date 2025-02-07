import asyncio

from src.bot.bot_handler import *
from src.db.db_setup import *


# Главная точка входа
def main():
    reinit_db()
    asyncio.run(BotHandler.initialize_bot())

if __name__ == "__main__":
    main()