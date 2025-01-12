import logging
from indicators.technical_indicators import calculate_indicators

logger = logging.getLogger(__name__)

def simplified_evaluate_trading_signals(data):
    """
    Evaluate trading signals based on technical indicators across multiple timeframes.

    Parameters:
        data (dict): Dictionary where keys are timeframes (e.g., '3m', '5m') and values are pandas DataFrames
                     with OHLCV data.

    Returns:
        str or None: Returns "buy" if at least 2 timeframes give a buy signal, "sell" if strong sell signals exist,
                     or None if no valid signals are found.
    """
    signals = {}
    timeframe_to_check = ['1m', '3m', '5m', '15m', '30m', '1h']
    buy_signals_count = 0

    for timeframe in timeframe_to_check:
        if timeframe not in data:
            logger.info(f"No data available for {timeframe}")
            continue

        df = data[timeframe]
        if df.empty:
            logger.info(f"DataFrame is empty for {timeframe} timeframe.")
            continue

        # Calculate indicators for the dataframe
        df = calculate_indicators(df)
        latest = df.iloc[-1]

        # Define buy and sell conditions
        buy_conditions = [
            latest['close'] < latest['lower_band'],
            latest['rsi'] < 30,
            latest['macd'] > latest['macd_signal'],
            latest['adx'] > 30 and latest['+DI'] > latest['-DI'],
            latest['close'] > latest['vwap'],
            latest['mfi'] < 20
        ]

        sell_conditions = [
            latest['close'] > latest['upper_band'],
            latest['rsi'] > 70,
            latest['macd'] < latest['macd_signal'],
            latest['adx'] > 25 and latest['-DI'] > latest['+DI'],
            latest['close'] < latest['vwap'],
            latest['mfi'] > 80
        ]

        # Calculate confidence scores
        buy_confidence = sum([1 if cond else 0 for cond in buy_conditions]) / len(buy_conditions)
        sell_confidence = sum([1 if cond else 0 for cond in sell_conditions]) / len(sell_conditions)
        print(f"Timeframe: {timeframe}, Buy Confidence: {buy_confidence}, Sell Confidence: {sell_confidence}")

        logger.debug(f"Timeframe: {timeframe}, Buy Confidence: {buy_confidence}, Sell Confidence: {sell_confidence}")

        # Apply thresholds to determine signals
        if buy_confidence >= 0.8:  # 80% confidence threshold for buy
            signals[timeframe] = ('buy', buy_confidence)
            buy_signals_count += 1
        elif sell_confidence >= 0.8:  # 80% confidence threshold for sell
            signals[timeframe] = ('sell', sell_confidence)

    # Prioritize "buy" if at least 2 timeframes indicate buy
    if buy_signals_count >= 2:
        logger.info(f"Buy signal triggered based on {buy_signals_count} timeframes.")
        return "buy"

    logger.info("No valid signals found.")
    print(signals)
    print(buy_signals_count)
    # print(top_signal)
    return signals