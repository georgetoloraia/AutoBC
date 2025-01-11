import ccxt.async_support as ccxt
import asyncio
import logging
import pandas as pd
import time
from config import settings
from trading.strategy import simplified_evaluate_trading_signals
from notifications.telegram_bot import send_telegram_message
from indicators.technical_indicators import calculate_indicators
from indicators.calculate_indicator_score import calculate_indicator_score

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Initialize Binance exchange connection
exchange = ccxt.binance({
    'apiKey': settings.API_KEY,
    'secret': settings.SECRET,
    'enableRateLimit': True,
    'options': {'adjustForTimeDifference': True}
})

# Cache for balance
balance_cache = {}

async def get_tradeable_pairs(quote_currency):
    try:
        await exchange.load_markets()
        tradeable_pairs = [symbol for symbol in exchange.symbols if quote_currency in symbol.split('/')]
        return tradeable_pairs
    except Exception as e:
        logger.error(f"Error loading markets: {e}")
        return []

async def close_exchange():
    if hasattr(exchange, 'close'):
        await exchange.close()

def preprocess_data(df):
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("DataFrame must contain open, high, low, close, and volume columns")
    df = df.ffill().bfill()
    return df

async def fetch_historical_prices(pair, timeframes=['3m', '5m', '15m', '1h'], limit=1000):
    data = {}
    try:
        for timeframe in timeframes:
            ohlcv = await exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
            if not ohlcv:
                logger.info(f"No data returned for {pair} in {timeframe} timeframe.")
                continue
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = preprocess_data(df)
            df = calculate_indicators(df)
            data[timeframe] = df
        return data
    except Exception as e:
        logger.error(f"Error fetching historical prices for {pair}: {e}")
        return data

async def rate_limited_fetch(func, *args, **kwargs):
    """
    Wrapper for API calls to handle rate limits.
    """
    try:
        return await func(*args, **kwargs)
    except ccxt.RateLimitExceeded as e:
        logger.warning("Rate limit exceeded. Sleeping for 1 minute.")
        await asyncio.sleep(60)
        return await func(*args, **kwargs)

async def fetch_order_book(pair):
    return await rate_limited_fetch(exchange.fetch_order_book, pair)

async def fetch_recent_trades(pair, limit=100):
    return await rate_limited_fetch(exchange.fetch_trades, pair, limit=limit)

async def get_balance(currency):
    """
    Fetch balance with caching to reduce API calls.
    """
    cache_duration = 60  # Cache for 1 minute
    if currency in balance_cache:
        cached_balance, timestamp = balance_cache[currency]
        if (time.time() - timestamp) < cache_duration:
            return cached_balance

    try:
        balance = await exchange.fetch_balance()
        available_balance = balance['free'][currency]
        balance_cache[currency] = (available_balance, time.time())
        logger.info(f"Available balance for {currency}: {available_balance}")
        return available_balance
    except Exception as e:
        logger.error(f"Error fetching balance for {currency}: {e}")
        return 0

async def place_market_order(pair, side, amount):
    """
    Place a market order.
    """
    try:
        if amount <= 0:
            logger.error(f"Invalid amount for {side} order: {amount}")
            return None
        if side == 'buy':
            order = await exchange.create_market_buy_order(pair, amount)
        elif side == 'sell':
            order = await exchange.create_market_sell_order(pair, amount)
        logger.info(f"Market {side} order placed for {pair}: {amount} units.")
        await send_telegram_message(f"Market {side} order placed for {pair}: {amount} units.")
        return order
    except Exception as e:
        logger.error(f"Error placing {side} order for {pair}: {e}")
        await send_telegram_message(f"Error placing {side} order for {pair}: {e}")
        return None

async def advanced_trade():
    """
    Main trading loop with dynamic profit-taking logic.
    """
    if settings.quote_currency:
        quote_currency = 'USDT'
        pairs = await get_tradeable_pairs(quote_currency)
    else:
        pairs = settings.DESIRED_COINS

    while True:
        try:
            for pair in pairs:
                logger.info(f"Processing pair: {pair}")

                # Fetch and preprocess market data
                historical_prices = await fetch_historical_prices(pair)
                if not historical_prices:
                    continue

                order_book = await fetch_order_book(pair)
                if not order_book:
                    continue

                # Evaluate trading signals
                trading_signals = simplified_evaluate_trading_signals(historical_prices)
                logger.info(f"Trading signals for {pair}: {trading_signals}")

                # Initialize dynamic profit-taking parameters
                profit_percentage = settings.TAKE_PROFIT_PERCENTAGE
                profit_step = 0.005  # Increment profit by 1% on positive signals
                max_profit_percentage = 0.30  # Cap at 20% profit
                stop_loss_buffer = 0.02  # Adjust stop-loss to 2% below current price
                buy_price = None  # Track the price at which the asset was bought

                if 'buy' in trading_signals.values():
                    usdt_balance = await get_balance('USDT')
                    amount_to_buy = usdt_balance / order_book['asks'][0][0]
                    buy_order = await place_market_order(pair, 'buy', amount_to_buy)

                    if buy_order:
                        buy_price = order_book['asks'][0][0]  # Record buy price
                        logger.info(f"Bought {pair} at {buy_price}")
                        start_time = 0

                        while True:
                            start_time += 1
                            current_price = await rate_limited_fetch(exchange.fetch_ticker, pair)
                            current_price = current_price['last']

                            # profit += Logic
                            if start_time % 15 == 0:
                                historical_prices = await fetch_historical_prices(pair)
                                if not historical_prices:
                                    logger.warning("Failed to refresh historical prices.")
                                    continue
                                logger.info("Historical prices refreshed.")

                            # Calculate indicator score
                            score = calculate_indicator_score(historical_prices)
                            logger.info(f"Indicator score for {pair}: {score:.2f}")

                            profit_percentage += score * profit_step
                            profit_percentage = min(max(profit_percentage, 0.01), max_profit_percentage)  # Clamp between 1% and 20%

                            # Calculate take-profit and stop-loss prices
                            take_profit_price = buy_price * (1 + profit_percentage)
                            stop_loss_price = current_price * (1 - stop_loss_buffer)

                            logger.info(f"Current Price: {current_price}")
                            logger.info(f"Take-Profit Price: {take_profit_price}")
                            logger.info(f"Stop-Loss Price: {stop_loss_price}\n")


                            if current_price >= take_profit_price:
                                logger.info(f"Take-Profit triggered! Selling at {current_price}")
                                await place_market_order(pair, 'sell', amount_to_buy)
                                break
                            elif current_price <= stop_loss_price:
                                logger.info(f"Stop-Loss triggered! Selling at {current_price}")
                                await place_market_order(pair, 'sell', amount_to_buy)
                                break

                            await asyncio.sleep(30)

                elif 'sell' in trading_signals.values():
                    asset = pair.split('/')[0]
                    asset_balance = await get_balance(asset)
                    await place_market_order(pair, 'sell', asset_balance)
                    logger.info(f"Sold {pair}")

                await asyncio.sleep(2)

            await asyncio.sleep(90)
        except Exception as e:
            logger.error(f"An error occurred during trading: {e}")
            await asyncio.sleep(60)
