import logging
from indicators.technical_indicators import calculate_indicators
from config.settings import (
    BUY_CONFIDENCE_THRESHOLD,
    SELL_CONFIDENCE_THRESHOLD,
)

logger = logging.getLogger(__name__)

def define_short_term_strategy(df, mode="buy"):
    """
    Define short-term trading strategy for 15-minute timeframe.

    Parameters:
        df (pd.DataFrame): DataFrame containing OHLCV data with calculated indicators.
        mode (str): "buy" or "sell" to define the respective conditions.

    Returns:
        bool: True if the conditions for buy/sell are met, False otherwise.
    """
    if len(df) < 4:  # Ensure enough data points
        return False

    # Get the last four rows
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    prev_2 = df.iloc[-3]
    prev_3 = df.iloc[-4]

    if mode == "buy":
        # Detect downward trend and upward reversal
        downward_trend = prev_3['close'] > prev_2['close'] > previous['close']
        upward_reversal = latest['close'] > previous['close']

        # Indicators
        # rsi_oversold = latest['rsi'] < 40
        macd_bullish = latest['macd'] > latest['macd_signal']
        volume_spike = latest['volume'] > df['volume'].rolling(10).mean().iloc[-1]

        # Log details
        logger.info(f"BUY Conditions - || Downward Trend: {downward_trend}, Upward Reversal: {upward_reversal}")
        logger.info(f"BUY Indicators - || MACD Bullish: {macd_bullish}, Volume Spike: {volume_spike}")

        # Combine conditions
        return downward_trend and upward_reversal and macd_bullish and volume_spike

    elif mode == "sell":
        # Detect upward trend and downward reversal
        upward_trend = prev_3['close'] < prev_2['close'] < previous['close']
        downward_reversal = latest['close'] < previous['close']

        # Indicators
        rsi_overbought = latest['rsi'] > 65
        macd_bearish = latest['macd'] < latest['macd_signal']
        volume_spike = latest['volume'] > df['volume'].rolling(10).mean().iloc[-1]

        # Log details
        # logger.info(f"SELL Conditions - Upward Trend: {upward_trend}, Downward Reversal: {downward_reversal}")
        # logger.info(f"SELL Indicators - RSI Overbought: {rsi_overbought}, MACD Bearish: {macd_bearish}, Volume Spike: {volume_spike}")

        # Combine conditions
        return upward_trend and downward_reversal and rsi_overbought and macd_bearish and volume_spike

    else:
        raise ValueError("Invalid mode. Use 'buy' or 'sell'.")


def simplified_evaluate_trading_signals(data, order_book):
    """
    Evaluate trading signals for 15-minute timeframe.

    Parameters:
        data (dict): Dictionary where keys are timeframes and values are DataFrames.
        order_book (dict): Order book data with 'bids' and 'asks'.

    Returns:
        str: "buy", "sell", or "wait".
    """
    logger.info("=== Evaluating 15-Minute Trading Signals ===")

    # Ensure 15-minute data is available
    if '15m' not in data:
        logger.warning("No data available for 15-minute timeframe.")
        return "wait"

    df_15m = data['15m']
    if df_15m.empty:
        logger.warning("15m DataFrame is empty.")
        return "wait"

    # Calculate indicators
    try:
        df_15m = calculate_indicators(df_15m)
    except Exception as e:
        logger.error(f"Error calculating indicators for 15m timeframe: {e}")
        return "wait"

    # Evaluate buy and sell signals
    buy_signal = define_short_term_strategy(df_15m, mode="buy")
    sell_signal = define_short_term_strategy(df_15m, mode="sell")

    # Evaluate order book signal
    order_book_signal = analyze_order_book(order_book)

    # Determine final action
    if buy_signal and order_book_signal:
        logger.info("Buy signal triggered for 15m strategy.")
        return "buy"
    elif sell_signal:
        logger.info("Sell signal triggered for 15m strategy.")
        return "sell"
    else:
        logger.info("No clear signal. Returning 'wait'.")
        return "wait"


def analyze_order_book(order_book):
    """
    Analyze order book data to evaluate buying or selling pressure.

    Parameters:
        order_book (dict): Order book data with 'bids' and 'asks'.

    Returns:
        bool: True if strong buying pressure, False otherwise.
    """
    bids = order_book.get('bids', [])
    asks = order_book.get('asks', [])

    if not bids or not asks:
        return False

    total_bid_volume = sum([bid[1] for bid in bids])
    total_ask_volume = sum([ask[1] for ask in asks])
    spread = asks[0][0] - bids[0][0]

    logger.info(f"Order Book Analysis:")
    logger.info(f"  - Total Bid Volume: {total_bid_volume:.2f}")
    logger.info(f"  - Total Ask Volume: {total_ask_volume:.2f}")
    logger.info(f"  - Bid-Ask Spread: {spread:.6f}")

    return total_bid_volume > total_ask_volume



'''
DESIRED_COINS = [
    "BTC/USDT",  # Bitcoin - High volume, often volatile enough for short-term trading
    "ETH/USDT",  # Ethereum - High volume, moderate volatility
    "SOL/USDT",  # Solana - Volatile, often large intraday movements
    "ADA/USDT",  # Cardano - Popular and moderately volatile
    "BNB/USDT",  # Binance Coin - High volume, decent volatility
    "XRP/USDT",  # Ripple - Consistent volume and price action
    "DOGE/USDT",  # Dogecoin - Volatile, good for intraday strategies
    "MATIC/USDT",  # Polygon - High liquidity, reasonable price swings
    "LTC/USDT",  # Litecoin - Stable but shows good short-term trends
    "SHIB/USDT",  # Shiba Inu - Highly volatile, good for scalping
    "DOT/USDT",  # Polkadot - Decent liquidity and intraday moves
    "AVAX/USDT",  # Avalanche - Volatility and decent volume
    "APT/USDT",  # Aptos - Newer, higher volatility
    "LINK/USDT",  # Chainlink - Moderate liquidity, but trends well
    "ATOM/USDT",  # Cosmos - Good for consistent price trends
]


'''