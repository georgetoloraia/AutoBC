import logging
from indicators.technical_indicators import calculate_indicators
from config.settings import TIMEFRAMES_FOR_SCORE

logger = logging.getLogger(__name__)

def calculate_indicator_score(data):
    """
    Calculate an aggregated indicator score for evaluating market conditions.

    Parameters:
        data (dict): A dictionary where keys are timeframes (e.g., '3m', '5m') and values are pandas DataFrames
                     with OHLCV data.

    Returns:
        float: A normalized score between -1 (strongly bearish) and +1 (strongly bullish).
    """
    score = 0
    total_weight = 0

    # Define conditions and weights
    conditions = [
        ("close < lower_band", 0.2),  # Price below lower Bollinger Band
        ("rsi < 30", 0.2),  # RSI below 30 (oversold)
        ("macd > macd_signal", 0.2),  # MACD bullish crossover
        ("adx > 30 and +DI > -DI", 0.2),  # Strong ADX trend
        ("close > vwap", 0.1),  # Price above VWAP
        ("mfi < 20", 0.1)  # Money Flow Index indicating oversold
    ]

    for timeframe in TIMEFRAMES_FOR_SCORE:
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

        # Evaluate conditions
        for condition, weight in conditions:
            try:
                # Use eval to dynamically evaluate the condition
                condition_met = eval(condition, None, latest.to_dict())
            except Exception as e:
                logger.error(f"Error evaluating condition '{condition}' for {timeframe}: {e}")
                continue

            # Adjust score based on condition result
            total_weight += weight
            if condition_met:
                score += weight
            else:
                score -= weight

    # Normalize the score to a range of -1 to +1
    if total_weight > 0:
        score = round(score / total_weight, 2)

    logger.info(f"Calculated indicator score: {score}")
    return score
