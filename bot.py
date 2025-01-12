import asyncio
import logging
import ccxt.async_support as ccxt
# from config import settings  # Ensure this is uncommented if settings are used
from trading.trader import advanced_trade, close_exchange

import os
import logging

# Ensure the logs directory exists
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure logging
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Logs to console
    ]
)
logger = logging.getLogger(__name__)


# Main function
async def main():
    """
    Entry point for the trading bot.
    This function initializes trading, handles exceptions, and ensures cleanup.
    """
    logger.info("Starting AutoBC Trading Bot...")
    try:
        await advanced_trade()
    except ccxt.BaseError as api_error:
        logger.error(f"Exchange API Error: {api_error}")
    except KeyboardInterrupt:
        logger.warning("Bot interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await close_exchange()
        logger.info("Exchange connection closed. Bot has stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Exiting AutoBC Trading Bot.")
