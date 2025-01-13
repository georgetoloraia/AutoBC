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

# Trading Parameters
USE_ML = False  # Disabled for now, as you're not using ChatGPT or ML
ML_MODEL_PATH = "data/ml_model.pkl"
OPENAI_API_KEY = os.getenv('open_api_key')

quote_currency = True  # If true, trade all pairs with the quote currency (e.g., USDT)
INITIAL_INVESTMENT = 5.0  # USD
STOP_LOSS_PERCENTAGE = 0.02  # 2%
TAKE_PROFIT_PERCENTAGE = 0.05  # Initial take-profit percentage (5%)

# Dynamic Profit-Taking Parameters
PROFIT_STEP = 0.005  # 0.5% increment for positive indicator signals
MAX_PROFIT_PERCENTAGE = 0.30  # Cap at 30% maximum profit

TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h']
BUY_CONFIDENCE_THRESHOLD = 0.8
SELL_CONFIDENCE_THRESHOLD = 0.8

TIMEFRAME_WEIGHTS = {
    '1m': 0.4,   # Short-term, very noisy, low weight
    '3m': 0.6,   # Slightly more reliable than 1m
    '5m': 1.0,   # Common timeframe for scalping
    '15m': 1.2,  # Balanced between short-term noise and trend reliability
    '30m': 1.0,  # Stronger signals, suitable for intraday trading
    '1h': 0.8    # Reliable for intraday and swing trading
}
'''
This wait
    '4h': 1.5,   # Suitable for swing trading and longer-term trends
    '1d': 2.0    # Best for confirming overall market direction
'''

INDICATOR_WEIGHTS = {
    # Bollinger Bands
    'close < lower_band': 0.2,   # Price below lower Bollinger Band (oversold)
    'close > upper_band': 0.2,   # Price above upper Bollinger Band (overbought)

    # RSI
    'rsi < 30': 0.2,             # RSI below 30 (oversold)
    'rsi > 70': 0.2,             # RSI above 70 (overbought)

    # MACD
    'macd > macd_signal': 0.25,  # MACD bullish crossover
    'macd < macd_signal': 0.25,  # MACD bearish crossover

    # ADX and Directional Indicators
    'adx > 30 and +DI > -DI': 0.25,  # Strong trend with bullish directional movement
    'adx > 25 and -DI > +DI': 0.25,  # Strong trend with bearish directional movement

    # Money Flow Index (MFI)
    'mfi < 20': 0.15,            # MFI indicating oversold
    'mfi > 80': 0.15,            # MFI indicating overbought

    # VWAP
    'close > vwap': 0.1,         # Price above VWAP (bullish)
    'close < vwap': 0.1,         # Price below VWAP (bearish)

    # Average True Range (ATR)
    'atr > atr.shift(1)': 0.1,   # Increasing volatility

    # OBV (On-Balance Volume)
    'obv > obv.shift(1)': 0.1,   # Positive volume flow (bullish)
    'obv < obv.shift(1)': 0.1    # Negative volume flow (bearish)
}



DESIRED_COINS = [
    "BTC/USDT",   # Bitcoin - High liquidity, relatively stable
    "ETH/USDT",   # Ethereum - High liquidity, good for consistent trends
    "BNB/USDT",   # Binance Coin - High liquidity, suitable for Binance ecosystem traders
    "SOL/USDT",   # Solana - Increasing adoption, moderate volatility
    "XRP/USDT",   # Ripple - High liquidity, speculative and volatile
    "ADA/USDT",   # Cardano - Strong community support and steady price action
    "DOGE/USDT",  # Dogecoin - Popular and volatile, speculative trading
    "PEPE/USDT",  # PEPE - High speculation and volatility
    "PROM/USDT",  # Prom - Top gainer, high momentum
    "STG/USDT",   # Stargate - Moderate liquidity, potential short-term momentum
    "PNUT/USDT",  # PNUT - Strong gain potential in short-term trends
    "XVS/USDT",   # Venus - Trending with significant price change
    "KNC/USDT",   # Kyber Network - Moderate momentum, short-term opportunities
    "TFUEL/USDT", # Theta Fuel - Significant short-term price changes
    "MATIC/USDT", # Polygon - Stable upward trends with moderate volatility
]
