import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('API_KEY')
SECRET = os.getenv('SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

quote_currency = 'USDT'
initial_investment = 5.0  # investment amount | Modifi if need
rsi_period = 14  # User's RSI period
commission_rate = 0.001  # 0.1% | Modifi if need
stop_loss_percentage = 0.015  # 5% stop loss | Modifi if need
take_profit_percentage = 0.05  # 10% take profit | Modifi if need
