import logging
import numpy as np
import pandas as pd
from indicators.technical_indicators import calculate_indicators
from config.settings import (
    BUY_CONFIDENCE_THRESHOLD,
    SELL_CONFIDENCE_THRESHOLD,
    RISK_PER_TRADE,  # Percentage of balance to risk per trade
    TRAILING_STOP_PERCENTAGE,  # Percentage for trailing stop
)

logger = logging.getLogger(__name__)

def define_short_term_strategy(df, mode="buy"):
    """
    Define short-term trading strategy with weighted conditions and trend filter.

    Parameters:
        df (pd.DataFrame): DataFrame containing OHLCV data with calculated indicators.
        mode (str): "buy" or "sell" to define the respective conditions.

    Returns:
        float: A confidence score between 0 and 1, where 1 indicates high confidence.
    """
    if len(df) < 4:  # Ensure enough data points for trend detection
        return 0.0

    # Get the last four rows
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    prev_2 = df.iloc[-3]
    prev_3 = df.iloc[-4]

    # Trend filter (200-period moving average)
    if 'ma_200' not in df.columns or pd.isna(df['ma_200'].iloc[-1]):
        trend_filter = True  # Assume no trend filter if ma_200 is not available
    else:
        trend_filter = latest['close'] > df['ma_200'].iloc[-1]

    if mode == "buy":
        # Trend conditions
        downward_trend = prev_3['close'] > prev_2['close'] > previous['close']
        upward_reversal = latest['close'] > previous['close']

        # Indicator conditions
        macd_bullish = latest['macd'] > latest['macd_signal']
        rsi_oversold = latest['rsi'] < 45
        volume_spike = latest['volume'] > df['volume'].rolling(20).mean().iloc[-1]

        # Weighted confidence score
        confidence = (
            0.4 * downward_trend +  # Trend is most important
            0.3 * upward_reversal +
            0.2 * macd_bullish +
            0.1 * rsi_oversold +
            0.1 * volume_spike
        )

        # Apply trend filter
        if not trend_filter:
            confidence *= 0.5  # Reduce confidence if against the trend

        logger.info(f"BUY Confidence: {confidence:.2f}")
        return confidence

    elif mode == "sell":
        # Trend conditions
        upward_trend = prev_3['close'] < prev_2['close'] < previous['close']
        downward_reversal = latest['close'] < previous['close']

        # Indicator conditions
        macd_bearish = latest['macd'] < latest['macd_signal']
        rsi_overbought = latest['rsi'] > 65
        volume_spike = latest['volume'] > df['volume'].rolling(20).mean().iloc[-1]

        # Weighted confidence score
        confidence = (
            0.4 * upward_trend +  # Trend is most important
            0.3 * downward_reversal +
            0.2 * macd_bearish +
            0.1 * rsi_overbought +
            0.1 * volume_spike
        )

        # Apply trend filter
        if trend_filter:
            confidence *= 0.5  # Reduce confidence if against the trend

        logger.info(f"SELL Confidence: {confidence:.2f}")
        return confidence

    else:
        raise ValueError("Invalid mode. Use 'buy' or 'sell'.")


def simplified_evaluate_trading_signals(data, order_book):
    """
    Evaluate trading signals with dynamic thresholds and risk management.

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

    # Evaluate buy and sell signals with confidence scores
    buy_confidence = define_short_term_strategy(df_15m, mode="buy")
    sell_confidence = define_short_term_strategy(df_15m, mode="sell")

    # Evaluate order book signal
    order_book_signal = analyze_order_book(order_book)

    # Determine final action based on confidence and thresholds
    if buy_confidence >= BUY_CONFIDENCE_THRESHOLD and order_book_signal:
        logger.info(f"Buy signal triggered with confidence: {buy_confidence:.2f}")
        return "buy"
    # elif sell_confidence >= SELL_CONFIDENCE_THRESHOLD:
    #     logger.info(f"Sell signal triggered with confidence: {sell_confidence:.2f}")
    #     return "sell"
    else:
        logger.info("No clear signal. Returning 'wait'.")
        return "wait"


def analyze_order_book(order_book):
    """
    Analyze order book data with depth consideration.

    Parameters:
        order_book (dict): Order book data with 'bids' and 'asks'.

    Returns:
        float: A score between 0 and 1 indicating buying pressure.
    """
    bids = order_book.get('bids', [])
    asks = order_book.get('asks', [])

    if not bids or not asks:
        return 0.0

    # Calculate total bid and ask volume
    total_bid_volume = sum([bid[1] for bid in bids])
    total_ask_volume = sum([ask[1] for ask in asks])

    # Calculate depth-weighted score
    bid_ask_ratio = total_bid_volume / (total_bid_volume + total_ask_volume)
    spread = asks[0][0] - bids[0][0]
    spread_score = 1.0 if spread < 0.001 else 0.5  # Adjust based on market

    # Combine scores
    score = 0.7 * bid_ask_ratio + 0.3 * spread_score

    logger.info(f"Order Book Score: {score:.2f}")
    return score