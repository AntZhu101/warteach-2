import os
import json
import logging

# Настройка логирования (если ещё не настроено в основном модуле, то здесь будет использоваться базовая конфигурация)
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

DATA_FILE = "data/locations.json"

def load_locations():
    """Загружает локации из JSON-файла."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            locations = json.load(file)
            logger.info("Локации успешно загружены из %s", DATA_FILE)
            return locations
    except Exception as e:
        logger.error("Ошибка загрузки базы локаций: %s", e)
        return []

def save_to_json(user_id, data):
    filename = f"data/users/user_{user_id}.json"
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.info("Данные пользователя %s сохранены в %s", user_id, filename)
    except Exception as e:
        logger.error("Ошибка сохранения данных пользователя %s: %s", user_id, e)

def load_from_json(user_id):
    """Загружает данные пользователя из JSON-файла."""
    filename = f"data/users/user_{user_id}.json"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            logger.info("Данные пользователя %s успешно загружены из %s", user_id, filename)
            return data
        except Exception as e:
            logger.error("Ошибка загрузки данных пользователя %s: %s", user_id, e)
            return None
    logger.info("Файл пользователя %s не найден", user_id)
    return None

def load_training_data():
    filename = "data/training_data.json"
    if not os.path.exists(filename):
        logger.warning("Файл обучающих материалов %s не найден", filename)
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
        logger.info("Обучающие данные успешно загружены из %s", filename)
        return data
    except Exception as e:
        logger.error("Ошибка загрузки обучающих данных из %s: %s", filename, e)
        return {}

def load_user_data(user_id):
    filename = f"data/users/user_{user_id}.json"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            logger.info("Данные пользователя %s успешно загружены из %s", user_id, filename)
            return data
        except Exception as e:
            logger.error("Ошибка загрузки данных пользователя %s: %s", user_id, e)
            return None
    logger.info("Файл данных пользователя %s не найден", user_id)
    return None

def save_user_data(user_id, data):
    filename = f"data/users/user_{user_id}.json"
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.info("Данные пользователя %s успешно сохранены в %s", user_id, filename)
    except Exception as e:
        logger.error("Ошибка сохранения данных пользователя %s: %s", user_id, e)

def load_feedback():
    filename = "data/feedback/feedback.json"
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        logger.info("Файл отзывов %s не найден или пустой", filename)
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as file:
            feedback = json.load(file)
        logger.info("Отзывы успешно загружены из %s", filename)
        return feedback
    except json.JSONDecodeError as e:
        logger.error("Ошибка декодирования JSON в файле отзывов %s: %s", filename, e)
        return {}

def save_feedback(user_id, feedback_text, first_name="Неизвестно", last_name="Неизвестно"):
    filename = "data/feedback/feedback.json"
    feedback_data = load_feedback()
    
    if str(user_id) in feedback_data:
        user_feedback = feedback_data[str(user_id)]
        if "feedbacks" not in user_feedback:
            user_feedback["feedbacks"] = []
        user_feedback["feedbacks"].append(feedback_text)
    else:
        feedback_data[str(user_id)] = {
            "first_name": first_name,
            "last_name": last_name,
            "feedbacks": [feedback_text]
        }
    
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(feedback_data, file, ensure_ascii=False, indent=4)
        logger.info("Отзыв пользователя %s успешно сохранён в %s", user_id, filename)
    except Exception as e:
        logger.error("Ошибка сохранения отзывов пользователя %s: %s", user_id, e)
