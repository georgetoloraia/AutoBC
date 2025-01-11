import asyncio
import logging
import ccxt.async_support as ccxt
# from config import settings
from trading.trader import advanced_trade, close_exchange

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Add file handler to logger
file_handler = logging.FileHandler('results.txt')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)

# Main function
async def main():
    try:
        await advanced_trade()
    except Exception as e:
        logger.error(f"An error occurred in the main trading loop: {e}")
    finally:
        await close_exchange()
        logger.info("Exchange connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
