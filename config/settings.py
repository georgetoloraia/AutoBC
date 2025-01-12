import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Exchange API Keys
API_KEY = os.getenv('API_KEY')
SECRET = os.getenv('SECRET')

# Telegram API keys
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Log for debugging
# print(f"API_KEY: {API_KEY}")
# print(f"SECRET: {SECRET}")
# print(f"TELEGRAM_TOKEN: {TELEGRAM_TOKEN}")
# print(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")

# Trading Parameters
USE_ML = False  # Disabled for now, as you're not using ChatGPT or ML
ML_MODEL_PATH = "data/ml_model.pkl"
OPENAI_API_KEY = os.getenv('open_api_key')

quote_currency = False  # If true, trade all pairs with the quote currency (e.g., USDT)
INITIAL_INVESTMENT = 5.0  # USD
STOP_LOSS_PERCENTAGE = 0.02  # 2%
TAKE_PROFIT_PERCENTAGE = 0.05  # Initial take-profit percentage (5%)

# ---------------------
BUY_CONFIDENCE_THRESHOLD = 0.6
SELL_CONFIDENCE_THRESHOLD = 0.6

DESIRED_COINS = ["1000SATS/USDT",
                 "NOT/USDT",
                 "COMBO/USDT",
                 "PEOPLE/USDT",
                 "PEPE/USDT",
                 "COOKIE/USDT",
                 "IQ/USDT",
                 "D/USDT",
                 "POND/USDT",
                 "SUI/USDT",
                 "MBL/USDT",
                 "AI/USDT",
                 "LTO/USDT",
                 "RAY/USDT",
                 "HARD/USDT"
                 ]

# Dynamic Profit-Taking Parameters
PROFIT_STEP = 0.005  # 0.5% increment for positive indicator signals
MAX_PROFIT_PERCENTAGE = 0.30  # Cap at 30% maximum profit

TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h']

