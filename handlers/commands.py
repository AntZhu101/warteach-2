from aiogram import Bot
from aiogram.types import BotCommand

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="menu", description="Меню"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="learn", description="Начать обучение"),
        BotCommand(command="feedback", description="Оставить отзыв"),
        BotCommand(command="trainee", description="Меню наставника"),
        BotCommand(command="manager", description="Меню управляющего"),
    ]
    await bot.set_my_commands(commands)