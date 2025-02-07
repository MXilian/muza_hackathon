import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from src.bot.bot_commands.constants import *
from src.bot.bot_db_connector import BotDbConnector
from src.interests import INTERESTS, flatten_interests
from src.llm.mistral_connector import MistralConnector
from src.llm.museum_description_generator import MuseumDescriptionGenerator
from src.llm.museum_interests_linker import MuseumInterestLinker
from src.utils.logger import log


# Обработка колбэков и фолбэков
class CallbackHandler:
    # Показ интересов выбранной категории
    @staticmethod
    async def show_interests(update: Update, context: CallbackContext):
        query = update.callback_query
        user_id = query.from_user.id

        # Определяем категорию:
        if query.data.startswith(CALLBACK_SHOW_CATEGORY):
            category = query.data.replace(CALLBACK_SHOW_CATEGORY, "")
            context.user_data[CONTEXT_CATEGORY] = category
        else:
            category = context.user_data.get(CONTEXT_CATEGORY)
        log(f"category: {category}")

        if not category:
            await query.answer("Ошибка: категория не определена.")
            return

        log(f"category: {category}")

        keyboard = [
            [InlineKeyboardButton("<< В ГЛАВНОЕ МЕНЮ", callback_data=CALLBACK_MAIN_MENU)],
            [InlineKeyboardButton("< К СПИСКУ КАТЕГОРИЙ", callback_data=CALLBACK_BACK_TO_CATEGORIES)]
        ]

        # Получаем уже выбранные интересы пользователя
        user_interests = BotDbConnector.get_user_interests(user_id)

        # Добавляем интересы
        for interest in INTERESTS[category]:
            if interest in user_interests:
                # Если интерес уже выбран, добавляем кнопку для отмены выбора
                keyboard.append([InlineKeyboardButton(
                    f"{interest} [отменить выбор]",
                    callback_data=f"{CALLBACK_UNSELECT}{interest}"
                )])
            else:
                # Если интерес не выбран, оставляем обычную кнопку
                keyboard.append([InlineKeyboardButton(
                    interest,
                    callback_data=f"{CALLBACK_INTEREST}{interest}"
                )])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Выберите интересы в категории {category}:",
            reply_markup=reply_markup
        )


    # Обработчик для ввода города
    @staticmethod
    async def handle_location_input(update: Update, context: CallbackContext):
        await update.message.reply_text(
            f"Подождите пожалуйста, осуществляется поиск. Это займет несколько минут..."
        )

        location = update.message.text
        user_id = update.effective_user.id

        # Получаем интересы пользователя
        user_interests = BotDbConnector.get_user_interests(user_id)
        log(f"[handle_location_input] user_interests: {user_interests}")

        # Если интересов нет, сообщаем об ошибке
        if not user_interests:
            await update.message.reply_text(
                "У вас пока нет выбранных интересов. Пожалуйста, сначала выберите интересы."
            )
            return ConversationHandler.END

        # Фильтруем музеи по городу
        museums = BotDbConnector.filter_museums_by_city(location, limit=35)
        log(f"[handle_location_input] museums_by_city: {museums}")

        if not museums:
            await update.message.reply_text(
                f"По вашему запросу (город: {location}) ничего не найдено."
            )
            return ConversationHandler.END

        # Получаем полный список интересов
        all_interests = flatten_interests(INTERESTS)
        log(f"[handle_location_input] all_interests: {all_interests}")

        # Связываем музеи с интересами
        mistral_connector = MistralConnector()
        linker = MuseumInterestLinker(mistral_connector)

        for museum in museums:
            # Проверяем, есть ли уже привязанные интересы
            museum_interests = BotDbConnector.get_museum_interests(museum['museum_id'])

            if not museum_interests:
                # Если интересов нет, связываем их с помощью Mistral
                linked_interests = linker.link_museum_interests(museum, all_interests)
                linker.save_linked_interests(museum['museum_id'], linked_interests)

        # Фильтруем музеи по интересам пользователя
        filtered_museums = BotDbConnector.filter_museums_by_interests(museums, user_interests)
        log(f"[MuseumInterestLinker] filtered_museums {filtered_museums}")

        # Генерируем описания с обоснованием
        description_generator = MuseumDescriptionGenerator(mistral_connector)
        descriptions = description_generator.generate_museum_descriptions(filtered_museums)

        # Разделяем descriptions на отдельные описания музеев
        museum_descriptions = descriptions.split("|||") if descriptions else []

        log(f"[handle_location_input] Отправляем пользователю описания музеев")
        try:
            # Отправляем пользователю описания музеев
            await update.message.reply_text(
                f"Вот найденные музеи по вашему запросу:"
            )
            for text in museum_descriptions:
                await update.message.reply_text(
                    f"\n\n{text}"
                )
                await asyncio.sleep(1)
        except Exception as e:
            log(f"Ошибка при отправке описаний музеев: {e}")
            await update.message.reply_text(
                f"Непредвиденный сбой. Попробуйте позже."
            )

        return ConversationHandler.END


    # Обработчик для отмены поиска музеев
    @staticmethod
    async def cancel_museum_search(update: Update, context: CallbackContext):
        await update.message.reply_text("Поиск музеев отменен.")
        return ConversationHandler.END


    # Обработка отмены выбора интереса (в меню /select_interests)
    @staticmethod
    async def handle_unselect_interest(update: Update, context: CallbackContext):
        query = update.callback_query
        interest_name = query.data.replace(CALLBACK_UNSELECT, "")
        user_id = query.from_user.id

        # Удаляем интерес
        interest_id = BotDbConnector.get_interest_id(interest_name)
        if interest_id is None:
            await query.answer(f"Интерес '{interest_name}' не найден.")
            return

        BotDbConnector.remove_interest(user_id, interest_id)

        # Показываем подтверждение
        await query.answer(f"Интерес '{interest_name}' больше не выбран.")

        # Обновляем список интересов
        await CallbackHandler.show_interests(update, context)


    # Обработка удаления интереса (в меню /remove_interest)
    @staticmethod
    async def handle_remove_interest(update: Update, context: CallbackContext):
        query = update.callback_query

        if query.data == "cancel_remove":
            await query.edit_message_text("Операция удаления отменена.")
            return

        interest_name = query.data.replace(CALLBACK_REMOVE, "")
        user_id = query.from_user.id

        # Получаем ID интереса через функцию из bot_db_functions
        interest_id = BotDbConnector.get_interest_id(interest_name)
        if interest_id is None:
            await query.answer(f"Интерес '{interest_name}' не найден.")
            return

        # Удаляем интерес через функцию из bot_db_functions
        BotDbConnector.remove_interest(user_id, interest_id)
        await query.edit_message_text(f"Интерес '{interest_name}' успешно удален.")


    # Обработка выбора интереса
    @staticmethod
    async def handle_interest_selection(update: Update, context: CallbackContext):
        query = update.callback_query
        interest = query.data.replace(CALLBACK_INTEREST, "")
        user_id = query.from_user.id

        # Добавляем интерес
        interest_id = BotDbConnector.get_interest_id(interest)
        if interest_id is None:
            await query.answer(f"Интерес '{interest}' не найден.")
            return

        BotDbConnector.add_interest(user_id, interest_id)
        await query.answer(f"Вы выбрали: {interest}")

        # Обновляем список интересов с текущей категорией
        await CallbackHandler.show_interests(update, context)


    # Функция для обработки ошибок
    @staticmethod
    async def error_handler(update, context: CallbackContext):
        log(f"Ошибка: {context.error}")