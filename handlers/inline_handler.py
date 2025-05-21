import json
import logging
from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from utils.json_utils import load_locations
from text import INLINE_QUERY_ERROR

# Настройка логирования: вывод логов только в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = Router()

@router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query = inline_query.query.strip().lower()
    logger.info(f"Inline query received from user {inline_query.from_user.id}: '{query}'")
    
    # Загружаем актуальные данные из JSON при каждом запросе
    locations = load_locations()
    logger.info(f"Loaded {len(locations)} locations from JSON")
    
    # Фильтрация по названию, городу или адресу
    filtered_locations = [
        loc for loc in locations if query in loc["title"].lower() or query in loc["city"].lower() or query in loc["address"].lower()
    ] if query else locations
    
    logger.info(f"Found {len(filtered_locations)} matching locations")
    
    if not filtered_locations:
        await inline_query.answer([], cache_time=1)
        logger.info("No matching locations found, returning empty result")
        return

    # Формируем текстовые результаты
    results = [
        InlineQueryResultArticle(
            id=f"loc_{i}",
            title=loc["title"],
            description=f"{loc['city']}, {loc['address']}",
            input_message_content=InputTextMessageContent(
                message_text=f"{loc['title']} {loc['city']} {loc['address']}"
            )
        )
        for i, loc in enumerate(filtered_locations)
    ]
    
    try:
        await inline_query.answer(results, cache_time=1)
        logger.info("Inline query results sent successfully")
    except Exception as e:
        logger.error(f"{INLINE_QUERY_ERROR} {e}")
