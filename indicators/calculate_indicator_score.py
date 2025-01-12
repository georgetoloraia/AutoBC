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
    timeframe_to_check = ['1m', '3m', '5m', '15m']

    # Define indicator conditions and their weights
    indicator_conditions = [
        ("close < lower_band", 0.2),  # Price below lower Bollinger Band
        ("rsi < 30", 0.2),  # RSI below 30 (oversold)
        ("macd > macd_signal", 0.2),  # MACD bullish crossover
        ("adx > 30 and +DI > -DI", 0.2),  # ADX strong trend
        ("close > vwap", 0.1),  # Price above VWAP
        ("mfi < 20", 0.1)  # Money Flow Index indicating oversold
    ]

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

        # Evaluate each condition
        for condition, weight in indicator_conditions:
            try:
                condition_met = eval(condition, None, latest.to_dict())
            except Exception as e:
                logger.error(f"Error evaluating condition '{condition}' for {timeframe}: {e}")
                continue

            total_weight += weight
            if condition_met:
                score += weight
            else:
                score -= weight

    # Normalize score to a range of -1 to +1
    if total_weight > 0:
        score /= total_weight

    logger.info(f"Calculated indicator score: {score:.2f}")
    return score
