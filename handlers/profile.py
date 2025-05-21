import os
import json
import logging
from aiogram import Router, F, Bot, types
from aiogram.types import Message, FSInputFile, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Настройка логирования: вывод логов только в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

router = Router()

# Состояния для редактирования профиля
class EditProfile(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_mentor = State()
    waiting_for_email = State()

class MenuCallbackData:
    action = "back_to_menu"

class EditCallbackData:
    action = "edit_profile"

class AssignmentsCallbackData:
    action = "my_assignments"

async def profile_command(event: Message | CallbackQuery):
    """Выводит профиль пользователя с кнопками 'Меню', 'Редактировать' и 'Мои задания'."""
    user_id = event.from_user.id
    filename = f"data/users/user_{user_id}.json"
    image_path = "images/profile.jpg"

    if not os.path.exists(filename):
        text = "❌ *Профиль не найден.*\nЗаполните анкету командой /start."
        logger.warning(f"Профиль не найден для пользователя {user_id} (файл {filename} отсутствует)")
        if isinstance(event, Message):
            await event.answer(text, parse_mode="Markdown")
        elif isinstance(event, CallbackQuery):
            await event.message.answer(text, parse_mode="Markdown")
        return

    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    logger.info(f"Загружен профиль пользователя {user_id}")

    profile_text = (
        f"📌 *Ваш профиль:*\n"
        f"📅 Дата регистрации: {data.get('registration_date', 'Не указана')}\n"
        f"👤 Имя: {data.get('first_name', 'Не указано')} {data.get('last_name', 'Не указано')}\n"
        f"💼 Должность: {data.get('position', 'Не указана')}\n"
        f"👥 Ментор: {data.get('mentor_name', 'Не указан')}\n"
        f"🌍 Локация: {data.get('city', 'Не указан')}, {data.get('location', 'Не указана')}\n"
        f"📧 Email: {data.get('email', 'Не указан')}\n"
        f"📞 Телефон: {data.get('phone_number', 'Не указан')}\n"
        f"🎮 VR-Room: {data.get('vr_room', 'Не указан')}\n"
        f"🎢 VR-Extreme: {', '.join([key for key, val in data.get('attractions', {}).items() if val == 'Есть']) or 'Нет'}\n"
        f"🪙 Warcoin: {data.get('warcoin', 0)}\n"
        f"📚 Курс обучения: {data.get('course', 'Не инициализирован')}\n"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Меню", callback_data=MenuCallbackData.action)],
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=EditCallbackData.action)],
            [InlineKeyboardButton(text="📋 Мои задания", callback_data=AssignmentsCallbackData.action)]
        ]
    )

    if os.path.exists(image_path):
        logger.info(f"Отправка профиля с изображением для пользователя {user_id}")
        if isinstance(event, Message):
            await event.answer_photo(photo=FSInputFile(image_path), caption=profile_text, parse_mode="Markdown", reply_markup=keyboard)
        elif isinstance(event, CallbackQuery):
            await event.message.answer_photo(photo=FSInputFile(image_path), caption=profile_text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        logger.info(f"Изображение профиля не найдено. Отправка только текста для пользователя {user_id}")
        if isinstance(event, Message):
            await event.answer(profile_text, parse_mode="Markdown", reply_markup=keyboard)
        elif isinstance(event, CallbackQuery):
            await event.message.answer(profile_text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == AssignmentsCallbackData.action)
async def show_assignments(callback_query: CallbackQuery, bot: Bot):
    """Показывает задания пользователя из раздела 'mistakes'."""
    user_id = callback_query.from_user.id
    filename = f"data/users/user_{user_id}.json"

    if not os.path.exists(filename):
        logger.warning(f"Профиль не найден для пользователя {user_id} (файл {filename} отсутствует)")
        await callback_query.answer("Профиль не найден.", show_alert=True)
        return

    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    mistakes = data.get("mistakes", [])
    if not mistakes:
        assignments_text = "✅ У вас нет заданий для выполнения. Все ошибки пройдены!"
    else:
        assignments_text = "📋 *Ваши задания:*\n\n"
        for i, mistake in enumerate(mistakes, start=1):
            assignments_text += f"{i}. {mistake['quest']}\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📌 Профиль", callback_data="back_to_profile")],
            [InlineKeyboardButton(text="🔙 Меню", callback_data=MenuCallbackData.action)],
        ]
    )

    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        logger.info("Старое сообщение удалено")
    except Exception as e:
        logger.warning(f"Ошибка удаления сообщения: {e}")

    await callback_query.message.answer(assignments_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(lambda c: c.data == "back_to_profile")
async def back_to_profile(callback_query: CallbackQuery, bot: Bot):
    """Возвращает пользователя к просмотру профиля."""
    logger.info(f"Callback 'back_to_profile' от пользователя {callback_query.from_user.id}")
    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        logger.info("Старое сообщение удалено")
    except Exception as e:
        logger.warning(f"Ошибка удаления сообщения: {e}")

    await profile_command(callback_query)
    await callback_query.answer()

@router.callback_query(lambda c: c.data == MenuCallbackData.action)
async def main_menu_handler(callback_query: CallbackQuery, bot: Bot):
    logger.info(f"Callback 'back_to_menu' от пользователя {callback_query.from_user.id}")
    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        logger.info("Старое сообщение удалено")
    except Exception as e:
        logger.warning(f"Ошибка удаления сообщения: {e}")

    from handlers.menu import show_menu
    await show_menu(callback_query.message)
    await callback_query.answer()