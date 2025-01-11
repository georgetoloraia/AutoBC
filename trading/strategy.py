import logging
from indicators.technical_indicators import calculate_indicators

logger = logging.getLogger(__name__)

def simplified_evaluate_trading_signals(data):
    signals = {}
    timeframe_to_check = ['1m', '3m', '5m', '15m']

    buy_signals_count = 0

    # for timeframe, df in data.items():
    for timeframe in timeframe_to_check:
        if timeframe not in data:
            logger.info(f"No data available for {timeframe}")
            continue
        df = data[timeframe]
        if df.empty:
            logger.info(f"DataFrame is empty for {timeframe} timeframe.")
            continue

        df = calculate_indicators(df)
        latest = df.iloc[-1]

        # Buy conditions
        buy_conditions = [
            latest['close'] < latest['lower_band'],  # Price below lower Bollinger Band
            latest['rsi'] < 30,  # RSI below 35
            latest['macd'] > latest['macd_signal'],  # MACD bullish crossover
            latest['adx'] > 30 and latest['+DI'] > latest['-DI'],  # ADX indicating strong trend
            latest['close'] > latest['vwap'],  # Price above VWAP
            latest['mfi'] < 20  # Money Flow Index indicating oversold
        ]

        # Sell conditions
        sell_conditions = [
            latest['close'] > latest['upper_band'],  # Price above upper Bollinger Band
            latest['rsi'] > 70,  # RSI above 70
            latest['macd'] < latest['macd_signal'],  # MACD bearish crossover
            latest['adx'] > 25 and latest['-DI'] > latest['+DI'],  # ADX indicating strong trend
            latest['close'] < latest['vwap'],  # Price below VWAP
            latest['mfi'] > 80  # Money Flow Index indicating overbought
        ]

        buy_confidence = sum([1 if cond else 0 for cond in buy_conditions]) / len(buy_conditions)
        sell_confidence = sum([1 if cond else 0 for cond in sell_conditions]) / len(sell_conditions)

        # logger.info(f"\n* * * * * * *\nbuy_condintions: {buy_conditions}\nbuy_confidence: {buy_confidence}\n* * * * * * * * * \n")

        if buy_confidence >= 0.8 and latest['mfi'] < 20 and latest['rsi'] < 30:
            logger.info(f"Simplified Buy signal conditions met in {timeframe} timeframe.")
            # signals[timeframe] = ('buy', buy_confidence)
            buy_signals_count += 1
        elif all(sell_conditions):
            logger.info(f"Simplified Sell signal conditions met in {timeframe} timeframe.")
            signals[timeframe] = ('sell', sell_confidence)

    if buy_signals_count >= 2:
        for tf in signals:
            if tf in signals and signals[tf][0] == 'sell':
                continue
        signals[timeframe] = ('buy', buy_confidence)

    return signals
