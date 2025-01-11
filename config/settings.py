import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Exchange API Keys
API_KEY = os.getenv('api_key')
SECRET = os.getenv('secret')

# Telegram API keys
TELEGRAM_TOKEN = os.getenv('telegram_token')
TELEGRAM_CHAT_ID = os.getenv('telegram_chat_id')

# Log for debugging
print(f"API_KEY: {API_KEY}")
print(f"SECRET: {SECRET}")
print(f"TELEGRAM_TOKEN: {TELEGRAM_TOKEN}")
print(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")

# Trading Parameters
USE_ML = False  # Disabled for now, as you're not using ChatGPT or ML
ML_MODEL_PATH = "data/ml_model.pkl"
OPENAI_API_KEY = os.getenv('open_api_key')

quote_currency = False  # If true, trade all pairs with the quote currency (e.g., USDT)
INITIAL_INVESTMENT = 5.0  # USD
STOP_LOSS_PERCENTAGE = 0.02  # 2%
TAKE_PROFIT_PERCENTAGE = 0.05  # Initial take-profit percentage (5%)
DESIRED_COINS = ["BTC/USDT", "ETH/USDT", "PEPE/USDT"]

# Dynamic Profit-Taking Parameters
PROFIT_STEP = 0.005  # 0.5% increment for positive indicator signals
MAX_PROFIT_PERCENTAGE = 0.30  # Cap at 30% maximum profit






'''
# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('API_KEY')
SECRET = os.getenv('SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# quote_currency = 'USDT'
quote_currency = False
initial_investment = 5.0  # investment amount | Modifi if need
rsi_period = 14  # User's RSI period
commission_rate = 0.05  #| Modifi if need
stop_loss_percentage = 0.02  # | Modifi if need
take_profit_percentage = 0.015  # | Modifi if need

DESIRED_COINS = ["1000SATS/USDT",
                 "SOL/USDT",
                 "LINK/USDT",
                 "FTM/USDT",
                 "AUDIO/USDT",
                 "IO/USDT",
                 "BB/USDT",
                 "NOT/USDT",
                 "COMBO/USDT",
                 "PEOPLE/USDT",
                 "PEPE/USDT",
                 "BAKE/USDT",
                 "COS/USDT",
                 "XAI/USDT",
                 "IMX/USDT",
                 "FLOKI/USDT",
                 "STMX/USDT",
                 "MBL/USDT",
                 "AERGO/USDT",
                 "ZK/USDT",
                 ]

'''