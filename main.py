import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import json
import logging

from database import db

from handlers.start import router as start_router
from handlers.help import router as help_router
from handlers.add_book import router as add_book_router
from handlers.scan_isbn import router as scan_isbn_router
from handlers.my_library import router as my_library_router
from handlers.search import router as search_router
from handlers.search_my_library import router as search_my_library_router
from handlers.stats import router as stats_router
from handlers.quotes import router as quotes_router
from handlers.shelves import router as shelves_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    try:
        with open('conf.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        token = data.get('token')
        if not token:
            logger.error("Токен не найден в conf.json")
            return
        
        bot = Bot(token=token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        dp.include_router(start_router)
        dp.include_router(help_router)
        dp.include_router(add_book_router)
        dp.include_router(scan_isbn_router)
        dp.include_router(my_library_router)
        dp.include_router(search_router)
        dp.include_router(search_my_library_router)
        dp.include_router(stats_router)
        dp.include_router(quotes_router)
        dp.include_router(shelves_router)
        
        logger.info("✅ Все роутеры загружены")
        logger.info("📚 Библиотекарь запущен!")

        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        if 'bot' in locals():
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())