# Команды бота
COMMAND_START = "start"
COMMAND_HELP = "help"
COMMAND_PRIVACY = "privacy"
COMMAND_SELECT_INTERESTS = "select_interests"
COMMAND_REMOVE_INTEREST = "remove_interest"
COMMAND_SHOW_MY_INTERESTS = "show_my_interests"
COMMAND_MUSEUMS_FOR_ME = "museums_for_me"

# Колбэки бота
CALLBACK_SHOW_CATEGORY = "category_"
CALLBACK_MAIN_MENU = "main_menu"
CALLBACK_BACK_TO_CATEGORIES = "back_to_categories"
CALLBACK_INTEREST = "interest_"
CALLBACK_UNSELECT = "unselect_"
CALLBACK_REMOVE = "remove_"
CALLBACK_CANCEL_REMOVE = "cancel_remove"
CALLBACK_INTERESTS_DONE = "interests_done"

CONTEXT_CATEGORY = "current_category"

# Тексты сообщений

# Текст команды /help
HELP_TEXT = (
    "Доступные команды:\n"
    f"/{COMMAND_START} - Начать работу с ботом\n"
    f"/{COMMAND_SELECT_INTERESTS} - Указать свои интересы\n"
    f"/{COMMAND_REMOVE_INTEREST} - Удалить выбранные интересы\n"
    f"/{COMMAND_SHOW_MY_INTERESTS} - Показать ваши выбранные интересы\n"
    f"/{COMMAND_MUSEUMS_FOR_ME} - Найти музеи по вашим интересам\n"
    f"/{COMMAND_PRIVACY} - Политика конфиденциальности\n"
    f"/{COMMAND_HELP} - Показать список доступных команд"
)

# Текст команды /start
START_TEXT = (
    "Привет! Я бот проекта Muza.\nМогу подобрать музеи под ваши интересы. "
    "Давайте выберем куда вам сходить."
    "Расскажите что вам интересно: "
    "\n"
)

# Текст команды /privacy
PRIVACY_TEXT = (
    "Наш бот собирает только ваш Telegram ID и информацию об интересах "
    "для формирования рекомендаций музеев. Персональные данные "
    "(имя, фамилия, телефон и др.) не запрашиваются и не сохраняются. "
    "При работе с AI-моделью передаются только ваши интересы в обезличенном виде, "
    "без привязки к личной идентификации."
)
