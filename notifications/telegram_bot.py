import logging
from telegram import Bot
from telegram.error import TelegramError
from config import settings

logger = logging.getLogger(__name__)

# Initialize Telegram Bot
try:
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    logger.info("Telegram bot initialized successfully.")
except TelegramError as e:
    logger.error(f"Failed to initialize Telegram bot: {e}")
    bot = None  # Ensure bot is None if initialization fails

async def send_telegram_message(message):
    """
    Sends a message via Telegram.

    Parameters:
        message (str): The message text to send.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    if not bot:
        logger.error("Telegram bot is not initialized. Message not sent.")
        return False

    try:
        await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)
        logger.info("Telegram message sent successfully.")
        return True
    except TelegramError as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False
