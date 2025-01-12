import logging
from indicators.technical_indicators import calculate_indicators
from config.settings import TIMEFRAMES, BUY_CONFIDENCE_THRESHOLD, SELL_CONFIDENCE_THRESHOLD, TIMEFRAME_WEIGHTS, INDICATOR_WEIGHTS

logger = logging.getLogger(__name__)

def simplified_evaluate_trading_signals(data):
    """
    Evaluate trading signals based on technical indicators across multiple timeframes.

    Parameters:
        data (dict): Dictionary where keys are timeframes (e.g., '3m', '5m') and values are pandas DataFrames
                     with OHLCV data.

    Returns:
        str or None: Returns "buy" if aggregate buy confidence is higher, "sell" if aggregate sell confidence is higher,
                     "wait" if market shows indecision, or None if no valid signals are found.
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
        except Exception as e:
            logger.error(f"Error calculating indicators for {timeframe}: {e}")
            continue

        # Evaluate buy and sell conditions
        buy_confidence = evaluate_conditions(latest, INDICATOR_WEIGHTS, buy=True)
        sell_confidence = evaluate_conditions(latest, INDICATOR_WEIGHTS, buy=False)

        # Adjust confidences with timeframe weight
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

    # Determine final signal
    return determine_final_signal(
        aggregate_buy_confidence,
        aggregate_sell_confidence,
        len(TIMEFRAMES),
        BUY_CONFIDENCE_THRESHOLD,
        SELL_CONFIDENCE_THRESHOLD
    )


def evaluate_conditions(latest, indicator_weights, buy=True):
    """
    Evaluate conditions for buy or sell signals.

    Parameters:
        latest (pd.Series): Latest row of indicator data.
        indicator_weights (dict): Dictionary of conditions and weights.
        buy (bool): If True, evaluates buy conditions; otherwise, evaluates sell conditions.

    Returns:
        float: Confidence score based on the conditions.
    """
    score = 0
    for condition, weight in indicator_weights.items():
        try:
            # Adjust condition logic for buy/sell
            condition_logic = condition if buy else f"not ({condition})"
            condition_met = eval(condition_logic, None, latest.to_dict())
            if condition_met:
                score += weight
            else:
                score -= weight
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            continue

    return max(0, min(score, 1))  # Clamp confidence score between 0 and 1


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


def determine_final_signal(aggregate_buy, aggregate_sell, num_timeframes, buy_threshold, sell_threshold):
    """
    Determine the final signal based on aggregated confidences.

    Parameters:
        aggregate_buy (float): Aggregate buy confidence.
        aggregate_sell (float): Aggregate sell confidence.
        num_timeframes (int): Total number of timeframes.
        buy_threshold (float): Buy confidence threshold.
        sell_threshold (float): Sell confidence threshold.

    Returns:
        str or None: "buy", "sell", "wait", or None.
    """
    avg_buy_confidence = aggregate_buy / num_timeframes
    avg_sell_confidence = aggregate_sell / num_timeframes

    if avg_buy_confidence >= buy_threshold:
        logger.info(f"Buy signal triggered with average buy confidence: {avg_buy_confidence:.2f}")
        return "buy"
    elif avg_sell_confidence >= sell_threshold:
        logger.info(f"Sell signal triggered with average sell confidence: {avg_sell_confidence:.2f}")
        return "sell"
    # elif abs(aggregate_buy - aggregate_sell) < 0.1:  # Example threshold for indecision
    #     logger.info("Market is indecisive. Returning 'wait' signal.")
    #     return "wait"

    logger.info("No valid signals found.")
    return 'wait'
