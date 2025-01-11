import logging
from telegram import Bot
from telegram.error import TelegramError
from config import settings  # Import the initialized `settings` object

logger = logging.getLogger(__name__)

# Initialize the bot with the token from settings
bot = Bot(token=settings.TELEGRAM_TOKEN)

async def send_telegram_message(message):
    try:
        await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)
    except TelegramError as e:
        logger.error(f"Failed to send Telegram message: {e}")
