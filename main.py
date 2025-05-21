import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import API_TOKEN
from handlers import commands, mentor, profile, training, tests, feedback, menu, start, inline_handler, registration, trainee, manager
from bot_instance import bot

# Определяем базовую папку (папку, где находится main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "bot.log")

# Удаляем все существующие обработчики логгера, если они есть
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Настройка логирования: вывод логов в консоль и запись в файл (режим append)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),  # вывод в консоль
        logging.FileHandler(LOG_FILE, encoding="utf-8")  # запись в файл
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота, хранилища и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

def register_handlers():
    dp.include_router(inline_handler.router)
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(profile.router)
    dp.include_router(training.router)
    dp.include_router(tests.router)
    dp.include_router(feedback.router)
    dp.include_router(menu.router)
    dp.include_router(mentor.router)
    dp.include_router(trainee.router)
    dp.include_router(manager.router)
    logger.info("Обработчики зарегистрированы")

async def main():
    try:
        register_handlers()
        logger.info("Запуск успешно")
        await commands.set_commands(bot)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Ошибка: %s", e)

if __name__ == '__main__':
    asyncio.run(main())
