import os
from dotenv import load_dotenv

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
stop_loss_percentage = 3      # first test | Modifi if need
take_profit_percentage = 2    # first test | Modifi if need

DESIRED_COINS = ["1000SATS/USDT",
                 "NOT/USDT",
                 "COMBO/USDT",
                 "PEOPLE/USDT",
                 "PEPE/USDT",
                 "BTC/USDT"
                 ]



# saved curency
'''
"BAKE/USDT",
                 "COS/USDT",
                 "XAI/USDT",
                 "IMX/USDT",
                 "FLOKI/USDT",
                 "STMX/USDT",
                 "MBL/USDT",
                 "AERGO/USDT",
                 "ZK/USDT",
                 "SOL/USDT",
                 "LINK/USDT",
                 "FTM/USDT",
                 "AUDIO/USDT",
                 "IO/USDT",
                 "BB/USDT",
'''