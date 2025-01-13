import logging
from indicators.technical_indicators import calculate_indicators
from config.settings import TIMEFRAMES, TIMEFRAME_WEIGHTS, INDICATOR_WEIGHTS, BUY_CONFIDENCE_THRESHOLD, SELL_CONFIDENCE_THRESHOLD
import pandas as pd

logger = logging.getLogger(__name__)

def simplified_evaluate_trading_signals(data):
    """
    Evaluate trading signals based on technical indicators across multiple timeframes.

    Parameters:
        data (dict): Dictionary where keys are timeframes (e.g., '3m', '5m') and values are pandas DataFrames
                     with OHLCV data.

    Returns:
        str: "buy", "sell", or "wait" based on aggregated confidence scores.
    """
    aggregate_buy_confidence = 0
    aggregate_sell_confidence = 0
    signals = {}

    for timeframe in TIMEFRAMES:
        if timeframe not in data:
            logger.info(f"No data available for {timeframe}")
            continue

        df = data[timeframe]
        if df.empty:
            logger.info(f"DataFrame is empty for {timeframe} timeframe.")
            continue

        # Calculate indicators
        try:
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else None
        except Exception as e:
            logger.error(f"Error calculating indicators for {timeframe}: {e}")
            continue

        # Buy conditions
        buy_conditions = [
            latest['close'] < latest['lower_band'],
            latest['rsi'] < 30,
            latest['macd'] > latest['macd_signal'],
            latest['adx'] > 30 and latest['+DI'] > latest['-DI'],
            latest['close'] > latest['vwap'],
            latest['mfi'] < 20,
            previous is not None and latest['atr'] > previous['atr'],  # Compare current ATR with its previous value
            previous is not None and latest['obv'] > previous['obv']   # Compare current OBV with its previous value
        ]

        # Sell conditions
        sell_conditions = [
            latest['close'] > latest['upper_band'],
            latest['rsi'] > 70,
            latest['macd'] < latest['macd_signal'],
            latest['adx'] > 25 and latest['-DI'] > latest['+DI'],
            latest['close'] < latest['vwap'],
            latest['mfi'] > 80,
            previous is not None and latest['atr'] < previous['atr'],  # Compare current ATR with its previous value
            previous is not None and latest['obv'] < previous['obv']   # Compare current OBV with its previous value
        ]

        # Evaluate buy and sell conditions
        buy_confidence = evaluate_conditions(buy_conditions)
        sell_confidence = evaluate_conditions(sell_conditions)

        # Apply timeframe weights
        timeframe_weight = TIMEFRAME_WEIGHTS.get(timeframe, 1.0)
        weighted_buy_confidence = buy_confidence * timeframe_weight
        weighted_sell_confidence = sell_confidence * timeframe_weight

        # Aggregate confidences
        aggregate_buy_confidence += weighted_buy_confidence
        aggregate_sell_confidence += weighted_sell_confidence

        # Store signals for debugging
        signals[timeframe] = {
            'buy_confidence': weighted_buy_confidence,
            'sell_confidence': weighted_sell_confidence
        }

    # Log detailed insights
    log_signal_details(signals, aggregate_buy_confidence, aggregate_sell_confidence)

    # Normalize weights
    total_weight = sum(TIMEFRAME_WEIGHTS.values())

    # Determine final signal
    return determine_final_signal(
        aggregate_buy_confidence,
        aggregate_sell_confidence,
        total_weight,
        BUY_CONFIDENCE_THRESHOLD,
        SELL_CONFIDENCE_THRESHOLD
    )


def evaluate_conditions(conditions):
    """
    Evaluate buy or sell conditions.

    Parameters:
        conditions (list): List of boolean conditions.

    Returns:
        float: Confidence score based on the conditions.
    """
    valid_conditions = [cond for cond in conditions if cond is not None]
    return sum(valid_conditions) / len(valid_conditions) if valid_conditions else 0.0


def log_signal_details(signals, aggregate_buy_confidence, aggregate_sell_confidence):
    """
    Log detailed signal confidence for each timeframe and aggregate results.

    Parameters:
        signals (dict): Signals with confidence scores per timeframe.
        aggregate_buy_confidence (float): Aggregate buy confidence.
        aggregate_sell_confidence (float): Aggregate sell confidence.
    """
    for timeframe, details in signals.items():
        logger.debug(f"Timeframe: {timeframe}, "
                     f"Buy Confidence: {details['buy_confidence']:.2f}, "
                     f"Sell Confidence: {details['sell_confidence']:.2f}")
    logger.info(f"Aggregate Buy Confidence: {aggregate_buy_confidence:.2f}")
    logger.info(f"Aggregate Sell Confidence: {aggregate_sell_confidence:.2f}")


def determine_final_signal(aggregate_buy, aggregate_sell, total_weight, buy_threshold, sell_threshold):
    """
    Determine the final signal based on aggregated confidences.

    Parameters:
        aggregate_buy (float): Aggregate buy confidence.
        aggregate_sell (float): Aggregate sell confidence.
        total_weight (float): Total weight of timeframes.
        buy_threshold (float): Buy confidence threshold.
        sell_threshold (float): Sell confidence threshold.

    Returns:
        str: "buy", "sell", or "wait".
    """
    avg_buy_confidence = aggregate_buy / total_weight
    avg_sell_confidence = aggregate_sell / total_weight

    if avg_buy_confidence >= buy_threshold:
        logger.info(f"Buy signal triggered with average buy confidence: {avg_buy_confidence:.2f}")
        return "buy"
    elif avg_sell_confidence >= sell_threshold:
        logger.info(f"Sell signal triggered with average sell confidence: {avg_sell_confidence:.2f}")
        return "sell"

    logger.info("Market is indecisive. Returning 'wait' signal.")
    return "wait"
