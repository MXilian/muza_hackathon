from src.bot.bot_handler import *
from src.db.db_setup import *


# Главная точка входа
def main():
    init_db()
    BotHandler.initialize_bot()

if __name__ == "__main__":
    main()