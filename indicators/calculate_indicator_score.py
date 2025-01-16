import logging
from indicators.technical_indicators import calculate_indicators
from config.settings import TIMEFRAMES_FOR_SCORE, INDICATOR_WEIGHTS

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

        # Define conditions and weights dynamically (AFTER latest is defined)
        conditions = [
            (latest['close'] < latest['lower_band'], INDICATOR_WEIGHTS['close < lower_band']),
            (latest['rsi'] < 30, INDICATOR_WEIGHTS['rsi < 30']),
            (latest['macd'] > latest['macd_signal'], INDICATOR_WEIGHTS['macd > macd_signal']),
            (latest['adx'] > 30 and latest['+DI'] > latest['-DI'], INDICATOR_WEIGHTS['adx > 30 and +DI > -DI']),
            (latest['close'] > latest['vwap'], INDICATOR_WEIGHTS['close > vwap']),
            (latest['mfi'] < 20, INDICATOR_WEIGHTS['mfi < 20']),
        ]

        # Evaluate conditions
        for condition, weight in conditions:
            try:
                if condition:  # Direct boolean evaluation
                    score += weight
                else:
                    score -= weight
                total_weight += weight
            except Exception as e:
                logger.error(f"Error evaluating condition in {timeframe}: {e}")
                continue

    # Normalize the score to a range of -1 to +1
    if total_weight > 0:
        score = round(score / total_weight, 2)

    logger.info(f"Calculated indicator score: {score}")
    return score
