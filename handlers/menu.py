import logging
from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters.callback_data import CallbackData
from text import MENU_TEXT
from utils.json_utils import load_user_data, save_user_data  # Импортируем функции работы с JSON

# Настройка логирования: вывод логов только в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = Router()

# Определяем callback_data для профиля
class ProfileCallbackData(CallbackData, prefix="profile"):
    action: str

# Определяем callback_data для заданий
class AssignmentsCallbackData(CallbackData, prefix="assignments"):
    action: str

async def show_menu(message: types.Message):
    """Показывает главное меню."""
    logger.info(f"Отправка главного меню пользователю {message.from_user.id}")

    # Загружаем данные пользователя
    user_id = message.from_user.id
    user_data = load_user_data(user_id)

    # Проверяем, является ли пользователь наставником
    is_mentor = user_data.get("role") == "mentor" if user_data else False

    # Формируем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Профиль", callback_data=ProfileCallbackData(action="show_profile").pack())],
        [InlineKeyboardButton(text="Мои задания", callback_data=AssignmentsCallbackData(action="show_assignments").pack())],
        [InlineKeyboardButton(text="Обучение", callback_data="training")],
        [InlineKeyboardButton(text="Обратная связь", callback_data="feedback")],
        [InlineKeyboardButton(text="Курсы", callback_data="courses")],
    ])

    # Если пользователь наставник, добавляем кнопку "Меню наставника"
    if is_mentor:
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="Меню наставника", callback_data="mentor_menu")]
        )

    await message.answer(MENU_TEXT, reply_markup=keyboard)

@router.message(Command("menu"))
async def menu_command(message: types.Message):
    logger.info(f"Команда /menu от пользователя {message.from_user.id}")
    await show_menu(message)

@router.message(lambda message: message.text == "/trainee")
async def show_trainees(message: Message):
    """
    Команда /trainee для отображения списка стажеров наставника.
    """
    user_id = message.from_user.id

    # Загружаем данные наставника
    mentor_data = load_user_data(user_id)
    if not mentor_data or mentor_data.get("role") != "mentor":
        await message.answer("Вы не являетесь наставником. У вас нет доступа к этой команде.")
        logger.warning(f"Пользователь {user_id} пытался открыть список стажеров, не являясь наставником.")
        return

    # Получаем список стажеров
    trainees = mentor_data.get("Trainee", {})
    if not trainees:
        await message.answer("У вас пока нет стажеров.")
        logger.info(f"У наставника {user_id} нет стажеров.")
        return

    # Формируем сообщение
    message_text = "У вас проходят стажировку сотрудники. Выберите стажера из списка ниже для просмотра подробной информации."

    # Формируем инлайн-кнопки для каждого стажера
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{data.get('first_name', 'Неизвестно')} {data.get('last_name', 'Неизвестно')}",
                callback_data=f"trainee_details:{trainee_id}"
            )]
            for trainee_id, data in trainees.items()
        ]
    )

    await message.answer(message_text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "mentor_menu")
async def mentor_menu_command(callback_query: types.CallbackQuery, bot: Bot):
    """
    Обработчик кнопки 'Меню наставника'.
    Открывает меню для наставника, аналогичное команде /trainee.
    """
    logger.info(f"Кнопка 'Меню наставника' нажата пользователем {callback_query.from_user.id}")
    
    # Удаляем старое сообщение
    try:
        await bot.delete_message(
            chat_id=callback_query.message.chat.id, 
            message_id=callback_query.message.message_id
        )
        logger.info("Старое сообщение удалено")
    except Exception as e:
        logger.warning(f"Ошибка удаления сообщения: {e}")
    
    # Загружаем данные наставника
    user_id = callback_query.from_user.id
    mentor_data = load_user_data(user_id)
    if not mentor_data or mentor_data.get("role") != "mentor":
        await callback_query.message.answer("Вы не являетесь наставником. У вас нет доступа к этому меню.")
        logger.warning(f"Пользователь {user_id} пытался открыть меню наставника, не являясь наставником.")
        await callback_query.answer()
        return

    # Получаем список стажеров
    trainees = mentor_data.get("Trainee", {})
    if not trainees:
        await callback_query.message.answer("У вас пока нет стажеров.")
        logger.info(f"У наставника {user_id} нет стажеров.")
        await callback_query.answer()
        return

    # Формируем сообщение
    message_text = "У вас проходят стажировку сотрудники. Выберите стажера из списка ниже для просмотра подробной информации."

    # Формируем инлайн-кнопки для каждого стажера
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{data.get('first_name', 'Неизвестно')} {data.get('last_name', 'Неизвестно')}",
                callback_data=f"trainee_details:{trainee_id}"
            )]
            for trainee_id, data in trainees.items()
        ]
    )

    await callback_query.message.answer(message_text, reply_markup=keyboard)
    await callback_query.answer()