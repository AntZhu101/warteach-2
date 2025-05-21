import logging
from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.json_utils import load_from_json, save_user_data
from bot_instance import bot

router = Router()
logger = logging.getLogger(__name__)

# Переменные для хранения временных данных
active_tests = {}  # Словарь для хранения данных о текущем тестировании (в памяти)

# Команда /attestatsiya
@router.message(lambda message: message.text == "/attestatsiya")
async def start_attestation(message: Message):
    """
    Команда /attestatsiya для начала итогового тестирования.
    Проверяем доступ к тестированию.
    """
    user_id = message.from_user.id

    # Загружаем профиль стажера
    trainee_data = load_from_json(user_id)
    if not trainee_data:
        logger.warning(f"Данные стажера с ID {user_id} не найдены.")
        return

    # Проверяем доступ к тестированию
    if trainee_data.get("final_test_ready") is not True:
        # Если доступ отсутствует, ничего не выводим
        logger.info(f"Стажер {user_id} пытался начать тестирование без доступа.")
        return

    # Доступ есть, выводим информацию о тесте
    mistakes = trainee_data.get("mistakes", [])
    num_questions = len(mistakes)

    await message.answer(
        f"✅ Это итоговый тест, который нельзя будет перепройти.\n"
        f"Он состоит из {num_questions} вопросов.\n"
        "Это все вопросы, на которые вы не смогли дать правильный ответ в прошлых тестах.\n\n"
        "Чтобы начать тестирование, нажмите кнопку «Начать» ниже.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Начать", callback_data="start_test")]
            ]
        )
    )

# Кнопка "Начать"
@router.callback_query(lambda c: c.data == "start_test")
async def handle_start_test(callback: CallbackQuery):
    """
    Обработчик кнопки "Начать". Начинаем тестирование.
    """
    user_id = callback.from_user.id

    # Загружаем профиль стажера
    trainee_data = load_from_json(user_id)
    if not trainee_data:
        await callback.message.delete()
        logger.warning(f"Данные стажера с ID {user_id} не найдены.")
        return

    # Проверяем доступ к тестированию
    if trainee_data.get("final_test_ready") is not True:
        # Если доступа нет, удаляем сообщение
        await callback.message.delete()
        logger.info(f"Стажер {user_id} пытался начать тестирование без доступа.")
        return

    # Доступ есть, начинаем тестирование
    mistakes = trainee_data.get("mistakes", [])

    # Проверяем, есть ли вопросы
    if not mistakes:
        await callback.message.edit_text("У вас нет вопросов для тестирования.")
        return

    # Сохраняем данные о текущем тесте в памяти
    active_tests[user_id] = {
        "questions": mistakes,
        "current_index": 0,
        "errors": []
    }

    # Отображаем первый вопрос
    await send_question(callback, user_id)

async def send_question(callback: CallbackQuery, user_id: int):
    """
    Отображает текущий вопрос тестирования.
    """
    test_data = active_tests.get(user_id)
    if not test_data:
        await callback.message.delete()
        logger.warning(f"Тестирование для стажера {user_id} неактивно.")
        return

    current_index = test_data["current_index"]
    questions = test_data["questions"]

    # Проверяем, есть ли еще вопросы
    if current_index >= len(questions):
        await show_test_results(callback, user_id)
        return

    # Получаем текущий вопрос
    question_data = questions[current_index]
    question_text = question_data.get("question_text", "Вопрос отсутствует.")
    correct_answer = question_data.get("correct_answer", 1)

    # Формируем кнопки для вариантов ответа
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(i), callback_data=f"answer:{i}:{correct_answer}")]
            for i in range(1, 5)
        ]
    )

    # Отправляем вопрос
    await callback.message.edit_text(
        f"Вопрос {current_index + 1}:\n{question_text}",
        reply_markup=keyboard
    )

# Обработчик ответа на вопрос
@router.callback_query(lambda c: c.data.startswith("answer:"))
async def handle_answer(callback: CallbackQuery):
    """
    Обрабатывает ответ на вопрос.
    """
    user_id = callback.from_user.id
    if user_id not in active_tests:
        await callback.message.delete()
        logger.warning(f"Тестирование для стажера {user_id} неактивно.")
        return

    _, selected_answer, correct_answer = callback.data.split(":")
    selected_answer = int(selected_answer)
    correct_answer = int(correct_answer)

    # Проверяем правильность ответа
    test_data = active_tests[user_id]
    current_index = test_data["current_index"]
    questions = test_data["questions"]

    if current_index < len(questions):
        question_data = questions[current_index]
        if selected_answer != correct_answer:
            # Если ответ неверный, добавляем задание в список ошибок
            test_data["errors"].append(question_data)

    # Переходим к следующему вопросу
    test_data["current_index"] += 1

    # Показ следующего вопроса
    await send_question(callback, user_id)

async def show_test_results(callback: CallbackQuery, user_id: int):
    """
    Отображает результаты тестирования и уведомляет наставника.
    """
    if user_id not in active_tests:
        await callback.message.delete()
        logger.warning(f"Тестирование для стажера {user_id} неактивно.")
        return

    test_data = active_tests.pop(user_id)  # Удаляем данные теста из памяти
    questions = test_data["questions"]
    errors = test_data["errors"]

    num_questions = len(questions)
    num_errors = len(errors)

    # Формируем итоговое сообщение для стажера
    result_message = (
        f"✅ Итоговое тестирование завершено.\n\n"
        f"Всего вопросов: {num_questions}\n"
        f"Ошибок: {num_errors}\n\n"
    )

    if errors:
        result_message += "❌ Задания с ошибками:\n"
        for task in errors:
            result_message += f"- {task.get('quest', 'Не указано')}\n"

    # Отображаем результаты стажеру
    await callback.message.edit_text(result_message)

    # Уведомляем наставника
    trainee_data = load_from_json(user_id)
    mentor_id = trainee_data.get("mentor", {}).get("id")
    if mentor_id:
        try:
            # Формируем сообщение для наставника
            mentor_message = (
                f"Стажер {trainee_data.get('first_name', 'Неизвестно')} "
                f"{trainee_data.get('last_name', 'Неизвестно')} "
                f"прошел итоговый тест с результатом {num_questions - num_errors}/{num_questions}.\n"
            )

            if errors:
                mentor_message += "Вот задания, которые стоит повторить:\n"
                for task in errors:
                    mentor_message += f"- {task.get('quest', 'Не указано')}\n"

            # Отправляем сообщение наставнику
            await bot.send_message(mentor_id, mentor_message)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение наставнику с ID {mentor_id}: {e}")

    # Удаляем строку "final_test_ready" из JSON
    if "final_test_ready" in trainee_data:
        del trainee_data["final_test_ready"]
        save_user_data(user_id, trainee_data)