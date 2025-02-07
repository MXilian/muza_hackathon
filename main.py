import asyncio

from src.bot.bot_handler import *
from src.db.db_setup import *


# Главная точка входа
async def main():
    reinit_db()
    await BotHandler.initialize_bot()

if __name__ == "__main__":
    asyncio.run(main())