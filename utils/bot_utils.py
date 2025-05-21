import os
import logging
from aiogram.types import FSInputFile
from bot_instance import bot

# Настройка логирования: вывод логов только в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def send_message_or_photo(chat_id, text, image=None, keyboard=None):
    if image:
        image_path = f"images/{image}"
        if os.path.exists(image_path):
            logger.info(f"Отправка изображения '{image_path}' пользователю {chat_id}")
            photo = FSInputFile(image_path)
            await bot.send_photo(chat_id, photo=photo, caption=text, reply_markup=keyboard)
        else:
            logger.warning(f"Изображение не найдено: {image_path} для пользователя {chat_id}")
            await bot.send_message(chat_id, f"{text}\n⚠️ Изображение не найдено: {image_path}", reply_markup=keyboard)
    else:
        logger.info(f"Отправка текстового сообщения пользователю {chat_id}")
        await bot.send_message(chat_id, text, reply_markup=keyboard)
