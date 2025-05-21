import logging
import os
from pathlib import Path
from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from utils.json_utils import load_user_data  # Импортируем функцию для работы с JSON

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = Router()

@router.message(lambda message: message.text == "/manager")
async def manager_command(message: Message):
    """
    Обработчик команды /Manager для отображения меню управляющего.
    """
    user_id = message.from_user.id

    # Загружаем данные пользователя
    user_data = load_user_data(user_id)
    if not user_data or user_data.get("role") != "Manager":
        # Если пользователь не управляющий, выводим сообщение об отсутствии доступа
        await message.answer("У вас нет доступа к этой команде. Данная функция доступна только для управляющих.")
        logger.warning(f"Пользователь {user_id} пытался открыть меню управляющего, не являясь управляющим.")
        return

    # Формируем сообщение и клавиатуру для меню управляющего
    message_text = "Добро пожаловать в меню управляющего. Выберите нужный раздел:"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сотрудники", callback_data="manager_employees")],
            [InlineKeyboardButton(text="Наставники", callback_data="manager_mentors")],
            [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")],
        ]
    )

    await message.answer(message_text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "manager_employees")
async def show_employees(callback: CallbackQuery):
    user_id = callback.from_user.id
    manager_data = load_user_data(user_id)
    if not manager_data or manager_data.get("role") != "Manager":
        await callback.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    manager_city = manager_data.get("city")
    if not manager_city:
        await callback.answer("Ошибка: ваша локация не указана в профиле.", show_alert=True)
        return

    employees = []
    users_dir = Path("data/users")
    for file_path in users_dir.glob("user_*.json"):
        # вынимаем id из имени файла, например из "user_12345.json" → 12345
        try:
            emp_id = int(file_path.stem.split("_", 1)[1])
        except (IndexError, ValueError):
            continue
        if emp_id == user_id:
            continue

        emp_data = load_user_data(emp_id)
        if not emp_data:
            continue

        if emp_data.get("city") == manager_city and emp_data.get("role") in ("Trainee", "Employee"):
            full_name = f"{emp_data.get('first_name', '')} {emp_data.get('last_name', '')}".strip()
            employees.append((full_name or "— Без имени —", emp_id))

    if not employees:
        await callback.message.edit_text("Нет сотрудников в вашей локации.")
        return

    # строим клавиатуру
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(name, callback_data=f"employee_details:{eid}")]
            for name, eid in employees
        ]
    )
    # заменяем сообщение
    await callback.message.delete()
    await callback.message.answer("Выберите сотрудника:", reply_markup=kb)
    await callback.answer()
