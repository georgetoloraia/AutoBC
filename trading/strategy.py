import logging
from indicators.technical_indicators import calculate_indicators
from config.settings import TIMEFRAMES, TIMEFRAME_WEIGHTS, INDICATOR_WEIGHTS, BUY_CONFIDENCE_THRESHOLD, SELL_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

def simplified_evaluate_trading_signals(data, order_book):
    """
    Evaluate trading signals based on technical indicators across multiple timeframes.

    Parameters:
        data (dict): Dictionary where keys are timeframes (e.g., '1m', '3m') and values are pandas DataFrames
                     with OHLCV data.

    Returns:
        dict: Dictionary containing buy and sell confidence scores per timeframe.
    """
    signals = {}
    aggregate_buy_confidence = 0
    aggregate_sell_confidence = 0

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
        buy_conditions = [
            latest['close'] < latest['lower_band'],  # Price below lower Bollinger Band
            latest['rsi'] < 30,                     # RSI below 30 (oversold)
            latest['macd'] > latest['macd_signal'], # MACD bullish crossover
            latest['adx'] > 30 and latest['+DI'] > latest['-DI'],  # Strong trend with positive directional movement
            latest['close'] > latest['vwap'],       # Price above VWAP
            latest['mfi'] < 20,                     # Money Flow Index indicating oversold
            previous is not None and latest['atr'] > previous['atr'],  # Increasing ATR
            previous is not None and latest['obv'] > previous['obv']   # Increasing OBV
        ]

        sell_conditions = [
            latest['close'] > latest['upper_band'],  # Price above upper Bollinger Band
            latest['rsi'] > 70,                     # RSI above 70 (overbought)
            latest['macd'] < latest['macd_signal'], # MACD bearish crossover
            latest['adx'] > 25 and latest['-DI'] > latest['+DI'],  # Strong trend with negative directional movement
            latest['close'] < latest['vwap'],       # Price below VWAP
            latest['mfi'] > 80,                     # Money Flow Index indicating overbought
            previous is not None and latest['atr'] < previous['atr'],  # Decreasing ATR
            previous is not None and latest['obv'] < previous['obv']   # Decreasing OBV
        ]

        # Evaluate conditions
        buy_confidence = evaluate_conditions(buy_conditions, INDICATOR_WEIGHTS)
        sell_confidence = evaluate_conditions(sell_conditions, INDICATOR_WEIGHTS)

        # Apply timeframe weight
        timeframe_weight = TIMEFRAME_WEIGHTS.get(timeframe, 1.0)
        weighted_buy_confidence = buy_confidence * timeframe_weight
        weighted_sell_confidence = sell_confidence * timeframe_weight

        # Aggregate confidences
        aggregate_buy_confidence += weighted_buy_confidence
        aggregate_sell_confidence += weighted_sell_confidence

        # Store confidence scores for the timeframe
        signals[timeframe] = {
            'buy_confidence': weighted_buy_confidence,
            'sell_confidence': weighted_sell_confidence
        }

    # Log aggregate confidence scores
    logger.info(f"Aggregate Buy Confidence: {aggregate_buy_confidence:.2f}")
    logger.info(f"Aggregate Sell Confidence: {aggregate_sell_confidence:.2f}")

    # Determine the final signal
    total_weight = sum(TIMEFRAME_WEIGHTS.values())
    avg_buy_confidence = aggregate_buy_confidence / total_weight
    avg_sell_confidence = aggregate_sell_confidence / total_weight

    # Evaluate order book data
    total_bid_volume, total_ask_volume, spread = analyze_order_book(order_book)
    if total_bid_volume > 1.5 * total_ask_volume:  # Example threshold
        logger.info("Strong buying pressure detected based on order book.")
        order_book_signal = True
    else:
        order_book_signal = False

    if avg_buy_confidence >= BUY_CONFIDENCE_THRESHOLD and order_book_signal:
        logger.info(f"Buy signal triggered with avg buy confidence: {avg_buy_confidence:.2f} and Book_order: {order_book_signal}")
        return "buy"
    elif avg_sell_confidence >= SELL_CONFIDENCE_THRESHOLD:
        logger.info(f"Sell signal triggered with avg sell confidence: {avg_sell_confidence:.2f}")
        return "sell"

    logger.info("No clear signals found. Returning 'wait'")
    return "wait"


def evaluate_conditions(conditions, indicator_weights):
    """
    Evaluate buy or sell conditions.

    Parameters:
        conditions (list): List of boolean conditions.
        indicator_weights (dict): Dictionary of indicator weights.

    Returns:
        float: Confidence score based on the conditions.
    """
    score = 0
    total_weight = 0

    for condition, weight in zip(conditions, indicator_weights.values()):
        total_weight += weight
        score += weight if condition else 0

    return score / total_weight if total_weight > 0 else 0

def analyze_order_book(order_book):
    bids = order_book.get('bids', [])
    asks = order_book.get('asks', [])

    if not bids or not asks:
        return None, None, None

    total_bid_volume = sum([bid[1] for bid in bids])
    total_ask_volume = sum([ask[1] for ask in asks])
    spread = asks[0][0] - bids[0][0]  # Calculate bid-ask spread

    return total_bid_volume, total_ask_volume, spread
