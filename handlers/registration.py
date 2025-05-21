import datetime
import logging
import re
from aiogram import Router, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
import re
import datetime
import logging
from aiogram import Router
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
)
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from handlers.states import ProfileStates
from utils.api_client import upsert_employee
from utils.json_utils import load_locations
from utils.course_plan import initialize_course_plan
from text import (
    INVALID_EMAIL, SEND_PHONE_NUMBER, USE_BUTTON_FOR_PHONE,
    INVALID_WARPOINT_LOCATION, REGISTRATION_SUCCESS_MESSAGE,
    CHOOSE_VR_ROOM, CHOOSE_VR_EXTREME, REGISTRATION_COMPLETE
)
from aiogram import Router
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
)
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
import datetime
import logging

from handlers.states import ProfileStates
from utils.api_client import upsert_employee
from utils.course_plan import initialize_course_plan
from text import (
    CHOOSE_VR_ROOM, CHOOSE_VR_EXTREME, INVALID_VR_EXTREME,
    CHOOSE_ATTRACTIONS, ATTRACT_SELECTION_PROMPT, BUTTONS_ALREADY_IN_STATE,
    REGISTRATION_COMPLETE, REGISTRATION_SUCCESS_MESSAGE
)
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from handlers.states import ProfileStates
from utils.api_client import upsert_employee, get_mentors
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.states import ProfileStates
from utils.api_client import upsert_employee
from utils.json_utils import load_locations  # для списка городов
from utils.course_plan import initialize_course_plan
from text import (
    CHOOSE_POSITION_PROMPT, INVALID_POSITION,
    ENTER_FIRST_NAME, ENTER_LAST_NAME, CHOOSE_CITY_PROMPT,
    ENTER_EMAIL, INVALID_EMAIL, SEND_PHONE_NUMBER, USE_BUTTON_FOR_PHONE,
    CHOOSE_WARPOINT_LOCATION, INVALID_WARPOINT_LOCATION,
    REGISTRATION_SUCCESS_MESSAGE, CHOOSE_VR_ROOM, CHOOSE_VR_EXTREME,
    INVALID_VR_EXTREME, CHOOSE_ATTRACTIONS, ATTRACT_SELECTION_PROMPT,
    BUTTONS_ALREADY_IN_STATE, REGISTRATION_COMPLETE
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Начать регистрацию")
async def start_registration(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # создаём или обновляем профиль в Django API
    await upsert_employee({'telegram_id': user_id})

    await state.set_state(ProfileStates.position)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Оператор")],
            [KeyboardButton(text="Администратор")],
            [KeyboardButton(text="Хостесс")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("На какую должность ты пришел работать?", reply_markup=keyboard)

@router.message(StateFilter(ProfileStates.position))
async def enter_position(message: Message, state: FSMContext):
    logger.info(f"Received position: {message.text}")
    choice = message.text
    if choice not in ["Оператор", "Администратор", "Хостесс"]:
        await message.answer("Пожалуйста, выберите должность из предложенных вариантов.")
        return

    # обновляем должность через API
    await upsert_employee({
        'telegram_id': message.from_user.id,
        'position': choice,
        'role': 'Trainee',
        'registration_date': datetime.date.today().isoformat()
    })

    await state.set_state(ProfileStates.first_name)
    await message.answer("Введите ваше имя:", reply_markup=ReplyKeyboardRemove())
# 3) Ввод имени
@router.message(StateFilter(ProfileStates.first_name))
async def enter_first_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.text.strip()

    await upsert_employee({
        'telegram_id': user_id,
        'first_name': first_name,
    })
    await state.update_data(first_name=first_name)

    await state.set_state(ProfileStates.last_name)
    await message.answer(ENTER_LAST_NAME)


# 4) Ввод фамилии
@router.message(StateFilter(ProfileStates.last_name))
async def enter_last_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    last_name = message.text.strip()

    await upsert_employee({
        'telegram_id': user_id,
        'last_name': last_name,
    })
    await state.update_data(last_name=last_name)

    await state.set_state(ProfileStates.city)
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать город", switch_inline_query_current_chat="")]
        ]
    )
    await message.answer(CHOOSE_CITY_PROMPT, reply_markup=inline_kb)


# 5) Обработчик выбора города
@router.message(StateFilter(ProfileStates.city))
async def handle_city_selection(message: Message, state: FSMContext):
    user_id = message.from_user.id
    city_info = message.text.strip()

    # Получаем список из utils/json_utils
    locations = load_locations()
    valid_cities = [f"{loc['title']} {loc['city']} {loc['address']}" for loc in locations]

    if city_info not in valid_cities:
        inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Выбрать город", switch_inline_query_current_chat="")]
            ]
        )
        await message.answer("Пожалуйста, выберите ваш город из списка:", reply_markup=inline_kb)
        return

    await upsert_employee({
        'telegram_id': user_id,
        'city': city_info,
    })
    await state.update_data(city=city_info)

    # Переходим дальше к выбору наставника
    await show_mentors(message, state)

async def show_mentors(message: Message, state: FSMContext):
    data = await state.get_data()
    # Предполагаем, что city хранится в формате "Title City Address"
    # Извлекаем второе слово (название города) и приводим к нижнему регистру
    parts = data.get("city", "").split()
    selected_city = parts[1].lower() if len(parts) > 1 else ""
    current_user_id = message.from_user.id

    # GET-запрос к API для получения списка менторов в этом городе
    mentors_list = await get_mentors(city=selected_city, role="mentor")
    # Отфильтруем себя, если вдруг попал в список
    mentors = [m for m in mentors_list if m["telegram_id"] != current_user_id]

    if not mentors:
        # Если наставников нет — сразу дёргаем следующий шаг
        await upsert_employee({
            "telegram_id": current_user_id,
            "mentor": None
        })
        await state.set_state(ProfileStates.email)
        await message.answer("Введите ваш email:")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{m['first_name']} {m['last_name']}",
                    callback_data=f"select_mentor:{m['telegram_id']}"
                )
            ]
            for m in mentors
        ]
    )
    await message.answer("Выберите наставника из доступных:", reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("select_mentor:"))
async def select_mentor(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    mentor_id = int(callback.data.split(":", 1)[1])

    # Обновляем профиль пользователя, записывая выбранного наставника
    await upsert_employee({
        "telegram_id": user_id,
        "mentor": mentor_id
    })

    await callback.answer("Наставник успешно выбран!")
    await state.set_state(ProfileStates.email)
    await callback.message.answer("Введите ваш email:")


router = Router()
logger = logging.getLogger(__name__)

# Ввод email
@router.message(StateFilter(ProfileStates.email))
async def enter_email(message: Message, state: FSMContext):
    user_id = message.from_user.id
    email = message.text.strip()

    # Проверка email
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, email):
        await message.answer("Некорректный адрес электронной почты. Пожалуйста, введите email в формате example@domain.com.")
        logger.warning(f"Пользователь {user_id} ввел некорректный email: {email}")
        return

    # Обновляем через API
    await upsert_employee({
        'telegram_id': user_id,
        'email': email,
    })
    await state.update_data(email=email)
    logger.info(f"Пользователь {user_id} ввел email: {email}")

    # Переход к вводу телефона
    await state.set_state(ProfileStates.phone_number)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить контакт", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Пожалуйста, отправьте ваш номер телефона, используя кнопку ниже:", reply_markup=keyboard)


# Ввод номера телефона
@router.message(StateFilter(ProfileStates.phone_number))
async def enter_phone_number(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not message.contact:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отправить контакт", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer("Пожалуйста, используйте кнопку для отправки вашего номера телефона:", reply_markup=keyboard)
        return

    phone_number = message.contact.phone_number
    await state.update_data(phone_number=phone_number)
    await upsert_employee({
        'telegram_id': user_id,
        'phone_number': phone_number,
    })
    logger.info(f"Пользователь {user_id} отправил номер телефона: {phone_number}")

    # Переход к выбору локации Warpoint
    await state.set_state(ProfileStates.warpoint_location)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Warpoint Park")],
            [KeyboardButton(text="Warpoint Arena")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите вашу локацию Warpoint:", reply_markup=keyboard)


# Ввод локации Warpoint
@router.message(StateFilter(ProfileStates.warpoint_location))
async def enter_warpoint_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    location = message.text.strip()

    if location not in ["Warpoint Park", "Warpoint Arena"]:
        await message.answer(INVALID_WARPOINT_LOCATION)
        logger.warning(f"Пользователь {user_id} выбрал неверную локацию: {location}")
        return

    await state.update_data(warpoint_location=location)
    await upsert_employee({
        'telegram_id': user_id,
        'warpoint_location': location,
    })
    logger.info(f"Пользователь {user_id} выбрал локацию: {location}")

    # Если Arena — сразу завершаем
    if location == "Warpoint Arena":
        # Сбрасываем VR и attractions, формируем курс
        await upsert_employee({
            'telegram_id': user_id,
            'vr_room': False,
            'vr_extreme': False,
            'attractions': {},
        })
        data = await state.get_data()
        data.update({'telegram_id': user_id})
        data = initialize_course_plan(data)
        # можно отправить init request, если нужно
        await state.clear()

        await message.answer_video(
            video=FSInputFile("video/complete_start.MP4"),
            caption=REGISTRATION_SUCCESS_MESSAGE,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"Регистрация завершена для пользователя {user_id} (Warpoint Arena)")
        return

    await state.set_state(ProfileStates.vr_room)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Да")], [KeyboardButton(text="Нет")]],
        resize_keyboard=True
    )
    await message.answer(CHOOSE_VR_ROOM, reply_markup=keyboard)


router = Router()
logger = logging.getLogger(__name__)

ATTRACTION_NAMES = ["Twister", "VR-Helicopter", "VR-Eggs", "Emotion"]

async def _update_user(data: dict):
    """Helper to send updates to Django API."""
    await upsert_employee(data)

def get_attractions_keyboard(attractions: dict) -> InlineKeyboardMarkup:
    buttons = []
    for name in ATTRACTION_NAMES:
        status = attractions.get(name, "Нет")
        icon = "✅" if status == "Да" else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {name}",
            callback_data=f"toggle_attraction:{name}"
        )])
    buttons.append([InlineKeyboardButton(text="✅ Закончить выбор", callback_data="finish_selection")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Ввод VR-Room
@router.message(StateFilter(ProfileStates.vr_room))
async def process_vr_room(message: Message, state: FSMContext):
    user_id = message.from_user.id
    choice = message.text.strip()
    await _update_user({'telegram_id': user_id, 'vr_room': choice})
    logger.info(f"Пользователь {user_id} выбрал VR-Room: {choice}")

    await state.set_state(ProfileStates.vr_extreme)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Да")], [KeyboardButton("Нет")]],
        resize_keyboard=True
    )
    await message.answer(CHOOSE_VR_EXTREME, reply_markup=keyboard)

# Ввод VR-Extreme
@router.message(StateFilter(ProfileStates.vr_extreme))
async def process_vr_extreme(message: Message, state: FSMContext):
    user_id = message.from_user.id
    vr_extreme_choice = message.text.strip()
    if vr_extreme_choice not in ["Да", "Нет"]:
        await message.answer(INVALID_VR_EXTREME)
        logger.warning(f"Пользователь {user_id} ввёл неверный выбор: {vr_extreme_choice}")
        return

    await _update_user({'telegram_id': user_id, 'vr_extreme': vr_extreme_choice})
    logger.info(f"Пользователь {user_id} выбрал VR-Extreme: {vr_extreme_choice}")

    if vr_extreme_choice == "Нет":
        defaults = {
            'attractions': {name: "Нет" for name in ATTRACTION_NAMES},
            'warcoin': 0
        }
        await _update_user({'telegram_id': user_id, **defaults})

        # Инициализируем курс и сохраняем полный план
        data = await state.get_data()
        data['user_id'] = user_id
        full_plan = initialize_course_plan(data)
        await _update_user({'telegram_id': user_id, **full_plan})

        await state.clear()
        await message.answer(REGISTRATION_COMPLETE, reply_markup=ReplyKeyboardRemove())
        logger.info(f"Регистрация завершена для пользователя {user_id} (без VR-Extreme)")
    else:
        # Переходим к выбору аттракционов
        await state.update_data(attractions={name: "Нет" for name in ATTRACTION_NAMES})
        await state.set_state(ProfileStates.attractions)
        await message.answer(CHOOSE_ATTRACTIONS, reply_markup=ReplyKeyboardRemove())
        await message.answer(
            ATTRACT_SELECTION_PROMPT,
            reply_markup=get_attractions_keyboard({name: "Нет" for name in ATTRACTION_NAMES})
        )
        logger.info(f"Пользователь {user_id} переходит к выбору аттракционов")

# Переключение аттракциона
@router.callback_query(lambda c: c.data.startswith("toggle_attraction:"))
async def toggle_attraction(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    attraction = callback.data.split(":", 1)[1]
    data = await state.get_data()
    attractions = data.get("attractions", {name: "Нет" for name in ATTRACTION_NAMES})
    attractions[attraction] = "Да" if attractions[attraction] == "Нет" else "Нет"

    await state.update_data(attractions=attractions)
    await _update_user({'telegram_id': user_id, 'attractions': attractions})

    new_kb = get_attractions_keyboard(attractions)
    await callback.message.edit_reply_markup(reply_markup=new_kb)
    await callback.answer()
    logger.info(f"Пользователь {user_id} изменил выбор аттракциона {attraction} на {attractions[attraction]}")

# Завершение выбора аттракционов
@router.callback_query(lambda c: c.data == "finish_selection")
async def finish_selection(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    attractions = data.get("attractions", {})

    # Нормализуем
    if all(v == "Нет" for v in attractions.values()):
        attractions = {name: "Нет" for name in ATTRACTION_NAMES}

    await _update_user({'telegram_id': user_id, 'attractions': attractions})

    # Инициализируем курс
    full_plan = initialize_course_plan({**data, 'user_id': user_id})
    await _update_user({'telegram_id': user_id, **full_plan})

    await state.clear()
    chat_id = callback.message.chat.id
    await callback.message.delete()
    await callback.bot.send_video(
        chat_id=chat_id,
        video=FSInputFile("video/complete_start.MP4"),
        caption=REGISTRATION_SUCCESS_MESSAGE,
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"Регистрация окончательно завершена для пользователя {user_id}")