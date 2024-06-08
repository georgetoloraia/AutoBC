import logging
from telegram import Bot
from telegram.error import TelegramError
from config import settings

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_TOKEN)

async def send_telegram_message(message):
    try:
        await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)
    except TelegramError as e:
        logger.error(f"Failed to send Telegram message: {e}")
