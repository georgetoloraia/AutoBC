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

quote_currency = False  # If true, trade all pairs with the quote currency (e.g., USDT)
INITIAL_INVESTMENT = 5.0  # USD
STOP_LOSS_PERCENTAGE = 0.02  # 2%
TAKE_PROFIT_PERCENTAGE = 0.05  # Initial take-profit percentage (5%)

# Dynamic Profit-Taking Parameters
PROFIT_STEP = 0.005  # 0.5% increment for positive indicator signals
MAX_PROFIT_PERCENTAGE = 0.30  # Cap at 30% maximum profit

TIMEFRAMES = [
    '1s',
    '1m',
    '3m',
    '5m',
    '15m',
    '30m',
    '1h',
    '2h',
    '4h',
    '6h',
    '8h',
    '12h',
    '1d',
    '3d',
    '1w',
    '1M'
]

TIMEFRAMES_FOR_SCORE = ['1m', '3m', '5m']
BUY_CONFIDENCE_THRESHOLD = 0.55
SELL_CONFIDENCE_THRESHOLD = 0.6

TIMEFRAME_WEIGHTS = {
    '1s': 0.8,  # Ultra-short-term, highly noisy but useful for scalping
    '1m': 1.0,  # Short-term, quick signals
    '3m': 1.2,  # Slightly more stable than 1m
    '5m': 1.4,  # Short-term scalping, reliable for immediate trends
    '15m': 1.6, # Balance between noise and short-term trends
    '30m': 1.8, # Suitable for short-term directional trading
    '1h': 1.5,  # Trend confirmation for short-term trading
    '2h': 1.3,  # Supporting longer short-term trends
    '4h': 1.0,  # Less influence, better for intraday/swing
    '6h': 0.8,  # Minimal impact on short-term decisions
    '8h': 0.6,  # Rarely used for short-term trading
    '12h': 0.4, # Better for swing/medium-term
    '1d': 0.2,  # Long-term trend confirmation
    '3d': 0.1,  # Minimal impact on short-term trades
    '1w': 0.05, # Negligible impact for scalping
    '1M': 0.01  # Almost no relevance for short-term trading
}




TIMEFRAME_WEIGHTS_FALSE = {
    '1m': 0.8,   # Short-term, very noisy, low weight
    '3m': 0.9,   # Slightly more reliable than 1m
    '5m': 1.2,   # Common timeframe for scalping
    '15m': 1.2,  # Balanced between short-term noise and trend reliability
    '30m': 0.8,  # Stronger signals, suitable for intraday trading
    '1h': 0.8    # Reliable for intraday and swing trading
}

INDICATOR_WEIGHTS = {
    'close < lower_band': 0.15,       # Bollinger Bands oversold
    'close > upper_band': 0.15,       # Bollinger Bands overbought
    'rsi < 30': 0.15,                 # RSI oversold
    'rsi > 70': 0.15,                 # RSI overbought
    'macd > macd_signal': 0.3,        # Strong bullish crossover
    'adx > 30 and +DI > -DI': 0.3,    # Confirmed trend strength
    'close > vwap': 0.1,              # Above VWAP (bullish momentum)
    'mfi < 20': 0.1,                  # Oversold condition (volume-based)
    'atr > atr.shift(1)': 0.1,        # Increasing volatility
    'obv > obv.shift(1)': 0.1         # Positive volume flow
}


DESIRED_COINS = [
    # High Liquidity and Stability
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT", "MATIC/USDT",

    # Moderate Volatility
    "SOL/USDT", "DOT/USDT", "AVAX/USDT", "ATOM/USDT", "LTC/USDT", "LINK/USDT", 
    "NEAR/USDT", "ALGO/USDT",

    # Speculative and High Volatility
    "DOGE/USDT", "PEPE/USDT", "SHIB/USDT", "APT/USDT", "PROM/USDT", "RNDR/USDT", 
    "ROSE/USDT", "STG/USDT",

    # Momentum Plays
    "GALA/USDT", "FTM/USDT", "SAND/USDT", "AXS/USDT", "IMX/USDT", "CFX/USDT"
]


DESIRED_COINS_FALSE = [
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