import logging
from datetime import datetime, timedelta
from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.json_utils import load_from_json, save_user_data
from bot_instance import bot  

router = Router()
logger = logging.getLogger(__name__)

TASKS_PER_PAGE = 5  # Количество заданий на одной странице

# Отображение списка стажеров
@router.message(lambda message: message.text == "/trainee")
async def show_trainees(message: Message):
    """
    Команда /trainee для отображения списка стажеров наставника.
    """
    user_id = message.from_user.id

    # Загружаем данные наставника
    mentor_data = load_from_json(user_id)
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


# Отображение профиля стажера
@router.callback_query(lambda c: c.data.startswith("trainee_details:"))
async def show_trainee_details(callback: CallbackQuery):
    """
    Обработчик для кнопок стажеров. Показывает профиль стажера.
    """
    user_id = callback.from_user.id
    trainee_id = callback.data.split(":")[1]

    # Удаляем старое сообщение
    await callback.message.delete()

    # Загружаем данные наставника
    mentor_data = load_from_json(user_id)
    if not mentor_data or mentor_data.get("role") != "mentor":
        await callback.answer("Ошибка: у вас нет доступа к этой информации.", show_alert=True)
        logger.warning(f"Пользователь {user_id} пытался получить данные стажера, не являясь наставником.")
        return

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    # Формируем информацию о стажере
    trainee_name = f"{trainee_data.get('first_name', 'Неизвестно')} {trainee_data.get('last_name', 'Неизвестно')}"
    trainee_phone = trainee_data.get("phone_number", "Не указан")
    registration_date = trainee_data.get("registration_date", "Дата регистрации отсутствует")

    # Вычисляем количество заданий
    mistakes = trainee_data.get("mistakes", [])
    num_tasks = len(mistakes) if isinstance(mistakes, list) else 0

    # Формируем сообщение для наставника
    trainee_details = (
        f"Профиль стажера:\n\n"
        f"Имя: {trainee_name}\n"
        f"Номер телефона: {trainee_phone}\n"
        f"Дата регистрации: {registration_date}\n"
        f"Количество заданий: {num_tasks}\n"
    )

    # Формируем кнопки
    keyboard_buttons = [
        [InlineKeyboardButton(
            text="Связаться со стажером",
            url=f"tg://user?id={trainee_id}"
        )],
        [InlineKeyboardButton(
            text="Задания",
            callback_data=f"trainee_tasks:0:{trainee_id}"  # Добавляем номер страницы
        )],
        [InlineKeyboardButton(
            text="Прогресс",
            callback_data=f"trainee_progress:{trainee_id}"
        )],
        [InlineKeyboardButton(
            text="Итоговый тест аттестация",
            callback_data=f"final_test:{trainee_id}"
        )],
        [InlineKeyboardButton(
            text="Повысить до оператора",
            callback_data=f"promote_to_operator:{trainee_id}"
        )],
    ]

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.answer(trainee_details, reply_markup=keyboard)

# Кнопка "Открыть тестирование"
@router.callback_query(lambda c: c.data.startswith("start_final_test:"))
async def start_final_test(callback: CallbackQuery):
    """
    Обработчик для кнопки "Открыть тестирование".
    """
    _, trainee_id = callback.data.split(":")

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    # Проверяем условия
    conditions = []

    # Условие 1: Пройти основной курс обучения
    course_plan = trainee_data.get("course_plan", {})
    all_courses_completed = all(
        lesson.get("status") == "completed" 
        for lessons in course_plan.values() 
        for lesson in lessons
    )
    conditions.append(("Пройти основной курс обучения", all_courses_completed))

    # Условие 2: Выполнить все задания
    mistakes = trainee_data.get("mistakes", [])
    all_tasks_completed = all(task.get("quest_status") == "completed" for task in mistakes)
    conditions.append(("Выполнить все задания", all_tasks_completed))

    # Условие 3: Отработать 1 месяц
    registration_date = trainee_data.get("registration_date")
    if registration_date:
        registration_date = datetime.strptime(registration_date, "%Y-%m-%d")
        one_month_passed = (datetime.now() - registration_date) >= timedelta(days=30)
    else:
        one_month_passed = False
    conditions.append(("Отработать 1 месяц", one_month_passed))

    # Проверяем, выполнены ли все условия
    unmet_conditions = [condition for condition, status in conditions if not status]
    if unmet_conditions:
        unmet_conditions_text = "\n".join(f"❌ {condition}" for condition in unmet_conditions)
        await callback.message.edit_text(
            f"Тест не может быть открыт по следующим причинам:\n{unmet_conditions_text}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Назад в меню стажера", callback_data=f"trainee_details:{trainee_id}")]
                ]
            )
        )
        return

    # Все условия выполнены — обновляем данные стажера
    trainee_data["final_test_ready"] = True
    save_user_data(trainee_id, trainee_data)

    # Уведомление наставнику
    await callback.message.edit_text(
        "✅ Итоговое тестирование открыто для стажера.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Назад в меню стажера", callback_data=f"trainee_details:{trainee_id}")]
            ]
        )
    )

    # Уведомление стажеру
    trainee_chat_id = trainee_data.get("user_id")  
    if trainee_chat_id:
        try:
            await bot.send_message(
                trainee_chat_id,
                "✅ Для вас открыто итоговое тестирование!\n"
                "Чтобы пройти тестирование, введите команду: /attestatsiya"
            )
            logger.info(f"Стажеру с ID {trainee_chat_id} отправлено уведомление об открытии теста.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение стажеру с ID {trainee_chat_id}: {e}")
    else:
        logger.warning(f"Не удалось отправить сообщение: у стажера отсутствует user_id.")
# Кнопка "Итоговое тестирование"
@router.callback_query(lambda c: c.data.startswith("final_test:"))
async def show_final_test(callback: CallbackQuery):
    """
    Обработчик для кнопки "Итоговое тестирование".
    """
    _, trainee_id = callback.data.split(":")

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    # Проверяем условия
    conditions = []

    # Условие 1: Пройти основной курс обучения
    course_plan = trainee_data.get("course_plan", {})
    all_courses_completed = all(
        lesson.get("status") == "completed" 
        for lessons in course_plan.values() 
        for lesson in lessons
    )
    conditions.append(("Пройти основной курс обучения", all_courses_completed))

    # Условие 2: Выполнить все задания
    mistakes = trainee_data.get("mistakes", [])
    all_tasks_completed = all(task.get("quest_status") == "completed" for task in mistakes)
    conditions.append(("Выполнить все задания", all_tasks_completed))

    # Условие 3: Отработать 1 месяц
    registration_date = trainee_data.get("registration_date")
    if registration_date:
        registration_date = datetime.strptime(registration_date, "%Y-%m-%d")
        one_month_passed = (datetime.now() - registration_date) >= timedelta(days=30)
    else:
        one_month_passed = False
    conditions.append(("Отработать 1 месяц", one_month_passed))

    # Формируем сообщение
    message_text = (
        f"Итоговый тест содержит {len(mistakes)} вопросов.\n\n"
        "Итоговое тестирование проходит перед аттестацией, и стажер должен выполнить следующие условия:\n"
    )
    for idx, (condition, status) in enumerate(conditions, start=1):
        status_icon = "✅" if status else "❌"
        message_text += f"{idx}. {condition} {status_icon}\n"

    # Кнопки
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Открыть тестирование", callback_data=f"start_final_test:{trainee_id}")
            ],
            [
                InlineKeyboardButton(text="Назад в меню стажера", callback_data=f"trainee_details:{trainee_id}")
            ]
        ]
    )

    await callback.message.edit_text(message_text, reply_markup=keyboard)

# Отображение профиля стажера
@router.callback_query(lambda c: c.data.startswith("trainee_details:"))
async def show_trainee_details(callback: CallbackQuery):
    """
    Обработчик для кнопок стажеров. Показывает профиль стажера.
    """
    user_id = callback.from_user.id
    trainee_id = callback.data.split(":")[1]

    # Удаляем старое сообщение
    await callback.message.delete()

    # Загружаем данные наставника
    mentor_data = load_from_json(user_id)
    if not mentor_data or mentor_data.get("role") != "mentor":
        await callback.answer("Ошибка: у вас нет доступа к этой информации.", show_alert=True)
        logger.warning(f"Пользователь {user_id} пытался получить данные стажера, не являясь наставником.")
        return

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    # Формируем информацию о стажере
    trainee_name = f"{trainee_data.get('first_name', 'Неизвестно')} {trainee_data.get('last_name', 'Неизвестно')}"
    trainee_phone = trainee_data.get("phone_number", "Не указан")
    registration_date = trainee_data.get("registration_date", "Дата регистрации отсутствует")

    # Вычисляем количество заданий
    mistakes = trainee_data.get("mistakes", [])
    num_tasks = len(mistakes) if isinstance(mistakes, list) else 0

    # Формируем сообщение для наставника
    trainee_details = (
        f"Профиль стажера:\n\n"
        f"Имя: {trainee_name}\n"
        f"Номер телефона: {trainee_phone}\n"
        f"Дата регистрации: {registration_date}\n"
        f"Количество заданий: {num_tasks}\n"
    )

    # Формируем кнопки
    keyboard_buttons = [
        [InlineKeyboardButton(
            text="Связаться со стажером",
            url=f"tg://user?id={trainee_id}"
        )],
        [InlineKeyboardButton(
            text="Задания",
            callback_data=f"trainee_tasks:0:{trainee_id}"  # Добавляем номер страницы
        )],
        [InlineKeyboardButton(
            text="Прогресс",
            callback_data=f"trainee_progress:{trainee_id}"
        )]
    ]

    # Проверяем наличие "final_test_ready" у стажера
    if not trainee_data.get("final_test_ready", False):
        # Если аттестация не открыта, добавляем кнопку
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="Итоговый тест аттестация",
                callback_data=f"final_test:{trainee_id}"
            )
        ])

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.answer(trainee_details, reply_markup=keyboard)


# Кнопка "Открыть тестирование"
@router.callback_query(lambda c: c.data.startswith("start_final_test:"))
async def start_final_test(callback: CallbackQuery):
    """
    Обработчик для кнопки "Открыть тестирование".
    """
    _, trainee_id = callback.data.split(":")

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    # Проверяем условия для открытия теста
    conditions = []

    # Условие 1: Пройти основной курс обучения
    course_plan = trainee_data.get("course_plan", {})
    all_courses_completed = all(
        lesson.get("status") == "completed" 
        for lessons in course_plan.values() 
        for lesson in lessons
    )
    conditions.append(("Пройти основной курс обучения", all_courses_completed))

    # Условие 2: Выполнить все задания
    mistakes = trainee_data.get("mistakes", [])
    all_tasks_completed = all(task.get("quest_status") == "completed" for task in mistakes)
    conditions.append(("Выполнить все задания", all_tasks_completed))

    # Условие 3: Отработать 1 месяц
    registration_date = trainee_data.get("registration_date")
    if registration_date:
        registration_date = datetime.strptime(registration_date, "%Y-%m-%d")
        one_month_passed = (datetime.now() - registration_date) >= timedelta(days=30)
    else:
        one_month_passed = False
    conditions.append(("Отработать 1 месяц", one_month_passed))

    # Проверяем, выполнены ли все условия
    unmet_conditions = [condition for condition, status in conditions if not status]
    if unmet_conditions:
        unmet_conditions_text = "\n".join(f"❌ {condition}" for condition in unmet_conditions)
        await callback.message.edit_text(
            f"Тест не может быть открыт по следующим причинам:\n{unmet_conditions_text}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Назад в меню стажера", callback_data=f"trainee_details:{trainee_id}")]
                ]
            )
        )
        return

    # Все условия выполнены — обновляем данные стажера
    trainee_data["final_test_ready"] = True
    save_user_data(trainee_id, trainee_data)

    # Уведомление наставнику
    await callback.message.edit_text(
        "✅ Итоговое тестирование открыто для стажера.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Назад в меню стажера", callback_data=f"trainee_details:{trainee_id}")]
            ]
        )
    )

    # Уведомление стажеру
    trainee_chat_id = trainee_data.get("user_id")  
    if trainee_chat_id:
        try:
            await bot.send_message(
                trainee_chat_id,
                "✅ Для вас открыто итоговое тестирование!\n"
                "Чтобы пройти тестирование, введите команду: /attestatsiya"
            )
            logger.info(f"Стажеру с ID {trainee_chat_id} отправлено уведомление об открытии теста.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение стажеру с ID {trainee_chat_id}: {e}")
    else:
        logger.warning(f"Не удалось отправить сообщение: у стажера отсутствует user_id.")

# Отображение заданий стажера
@router.callback_query(lambda c: c.data.startswith("trainee_tasks:"))
async def show_trainee_tasks(callback: CallbackQuery):
    """
    Обработчик для кнопки "Задания". Показывает задания стажера.
    """
    _, page_number, trainee_id = callback.data.split(":")
    page_number = int(page_number)

    # Удаляем старое сообщение
    await callback.message.delete()

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    tasks = trainee_data.get("mistakes", [])
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.get("quest_status") == "completed")

    # Формируем сообщение
    message_text = (
        f"У данного стажера {total_tasks} заданий.\n"
        f"Из них выполнено: {completed_tasks}.\n\n"
        "Вы как наставник обязаны пройти с стажером все задания, проверить его знания материала и отметить выполненные задания.\n\n"
        "Список заданий:\n"
    )

    # Формируем список заданий для текущей страницы
    start_index = page_number * TASKS_PER_PAGE
    end_index = start_index + TASKS_PER_PAGE
    tasks_for_page = tasks[start_index:end_index]

    for idx, task in enumerate(tasks_for_page, start=start_index + 1):
        message_text += f"{idx}. {task['quest']}\n"

    # Формируем кнопки для заданий
    keyboard_buttons = [
        [InlineKeyboardButton(
            text=f"{idx + 1} {task['quest'].split()[0]} {'✅' if task.get('quest_status') == 'completed' else '❌'}",
            callback_data=f"task_details:{idx}:{trainee_id}"
        )]
        for idx, task in enumerate(tasks_for_page, start=start_index)
    ]

    # Добавляем кнопки навигации
    navigation_buttons = []
    if start_index > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data=f"trainee_tasks:{page_number - 1}:{trainee_id}"
        ))
    if end_index < total_tasks:
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️", 
            callback_data=f"trainee_tasks:{page_number + 1}:{trainee_id}"
        ))

    if navigation_buttons:
        keyboard_buttons.append(navigation_buttons)

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.answer(message_text, reply_markup=keyboard)

# Обработчик для изменения статуса задания
@router.callback_query(lambda c: c.data.startswith("task_details:"))
async def update_task_status(callback: CallbackQuery):
    """
    Обработчик для изменения статуса задания на "выполнено".
    """
    _, task_index, trainee_id = callback.data.split(":")
    task_index = int(task_index)

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    tasks = trainee_data.get("mistakes", [])
    if task_index >= len(tasks):
        await callback.answer("Ошибка: задание не найдено.", show_alert=True)
        logger.error(f"Задание с индексом {task_index} не найдено для стажера {trainee_id}.")
        return

    # Обновляем статус задания
    tasks[task_index]["quest_status"] = "completed"
    save_user_data(trainee_id, trainee_data)

    # Формируем обновленный список кнопок
    page_number = task_index // TASKS_PER_PAGE  # Рассчитываем текущую страницу
    start_index = page_number * TASKS_PER_PAGE
    end_index = start_index + TASKS_PER_PAGE
    tasks_for_page = tasks[start_index:end_index]

    keyboard_buttons = [
        [InlineKeyboardButton(
            text=f"{idx + 1} {task['quest'].split()[0]} {'✅' if task.get('quest_status') == 'completed' else '❌'}",
            callback_data=f"task_details:{idx}:{trainee_id}"
        )]
        for idx, task in enumerate(tasks_for_page, start=start_index)
    ]

    # Добавляем кнопки навигации
    navigation_buttons = []
    if start_index > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"trainee_tasks:{page_number - 1}:{trainee_id}"
        ))
    if end_index < len(tasks):
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=f"trainee_tasks:{page_number + 1}:{trainee_id}"
        ))

    if navigation_buttons:
        keyboard_buttons.append(navigation_buttons)

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    # Обновляем сообщение
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("Задание отмечено как выполненное!")

# Отображение прогресса стажера
@router.callback_query(lambda c: c.data.startswith("trainee_progress:"))
async def show_trainee_progress(callback: CallbackQuery):
    """
    Обработчик для кнопки "Прогресс". Показывает прогресс обучения стажера.
    """
    user_id = callback.from_user.id
    trainee_id = callback.data.split(":")[1]

    # Удаляем старое сообщение
    await callback.message.delete()

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    course_plan = trainee_data.get("course_plan", {})
    if not course_plan:
        await callback.answer("Прогресс обучения не найден.", show_alert=True)
        logger.warning(f"Прогресс обучения для стажера {trainee_id} не найден.")
        return

    # Формируем сообщение с прогрессом
    progress_message = "📊 Прогресс обучения стажера:\n\n"
    for section, lessons in course_plan.items():
        progress_message += f"Раздел: {section}\n"
        for lesson in lessons:
            title = lesson.get("title", "Без названия")
            status = lesson.get("status", "not completed")
            status_icon = "✅" if status == "completed" else "❌"
            progress_message += f"{status_icon} {title}"

            # Добавляем информацию о тестах, если она есть
            if status == "completed" and "total_questions" in lesson and "correct_answers" in lesson:
                total_questions = lesson["total_questions"]
                correct_answers = lesson["correct_answers"]
                progress_message += f" ({correct_answers}/{total_questions})"
            progress_message += "\n"
        progress_message += "\n"

    # Кнопка "Назад"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data=f"trainee_details:{trainee_id}")]
        ]
    )

    await callback.message.answer(progress_message, reply_markup=keyboard)
# Отображение профиля стажера
@router.callback_query(lambda c: c.data.startswith("trainee_details:"))
async def show_trainee_details(callback: CallbackQuery):
    """
    Обработчик для кнопок стажеров. Показывает профиль стажера.
    """
    user_id = callback.from_user.id
    trainee_id = callback.data.split(":")[1]

    # Удаляем старое сообщение
    await callback.message.delete()

    # Загружаем данные наставника
    mentor_data = load_from_json(user_id)
    if not mentor_data or mentor_data.get("role") != "mentor":
        await callback.answer("Ошибка: у вас нет доступа к этой информации.", show_alert=True)
        logger.warning(f"Пользователь {user_id} пытался получить данные стажера, не являясь наставником.")
        return

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    # Формируем информацию о стажере
    trainee_name = f"{trainee_data.get('first_name', 'Неизвестно')} {trainee_data.get('last_name', 'Неизвестно')}"
    trainee_phone = trainee_data.get("phone_number", "Не указан")
    registration_date = trainee_data.get("registration_date", "Дата регистрации отсутствует")

    # Вычисляем количество заданий
    mistakes = trainee_data.get("mistakes", [])
    num_tasks = len(mistakes) if isinstance(mistakes, list) else 0

    # Формируем сообщение для наставника
    trainee_details = (
        f"Профиль стажера:\n\n"
        f"Имя: {trainee_name}\n"
        f"Номер телефона: {trainee_phone}\n"
        f"Дата регистрации: {registration_date}\n"
        f"Количество заданий: {num_tasks}\n"
    )

    # Формируем кнопки
    keyboard_buttons = [
        [InlineKeyboardButton(
            text="Связаться со стажером",
            url=f"tg://user?id={trainee_id}"
        )],
        [InlineKeyboardButton(
            text="Задания",
            callback_data=f"trainee_tasks:0:{trainee_id}"  # Добавляем номер страницы
        )],
        [InlineKeyboardButton(
            text="Прогресс",
            callback_data=f"trainee_progress:{trainee_id}"
        )],
        [InlineKeyboardButton(
            text="Повысить до оператора",
            callback_data=f"promote_to_operator:{trainee_id}"
        )]
    ]

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.answer(trainee_details, reply_markup=keyboard)


# Кнопка "Повысить до оператора"
@router.callback_query(lambda c: c.data.startswith("promote_to_operator:"))
async def promote_to_operator(callback: CallbackQuery):
    """
    Обработчик кнопки "Повысить до оператора".
    Показывает текст с требованиями для перевода и предоставляет кнопки для подтверждения или возврата.
    """
    trainee_id = callback.data.split(":")[1]

    # Удаляем старое сообщение
    await callback.message.delete()

    # Формируем сообщение с условиями перевода
    translation_message = (
        "Для перевода сотрудника из статуса стажера в статус оператора требуется, чтобы он:\n"
        "- Отработал не менее 1 месяца.\n"
        "- Полностью прошел курс обучения.\n"
        "- Выполнил все задания."
    )

    # Кнопки "Повысить" и "Назад"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Повысить",
                callback_data=f"confirm_promotion:{trainee_id}"
            )],
            [InlineKeyboardButton(
                text="Назад",
                callback_data=f"trainee_details:{trainee_id}"
            )]
        ]
    )

    await callback.message.answer(translation_message, reply_markup=keyboard)


# Кнопка "Повысить" (подтверждение перевода)
@router.callback_query(lambda c: c.data.startswith("confirm_promotion:"))
async def confirm_promotion(callback: CallbackQuery):
    """
    Обработчик для кнопки "Повысить".
    Проверяет выполнение условий и выполняет перевод стажера в операторы.
    """
    trainee_id = callback.data.split(":")[1]

    # Удаляем старое сообщение
    await callback.message.delete()

    # Загружаем данные стажера
    trainee_data = load_from_json(trainee_id)
    if not trainee_data:
        await callback.answer("Ошибка: данные стажера не найдены.", show_alert=True)
        logger.error(f"Данные стажера с ID {trainee_id} не найдены.")
        return

    # Проверяем условия
    conditions = []

    # Условие 1: Отработать 1 месяц
    registration_date = trainee_data.get("registration_date")
    if registration_date:
        registration_date = datetime.strptime(registration_date, "%Y-%m-%d")
        one_month_passed = (datetime.now() - registration_date) >= timedelta(days=30)
    else:
        one_month_passed = False
    conditions.append(("Отработать 1 месяц", one_month_passed))

    # Условие 2: Пройти курс обучения полностью
    course_plan = trainee_data.get("course_plan", {})
    all_courses_completed = all(
        lesson.get("status") == "completed" 
        for lessons in course_plan.values() 
        for lesson in lessons
    )
    conditions.append(("Пройти курс обучения полностью", all_courses_completed))

    # Условие 3: Выполнить все задания
    mistakes = trainee_data.get("mistakes", [])
    all_tasks_completed = all(task.get("quest_status") == "completed" for task in mistakes)
    conditions.append(("Выполнить все задания", all_tasks_completed))

    # Проверяем, выполнены ли все условия
    unmet_conditions = [condition for condition, status in conditions if not status]

    # Формируем текст для неудовлетворённых условий
    unmet_conditions_text = "\n".join(f"❌ {condition}" for condition in unmet_conditions)

    if unmet_conditions:
        await callback.message.answer(
            f"Сотрудник не может быть повышен до оператора по следующим причинам:\n{unmet_conditions_text}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Назад", callback_data=f"trainee_details:{trainee_id}")]
                ]
            )
        )
        return

    # Все условия выполнены — обновляем данные стажера
    trainee_data["role"] = "Employee"
    for key in ["course", "course_plan", "mistakes", "final_test_ready", "mentor"]:
        trainee_data.pop(key, None)
    save_user_data(trainee_id, trainee_data)

    # Удаляем информацию о стажере у наставника
    mentor_id = callback.from_user.id
    mentor_data = load_from_json(mentor_id)
    if mentor_data and "Trainee" in mentor_data:
        if trainee_id in mentor_data["Trainee"]:
            del mentor_data["Trainee"][trainee_id]
            save_user_data(mentor_id, mentor_data)
            logger.info(f"Стажер с ID {trainee_id} удалён из списка наставника {mentor_id}.")
        else:
            logger.warning(f"Стажер с ID {trainee_id} отсутствует в данных наставника {mentor_id}.")

    # Уведомление наставнику
    await callback.message.answer(
        "✅ Сотрудник успешно повышен до оператора.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data=f"trainee_details:{trainee_id}")]
            ]
        )
    )