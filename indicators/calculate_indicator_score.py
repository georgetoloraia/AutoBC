import logging
from indicators.technical_indicators import calculate_indicators

logger = logging.getLogger(__name__)

def calculate_indicator_score(data):
    """
    Calculate an indicator score for evaluating market conditions.

    Parameters:
        data (dict): A dictionary of dataframes for different timeframes.

    Returns:
        float: A score between -1 and +1 based on market conditions.
    """
    score = 0
    total_weight = 0
    timeframe_to_check = ['3m', '5m', '15m', '1h']

    for timeframe in timeframe_to_check:
        if timeframe not in data:
            logger.info(f"No data available for {timeframe}")
            continue
        df = data[timeframe]
        if df.empty:
            logger.info(f"DataFrame is empty for {timeframe} timeframe.")
            continue

        # Calculate indicators
        df = calculate_indicators(df)
        latest = df.iloc[-1]

        # Define indicator conditions and their weights
        conditions = [
            (latest['close'] < latest['lower_band'], 0.2),  # Price below lower Bollinger Band
            (latest['rsi'] < 30, 0.2),  # RSI below 30 (oversold)
            (latest['macd'] > latest['macd_signal'], 0.2),  # MACD bullish crossover
            (latest['adx'] > 30 and latest['+DI'] > latest['-DI'], 0.2),  # ADX strong trend
            (latest['close'] > latest['vwap'], 0.1),  # Price above VWAP
            (latest['mfi'] < 20, 0.1)  # Money Flow Index indicating oversold
        ]

        # Evaluate conditions and accumulate scores
        for condition, weight in conditions:
            total_weight += weight
            if condition:
                score += weight
            else:
                score -= weight

    # Normalize score to a range of -1 to +1
    if total_weight > 0:
        score /= total_weight

    logger.info(f"Calculated indicator score: {score}")
    return score
