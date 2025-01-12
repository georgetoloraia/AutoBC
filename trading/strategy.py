import logging
from indicators.technical_indicators import calculate_indicators
from config.settings import TIMEFRAMES, BUY_CONFIDENCE_THRESHOLD, SELL_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

def simplified_evaluate_trading_signals(data):
    """
    Evaluate trading signals based on technical indicators across multiple timeframes.

    Parameters:
        data (dict): Dictionary where keys are timeframes (e.g., '3m', '5m') and values are pandas DataFrames
                     with OHLCV data.

    Returns:
        str or None: Returns "buy" if aggregate buy confidence is higher, "sell" if aggregate sell confidence is higher,
                     or None if no valid signals are found.
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

        # Define buy and sell conditions
        buy_conditions = [
            latest['close'] < latest['lower_band'],  # Price below lower Bollinger Band
            latest['rsi'] < 30,  # RSI below 30 (oversold)
            latest['macd'] > latest['macd_signal'],  # MACD bullish crossover
            latest['adx'] > 30 and latest['+DI'] > latest['-DI'],  # Strong ADX trend
            latest['close'] > latest['vwap'],  # Price above VWAP
            latest['mfi'] < 20  # Money Flow Index indicating oversold
        ]

        sell_conditions = [
            latest['close'] > latest['upper_band'],  # Price above upper Bollinger Band
            latest['rsi'] > 70,  # RSI above 70 (overbought)
            latest['macd'] < latest['macd_signal'],  # MACD bearish crossover
            latest['adx'] > 25 and latest['-DI'] > latest['+DI'],  # Strong ADX trend
            latest['close'] < latest['vwap'],  # Price below VWAP
            latest['mfi'] > 80  # Money Flow Index indicating overbought
        ]

        # Calculate confidence scores
        buy_confidence = sum([1 if cond else 0 for cond in buy_conditions]) / len(buy_conditions)
        sell_confidence = sum([1 if cond else 0 for cond in sell_conditions]) / len(sell_conditions)
        logger.debug(f"Timeframe: {timeframe}")
        logger.debug(f"Buy Confidence: {buy_confidence:.2f}")
        logger.debug(f"Sell Confidence: {sell_confidence:.2f}")

        # Aggregate confidences
        aggregate_buy_confidence += buy_confidence
        aggregate_sell_confidence += sell_confidence

        # Store signals for logging/debugging
        signals[timeframe] = {
            'buy_confidence': buy_confidence,
            'sell_confidence': sell_confidence
        }

    # Determine final signal
    if aggregate_buy_confidence > aggregate_sell_confidence and aggregate_buy_confidence / len(TIMEFRAMES) >= BUY_CONFIDENCE_THRESHOLD:
        logger.info(f"Buy signal triggered with aggregate buy confidence: {aggregate_buy_confidence:.2f}")
        return "buy"
    elif aggregate_sell_confidence > aggregate_buy_confidence and aggregate_sell_confidence / len(TIMEFRAMES) >= SELL_CONFIDENCE_THRESHOLD:
        logger.info(f"Sell signal triggered with aggregate sell confidence: {aggregate_sell_confidence:.2f}")
        return "sell"

    logger.info("No valid signals found.")
    return signals
