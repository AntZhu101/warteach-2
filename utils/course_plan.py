import os
import json
import logging

# Настройка логирования: вывод в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_course_plan(data):
    """
    Формирует план курса обучения на основе ответов пользователя.
    Определение курса:
      - Если пользователь выбрал хотя бы один аттракцион (есть "Да") и vr_room == "да" → course = 1.
      - Если аттракционы выбраны, но vr_room != "да" → course = 2.
      - Если аттракционов нет, но vr_room == "да" → course = 3.
      - Иначе → course = 4.
    Затем формируется план курса (course_plan) как словарь секций.
    """
    attractions = data.get("attractions", {})
    has_attractions = any(val == "Да" for val in attractions.values())
    vr_room = data.get("vr_room", "").strip().lower() == "да"
    
    logger.info("Определение курса: has_attractions=%s, vr_room=%s", has_attractions, vr_room)
    
    if has_attractions and vr_room:
        data["course"] = 1
    elif has_attractions and not vr_room:
        data["course"] = 2
    elif not has_attractions and vr_room:
        data["course"] = 3
    else:
        data["course"] = 4

    logger.info("Определён курс: %s", data["course"])

    # Формирование плана курса в зависимости от курса.
    if data["course"] == 1:
        logger.info("Формирование плана курса для курса 1")
        chosen_attractions = [attr for attr, status in attractions.items() if status == "Да"]
        att_blocks = [
            {"title": "Инфо", "status": "not completed"},
            {"title": "Материал", "status": "not completed"}
        ]
        # Добавляем только выбранные аттракционы
        for attr in chosen_attractions:
            att_blocks.append({"title": attr, "status": "not completed"})
            att_blocks.append({"title": f"Тест {attr}", "status": "not completed"})
            logger.info("Добавлен аттракцион '%s' и тест для него", attr)
        att_blocks.append({"title": "Итог", "status": "not completed"})
        att_blocks.append({"title": "Тест итог", "status": "not completed"})

        course_plan = {
            "Attractions": att_blocks,
            "Arena": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал 1", "status": "not completed"},
                {"title": "Материал 2", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
            "VR-Room": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал 1", "status": "not completed"},
                {"title": "Материал 2", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
            "Excursion": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
            "Events": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ]
        }
    elif data["course"] == 2:
        logger.info("Формирование плана курса для курса 2")
        chosen_attractions = [attr for attr, status in attractions.items() if status == "Да"]
        att_blocks = [
            {"title": "Инфо", "status": "not completed"},
            {"title": "Материал", "status": "not completed"}
        ]
        for attr in chosen_attractions:
            att_blocks.append({"title": attr, "status": "not completed"})
            att_blocks.append({"title": f"Тест {attr}", "status": "not completed"})
            logger.info("Добавлен аттракцион '%s' и тест для него", attr)
        att_blocks.append({"title": "Итог", "status": "not completed"})
        att_blocks.append({"title": "Тест итог", "status": "not completed"})
        course_plan = {
            "Attractions": att_blocks,
            "Arena": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал 1", "status": "not completed"},
                {"title": "Материал 2", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
            "Excursion": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
            "Events": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
        }
    elif data["course"] == 3:
        logger.info("Формирование плана курса для курса 3")
        course_plan = {
            "VR-Room": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал 1", "status": "not completed"},
                {"title": "Материал 2", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
            "Arena": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал 1", "status": "not completed"},
                {"title": "Материал 2", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
            "Excursion": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
            "Events": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
        }
    else:
        logger.info("Формирование плана курса для курса 4")
        course_plan = {
            "Excursion": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
            "Events": [
                {"title": "Инфо", "status": "not completed"},
                {"title": "Материал", "status": "not completed"},
                {"title": "Тест", "status": "not completed"},
                {"title": "Итог", "status": "not completed"},
                {"title": "Тест итог", "status": "not completed"}
            ],
        }

    data["course_plan"] = course_plan
    logger.info("План курса сформирован")
    return data