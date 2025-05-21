import os
import json
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from handlers.states import FeedbackStates
from utils.json_utils import load_feedback, save_feedback
from text import FEEDBACK_PROMPT, FEEDBACK_THANK_YOU, UNKNOWN_FIRST_NAME, UNKNOWN_LAST_NAME

# Настройка логирования: вывод логов только в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("feedback"))
async def ask_feedback(message: Message, state: FSMContext):
    logger.info(f"Запрос отзыва от пользователя {message.from_user.id}")
    await message.answer(FEEDBACK_PROMPT)
    await state.set_state(FeedbackStates.waiting_for_feedback)

@router.message(FeedbackStates.waiting_for_feedback)
async def save_feedback_handler(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    feedback_text = message.text
    user_file = f"data/users/user_{user_id}.json"
    logger.info(f"Получен отзыв от пользователя {user_id}: {feedback_text}")

    if os.path.exists(user_file):
        try:
            with open(user_file, "r", encoding="utf-8") as file:
                user_data = json.load(file)
            logger.info(f"Файл пользователя {user_id} найден для сохранения отзыва")
        except Exception as e:
            logger.warning(f"Ошибка чтения файла пользователя {user_id}: {e}")
            user_data = {}
        first_name = user_data.get("first_name", UNKNOWN_FIRST_NAME)
        last_name = user_data.get("last_name", UNKNOWN_LAST_NAME)
    else:
        logger.warning(f"Файл пользователя {user_id} не найден, используются значения по умолчанию")
        first_name = UNKNOWN_FIRST_NAME
        last_name = UNKNOWN_LAST_NAME

    save_feedback(user_id, feedback_text, first_name, last_name)
    logger.info(f"Отзыв сохранён для пользователя {user_id}")

    await message.answer(FEEDBACK_THANK_YOU)
    await state.clear()
