import logging
from indicators.technical_indicators import calculate_indicators
from config.settings import (
    TIMEFRAMES,
    TIMEFRAME_WEIGHTS,
    INDICATOR_WEIGHTS,
    BUY_CONFIDENCE_THRESHOLD,
    SELL_CONFIDENCE_THRESHOLD,
)

logger = logging.getLogger(__name__)

def simplified_evaluate_trading_signals(data, order_book):
    """
    Evaluate trading signals based on technical indicators across multiple timeframes.

    Parameters:
        data (dict): Dictionary where keys are timeframes (e.g., '1m', '3m') and values are pandas DataFrames
                     with OHLCV data.
        order_book (dict): Order book data with 'bids' and 'asks'.

    Returns:
        str: "buy", "sell", or "wait".
    """

    total_weight = sum(TIMEFRAME_WEIGHTS.values())
    TIMEFRAME_WEIGHTS_NORMALIZED = {k: v / total_weight for k, v in TIMEFRAME_WEIGHTS.items()}

    signals = {}
    aggregate_buy_confidence = 0
    aggregate_sell_confidence = 0

    logger.info("=== Starting Signal Evaluation ===")

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

        # Define buy and sell conditions
        buy_conditions = define_conditions(latest, previous, mode="buy")
        sell_conditions = define_conditions(latest, previous, mode="sell")

        # Evaluate conditions
        buy_confidence = evaluate_conditions(buy_conditions, INDICATOR_WEIGHTS)
        sell_confidence = evaluate_conditions(sell_conditions, INDICATOR_WEIGHTS)

        # Apply timeframe weight
        timeframe_weight = TIMEFRAME_WEIGHTS_NORMALIZED.get(timeframe, 1.0)
        weighted_buy_confidence = buy_confidence * timeframe_weight
        weighted_sell_confidence = sell_confidence * timeframe_weight

        # Aggregate confidences
        aggregate_buy_confidence += weighted_buy_confidence
        aggregate_sell_confidence += weighted_sell_confidence

        # Store confidence scores for the timeframe
        signals[timeframe] = {
            'buy_confidence': weighted_buy_confidence,
            'sell_confidence': weighted_sell_confidence,
            'raw_buy_confidence': buy_confidence,
            'raw_sell_confidence': sell_confidence,
        }

    # Log aggregate confidence scores
    log_signal_details(signals, aggregate_buy_confidence, aggregate_sell_confidence)

    avg_buy_confidence = aggregate_buy_confidence
    avg_sell_confidence = aggregate_sell_confidence

    # Evaluate order book data
    order_book_signal = analyze_order_book(order_book)

    # Log order book analysis
    logger.info(f"Order Book Signal: {'Strong Buy' if order_book_signal else 'No Buy Signal'}")

    # Determine the final signal
    signal = determine_final_signal(avg_buy_confidence, avg_sell_confidence, order_book_signal)
    logger.info(f"Final Determined Signal: {signal.upper()}")

    return signal

def define_conditions(latest, previous, mode="buy"):
    """
    Define conditions for buy or sell signals using technical indicators.

    Parameters:
        latest (pd.Series): Latest row of technical indicators.
        previous (pd.Series): Previous row of technical indicators.
        mode (str): "buy" or "sell" to define the respective conditions.

    Returns:
        list: List of boolean conditions.
    """
    if mode == "buy":
        return [
            latest['close'] < latest['lower_band'],
            latest['rsi'] < 30,
            latest['macd'] > latest['macd_signal'],
            latest['adx'] > 30 and latest['+DI'] > latest['-DI'],
            latest['close'] > latest['vwap'],
            latest['mfi'] < 20,
            previous is not None and latest['atr'] > previous['atr'],
            previous is not None and latest['obv'] > previous['obv']
        ]
    elif mode == "sell":
        return [
            latest['close'] > latest['upper_band'],
            latest['rsi'] > 70,
            latest['macd'] < latest['macd_signal'],
            latest['adx'] > 25 and latest['-DI'] > latest['+DI'],
            latest['close'] < latest['vwap'],
            latest['mfi'] > 80,
            previous is not None and latest['atr'] < previous['atr'],
            previous is not None and latest['obv'] < previous['obv']
        ]
    else:
        raise ValueError("Invalid mode. Use 'buy' or 'sell'.")

def evaluate_conditions(conditions, indicator_weights):
    """
    Evaluate conditions and calculate confidence score.

    Parameters:
        conditions (list): List of boolean conditions.
        indicator_weights (dict): Dictionary of indicator weights.

    Returns:
        float: Confidence score based on the conditions.
    """
    score = 0
    total_weight = sum(indicator_weights.values())
    for condition, weight in zip(conditions, indicator_weights.values()):
        if condition:
            score += weight
    return score / total_weight if total_weight > 0 else 0

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

def log_signal_details(signals, aggregate_buy_confidence, aggregate_sell_confidence):
    """
    Log detailed signal confidence for each timeframe and aggregate results.

    Parameters:
        signals (dict): Signals with confidence scores per timeframe.
        aggregate_buy_confidence (float): Aggregate buy confidence.
        aggregate_sell_confidence (float): Aggregate sell confidence.
    """
    logger.info("\n=== Signal Details by Timeframe ===")
    for timeframe, details in signals.items():
        logger.info(f"Timeframe: {timeframe}")
        logger.info(f"  - Buy Confidence: {details['buy_confidence']:.4f}")
        logger.info(f"  - Sell Confidence: {details['sell_confidence']:.4f}")

    logger.info("\n=== Aggregated Signal Summary ===")
    logger.info(f"Total Aggregate Buy Confidence: {aggregate_buy_confidence:.4f}")
    logger.info(f"Total Aggregate Sell Confidence: {aggregate_sell_confidence:.4f}")

    logger.info("\n=== Timeframe Weights ===")
    for timeframe, weight in TIMEFRAME_WEIGHTS.items():
        normalized_weight = weight / sum(TIMEFRAME_WEIGHTS.values())
        logger.info(f"Timeframe: {timeframe}, Weight: {weight:.4f}, Normalized: {normalized_weight:.4f}")


def determine_final_signal(avg_buy_confidence, avg_sell_confidence, order_book_signal):
    """
    Determine the final signal based on aggregated confidences and order book data.

    Parameters:
        avg_buy_confidence (float): Average buy confidence.
        avg_sell_confidence (float): Average sell confidence.
        order_book_signal (bool): Whether order book shows strong buying pressure.

    Returns:
        str: "buy", "sell", or "wait".
    """
    if avg_buy_confidence >= BUY_CONFIDENCE_THRESHOLD:
        logger.info(f"Buy signal triggered with avg buy confidence: {avg_buy_confidence:.2f} and order book signal.")
        return "buy"
    elif avg_sell_confidence >= SELL_CONFIDENCE_THRESHOLD:
        logger.info(f"Sell signal triggered with avg sell confidence: {avg_sell_confidence:.2f}.")
        return "sell"

    logger.info("No clear signals found. Returning 'wait'.")
    return "wait"
