from aiogram import Bot,Dispatcher
import sys
from core.settings import BOT_TOKEN
from aiogram.client.bot import DefaultBotProperties
import asyncio
import logging

from .handler.private import user_private_router

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
ds = Dispatcher()

ds.include_router(user_private_router)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# file_handler = logging.FileHandler('bot/app.log')
# file_handler.setLevel(logging.INFO)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)

# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)
# stream_handler.setFormatter(formatter)

# logger.addHandler(file_handler)
logger.addHandler(stream_handler)

async def main():
    await ds.start_polling(bot)
