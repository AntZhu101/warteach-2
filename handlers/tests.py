import os
import json
import logging
from datetime import datetime
from aiogram import Dispatcher, types, Router, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from main import bot
from utils.json_utils import load_training_data, load_user_data, save_user_data
from utils.bot_utils import send_message_or_photo
from handlers.states import TestStates
from text import (
    TEST_ALREADY_COMPLETED, PROFILE_NOT_FOUND, TEST_ERROR_DATA_NOT_FOUND, TEST_COMPLETED,
    TEST_ERRORS_MESSAGE, TEST_ERROR_ITEM, SECTION_COMPLETED_MESSAGE
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = Router()

# Отправка вопросов теста
async def send_test_question(user_id, chat_id, section, test_name, question_number, state: FSMContext):
    training_data = load_training_data()
    test_data = training_data.get(section, {}).get(test_name, {})

    if f"Вопрос {question_number}" not in test_data:
        logger.info(f"Нет вопроса 'Вопрос {question_number}' в тесте {test_name} для пользователя {user_id}. Завершаем тест.")
        return await finish_test(user_id, chat_id, section, test_name, state)

    question_data = test_data[f"Вопрос {question_number}"]
    text = question_data["text"]
    image = question_data.get("image", None)
    correct_answer = question_data["correct_answer"]

    # Сохраняем текущий вопрос в state
    await state.update_data(
        section=section, 
        test_name=test_name, 
        question_number=question_number,
        correct_answer=correct_answer
    )
    logger.info(f"Отправка вопроса {question_number} теста '{test_name}' пользователю {user_id}")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1️⃣", callback_data="answer_1")],
            [InlineKeyboardButton(text="2️⃣", callback_data="answer_2")],
            [InlineKeyboardButton(text="3️⃣", callback_data="answer_3")],
            [InlineKeyboardButton(text="4️⃣", callback_data="answer_4")]
        ]
    )

    await send_message_or_photo(chat_id, text, image, keyboard)

# Обработчик ответа пользователя на вопрос теста
@router.callback_query(lambda call: call.data.startswith("answer_"))
async def check_answer(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"Получен ответ {call.data} от пользователя {call.from_user.id}")

    data = await state.get_data()
    if not data:
        logger.warning("Нет данных в состоянии, невозможно проверить ответ")
        return await call.answer("Произошла ошибка, попробуйте еще раз.", show_alert=True)

    user_id = call.from_user.id
    chat_id = call.message.chat.id
    section = data["section"]
    test_name = data["test_name"]
    question_number = int(data["question_number"])  # Текущий вопрос
    correct_answer = int(data["correct_answer"])
    user_answer = int(call.data.split("_")[1])

    user_data = load_user_data(user_id)
    if not user_data:
        logger.warning(f"Профиль пользователя {user_id} не найден")
        return await bot.send_message(chat_id, "Профиль не найден.")

    training_data = load_training_data()
    test_data = training_data.get(section, {}).get(test_name, {})
    correct_answers = data.get("correct_answers", 0)
    incorrect_answers = data.get("incorrect_answers", [])

    if user_answer == correct_answer:
        correct_answers += 1
        logger.info(f"Пользователь {user_id} дал правильный ответ на вопрос {question_number}")
    else:
        question_data = test_data.get(f"Вопрос {question_number}", {})
        mistake_entry = {
            "section": section,
            "test_name": test_name,
            "question_text": question_data.get("text", "Нет текста вопроса"),
            "correct_answer": question_data.get("correct_answer", "Неизвестно"),
            "quest": question_data.get("quest", "Нет дополнительного задания"),
            "quest_status": "not completed"  # Добавляем статус задания
        }
        incorrect_answers.append(mistake_entry)

        # Сохраняем неверный ответ в профиль пользователя
        if "mistakes" not in user_data:
            user_data["mistakes"] = []
        user_data["mistakes"].append(mistake_entry)
        save_user_data(user_id, user_data)

        logger.info(f"Пользователь {user_id} дал неверный ответ на вопрос {question_number}. Добавлено в mistakes.")

    await state.update_data(correct_answers=correct_answers, incorrect_answers=incorrect_answers)

    try:
        await bot.delete_message(chat_id, call.message.message_id)
        logger.info(f"Старое сообщение с вопросом удалено для пользователя {user_id}")
    except Exception as e:
        logger.warning(f"Ошибка удаления сообщения: {e}")

    next_question_number = question_number + 1
    next_question_key = f"Вопрос {next_question_number}"

    if next_question_key in test_data:
        await send_test_question(user_id, chat_id, section, test_name, next_question_number, state)
    else:
        await finish_test(user_id, chat_id, section, test_name, state)

# Завершение теста
async def finish_test(user_id, chat_id, section, test_name, state: FSMContext):
    logger.info(f"Завершение теста '{test_name}' для пользователя {user_id}")

    user_data = load_user_data(user_id)
    if not user_data:
        logger.warning(f"Профиль пользователя {user_id} не найден при завершении теста")
        return await bot.send_message(chat_id, "Профиль не найден.")

    # Проверка, завершен ли уже тест
    for lesson in user_data["course_plan"].get(section, []):
        if lesson["title"] == test_name and lesson["status"] == "completed":
            logger.info(f"Тест '{test_name}' уже завершён.")
            return

    training_data = load_training_data()
    test_data = training_data.get(section, {}).get(test_name, {})
    total_questions = len(test_data)

    data = await state.get_data()
    correct_answers = data.get("correct_answers", 0)
    incorrect_answers = data.get("incorrect_answers", [])

    # Обновляем статус теста и сохраняем результаты
    for lesson in user_data["course_plan"].get(section, []):
        if lesson["title"] == test_name:
            lesson["status"] = "completed"
            lesson["total_questions"] = total_questions
            lesson["correct_answers"] = correct_answers
            break  

    user_data["warcoin"] = user_data.get("warcoin", 0) + correct_answers
    save_user_data(user_id, user_data)

    # Сообщение с результатами теста
    completion_message = (
        f"✅ Тест \"{test_name}\" завершён!\n"
        f"📊 Ваши результаты:\n"
        f"✔️ Правильных ответов: {correct_answers} из {total_questions}\n"
        f"💰 Начислено Warcoin: {correct_answers}\n"
        f"🏆 Ваш баланс: {user_data['warcoin']} Warcoin\n"
    )
    await bot.send_message(chat_id, completion_message)

    # Сообщение с заданиями
    result_message = (
        f"Тестирование завершено. Вы совершили {len(incorrect_answers)} ошибок.\n\n"
        "Позже вам потребуется пройти вопросы, где были допущены ошибки, еще раз.\n"
        "Ниже приведены задания, которые помогут вам подготовиться к следующему прохождению теста:\n"
    )

    if incorrect_answers:
        incorrect_tasks = "\n".join(
            f"- {item['quest']} (Статус: {item['quest_status']})" for item in incorrect_answers
        )
        result_message += incorrect_tasks
    else:
        result_message += "Нет дополнительных заданий для выполнения."

    await bot.send_message(chat_id, result_message)

    # Проверка, завершен ли весь раздел
    if is_section_completed(user_data, section):
        section_complete_message = SECTION_COMPLETED_MESSAGE.format(
            first_name=user_data.get("first_name", "Пользователь"),
            section=section
        )
        await bot.send_message(chat_id, section_complete_message)

    await state.clear()

def is_section_completed(user_data, section):
    course_plan = user_data.get("course_plan", {})
    section_lessons = course_plan.get(section, [])
    return all(lesson["status"] == "completed" for lesson in section_lessons)