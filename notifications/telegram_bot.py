import logging
from telegram import Bot
from telegram.error import TelegramError
from config import settings  # Import the initialized `settings` object

logger = logging.getLogger(__name__)

# Initialize the bot with the token from settings
bot = Bot(token=settings.TELEGRAM_TOKEN)

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
