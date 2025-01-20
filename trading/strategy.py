import logging
from indicators.technical_indicators import calculate_indicators
from config.settings import (
    TIMEFRAME_WEIGHTS,
    BUY_CONFIDENCE_THRESHOLD,
    SELL_CONFIDENCE_THRESHOLD,
)

logger = logging.getLogger(__name__)

def define_reversal_strategy(df, mode="buy"):
    """
    Detect a downward "close" followed by an upward one for buy/sell signals.

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
        # Downward trend followed by upward close
        downward_trend = prev_3['close'] > prev_2['close'] > previous['close']
        upward_reversal = latest['close'] > previous['close']

        # Add confirmation indicators
        rsi_oversold = latest['rsi'] < 30
        macd_bullish = latest['macd'] > latest['macd_signal']
        adx_trending = latest['adx'] > 25

        return downward_trend and upward_reversal and rsi_oversold and macd_bullish and adx_trending

    elif mode == "sell":
        # Upward trend followed by downward close
        upward_trend = prev_3['close'] < prev_2['close'] < previous['close']
        downward_reversal = latest['close'] < previous['close']

        # Add confirmation indicators
        rsi_overbought = latest['rsi'] > 70
        macd_bearish = latest['macd'] < latest['macd_signal']
        adx_trending = latest['adx'] > 25

        return upward_trend and downward_reversal and rsi_overbought and macd_bearish and adx_trending

    else:
        raise ValueError("Invalid mode. Use 'buy' or 'sell'.")

def simplified_evaluate_trading_signals(data, order_book):
    """
    Evaluate trading signals based on the reversal strategy in the 15-minute timeframe.

    Parameters:
        data (dict): Dictionary where keys are timeframes and values are DataFrames.
        order_book (dict): Order book data with 'bids' and 'asks'.

    Returns:
        str: "buy", "sell", or "wait".
    """
    logger.info("=== Evaluating Trading Signals ===")

    # Check for 15m timeframe
    if '15m' not in data:
        logger.warning("No data available for 15m timeframe.")
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

    # Evaluate reversal strategy
    buy_signal = define_reversal_strategy(df_15m, mode="buy")
    logger.info(f"buy_signal: == {buy_signal}")
    sell_signal = define_reversal_strategy(df_15m, mode="sell")
    logger.info(f"sell_signal: == {sell_signal}")

    # Evaluate order book
    order_book_signal = analyze_order_book(order_book)

    # Determine final signal
    if buy_signal and order_book_signal:
        logger.info("Buy signal triggered based on 15m reversal strategy and order book analysis.")
        return "buy"
    elif sell_signal:
        logger.info("Sell signal triggered based on 15m reversal strategy.")
        return "sell"
    else:
        logger.info("No clear signals found. Returning 'wait'.")
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
