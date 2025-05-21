import os
import logging
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from aiogram.filters import Command
from utils.json_utils import load_from_json
from text import START_ALREADY_REGISTERED, START_MESSAGE
from handlers.registration import start_registration  # Импортируем функцию регистрации

router = Router()
logger = logging.getLogger(__name__)

# Команда /start
@router.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    logger.info(f"Команда /start от пользователя {user_id}")

    if load_from_json(user_id):
        await message.answer(START_ALREADY_REGISTERED)
        logger.info(f"Пользователь {user_id} уже зарегистрирован")
        return

    # Создаем инлайн-клавиатуру с кнопкой "Начать регистрацию"
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать регистрацию", callback_data="start_registration")]
        ]
    )

    image_path = os.path.join("images", "start.jpg")
    if os.path.exists(image_path):
        await message.answer_photo(
            photo=FSInputFile(image_path),
            caption=START_MESSAGE,
            reply_markup=inline_keyboard
        )
        logger.info(f"Отправлено фото-начало регистрации пользователю {user_id}")
    else:
        await message.answer(START_MESSAGE, reply_markup=inline_keyboard)
        logger.warning(f"Изображение {image_path} не найдено для пользователя {user_id}")

# Обработчик инлайн-кнопки "Начать регистрацию"
@router.callback_query(lambda c: c.data == "start_registration")
async def start_registration_callback(callback: CallbackQuery, state):
    """
    Обработчик нажатия кнопки "Начать регистрацию".
    Вызывает функцию регистрации из registration.py.
    """
    logger.info(f"Пользователь {callback.from_user.id} нажал кнопку 'Начать регистрацию'")
    # Больше не удаляем первое сообщение
    await start_registration(callback.message, state)  # Запускаем процесс регистрации