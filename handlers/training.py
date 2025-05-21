import os
import json
import logging
from aiogram import Dispatcher, types, Router, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from bot_instance import bot
from .tests import send_test_question
from utils.json_utils import load_training_data, load_user_data, save_user_data
from utils.bot_utils import send_message_or_photo
from utils.course_plan import initialize_course_plan
from utils import bot_utils
from text import (
    LEARN_PROFILE_NOT_FOUND, SECTION_DATA_NOT_FOUND, LESSON_MATERIAL_NOT_FOUND,
    TRAINING_COMPLETE, NEXT_LESSON_ERROR_PROFILE_NOT_FOUND
)

router = Router()

# Настройка логирования: вывод логов только в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

@router.message(Command("learn"))
async def start_learning(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = load_user_data(user_id)

    if not user_data:
        logger.warning("Профиль пользователя %s не найден при запуске обучения", user_id)
        await message.answer(LEARN_PROFILE_NOT_FOUND)
        return

    await send_lesson(user_id, message.chat.id, state)

@router.callback_query(lambda c: c.data == "training")
async def training_handler(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    logger.info("Callback 'training' получен от пользователя %s", callback_query.from_user.id)
    try:
        await bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )
        logger.info("Предыдущее сообщение успешно удалено")
    except Exception as e:
        logger.warning("Ошибка удаления сообщения: %s", e)

    # Ленивый импорт для избежания циклических зависимостей
    from .training import start_learning
    await start_learning(callback_query, state)
    await callback_query.answer()

async def start_learning(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_data = load_user_data(user_id)

    if not user_data:
        logger.warning("Профиль пользователя %s не найден при запуске обучения (callback)", user_id)
        await callback_query.message.answer(LEARN_PROFILE_NOT_FOUND)
        return

    await send_lesson(user_id, callback_query.message.chat.id, state)

# Отправка следующего урока или теста
async def send_lesson(user_id, chat_id, state: FSMContext, message_id=None):
    user_data = load_user_data(user_id)
    if not user_data:
        logger.warning("Профиль пользователя %s не найден при отправке урока", user_id)
        return await bot.send_message(chat_id, LEARN_PROFILE_NOT_FOUND)

    course_plan = user_data.get("course_plan", {})
    training_data = load_training_data()

    for section, lessons in course_plan.items():
        if section not in training_data:
            logger.error("Данные раздела '%s' не найдены в обучающих материалах", section)
            return await bot.send_message(chat_id, SECTION_DATA_NOT_FOUND.format(section=section))

        for lesson in lessons:
            if lesson["status"] == "not completed":
                lesson_name = lesson["title"]

                # Проверяем, является ли это тестом
                if lesson_name in training_data[section] and "Вопрос 1" in training_data[section][lesson_name]:
                    logger.info("Отправка теста '%s' пользователю %s", lesson_name, user_id)
                    return await send_test_question(user_id, chat_id, section, lesson_name, 1, state)

                lesson_data = training_data[section].get(lesson_name)
                if not lesson_data:
                    logger.error("Материал урока '%s' не найден", lesson_name)
                    return await bot.send_message(chat_id, LESSON_MATERIAL_NOT_FOUND.format(lesson_name=lesson_name))

                text = lesson_data.get("text", "Материал отсутствует.")
                image = lesson_data.get("image", None)

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="➡ Далее", callback_data=f"next_{section}_{lesson_name}")]
                    ]
                )

                logger.info("Отправка урока '%s' пользователю %s", lesson_name, user_id)
                await send_message_or_photo(chat_id, text, image, keyboard)

                if message_id:
                    try:
                        await bot.delete_message(chat_id, message_id)
                        logger.info("Предыдущее сообщение удалено")
                    except Exception as e:
                        logger.warning("Ошибка удаления сообщения: %s", e)
                return

    logger.info("Обучение завершено для пользователя %s", user_id)
    await bot.send_message(chat_id, TRAINING_COMPLETE)

@router.callback_query(lambda call: call.data.startswith("next_"))
async def next_lesson(call: types.CallbackQuery, state: FSMContext):
    logger.info("Callback 'next_lesson' вызван от пользователя %s с данными: %s", call.from_user.id, call.data)

    try:
        _, section, lesson_name = call.data.split("_", 2)
    except Exception as e:
        logger.error("Ошибка обработки callback data: %s", e)
        return

    user_id = call.from_user.id
    user_data = load_user_data(user_id)
    if not user_data:
        logger.warning("Профиль пользователя %s не найден при переходе к следующему уроку", user_id)
        await call.answer(NEXT_LESSON_ERROR_PROFILE_NOT_FOUND, show_alert=True)
        return

    # Обновляем статус текущего урока
    for lesson in user_data["course_plan"].get(section, []):
        if lesson["title"] == lesson_name:
            lesson["status"] = "completed"
            logger.info("Урок '%s' завершен для пользователя %s", lesson_name, user_id)
            break

    save_user_data(user_id, user_data)

    # Удаляем старое сообщение (проверяем на ошибки)
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        logger.info("Предыдущее сообщение удалено")
    except Exception as e:
        logger.warning("Ошибка удаления сообщения: %s", e)

    # Переход к следующему уроку
    logger.info("Отправка следующего урока пользователю %s", user_id)
    await send_lesson(user_id, call.message.chat.id, state)