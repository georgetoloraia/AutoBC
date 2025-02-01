import ccxt.async_support as ccxt
import asyncio
import logging
import pandas as pd
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

async def fetch_historical_prices(pair, timeframes=settings.TIMEFRAMES, limit=1000, save_to_csv=True):
    """
    Fetch historical OHLCV data for a trading pair and save it to a CSV file.

    Parameters:
        pair (str): Trading pair (e.g., 'BTC/USDT').
        timeframes (list): List of timeframes to fetch data for.
        limit (int): Number of data points to fetch per timeframe.
        save_to_csv (bool): Whether to save the data to a CSV file.

    Returns:
        dict: A dictionary where keys are timeframes and values are DataFrames.
    """
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
            # Save data to CSV if enabled
            if save_to_csv:
                filename = f"{pair.replace('/', '_')}_{timeframe}_historical_data.csv"
                df.to_csv(filename)
                logger.info(f"Saved historical data for {pair} ({timeframe}) to {filename}")
            data[timeframe] = df
        return data
    except Exception as e:
        logger.error(f"Error fetching historical prices for {pair}: {e}")
        return data
    
async def fetch_historical_prices_for_score(pair, timeframes=settings.TIMEFRAMES_FOR_SCORE, limit=1000):
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

async def fetch_order_book(pair):
    try:
        return await exchange.fetch_order_book(pair)
    except Exception as e:
        logger.error(f"Error fetching order book for {pair}: {e}")
        return None

async def get_balance(currency):
    """
    Fetch balance with caching to reduce API calls.
    """
    cache_duration = 60  # Cache for 1 minute
    if currency in balance_cache:
        cached_balance, timestamp = balance_cache[currency]
        if (pd.Timestamp.now() - timestamp).seconds < cache_duration:
            return cached_balance

    try:
        balance = await exchange.fetch_balance()
        available_balance = balance['free'][currency]
        balance_cache[currency] = (available_balance, pd.Timestamp.now())
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
    
async def convert_to_usdt(pair):
    try:
        asset = pair.split('/')[0]
        asset_balance = await get_balance(asset)
        if asset_balance > 0:
            # Check if the exchange supports direct conversion to USDT
            conversion_pair = f"{asset}/USDT"
            market = await exchange.fetch_ticker(conversion_pair)
            if market:
                order_result = await place_market_order(conversion_pair, 'sell', asset_balance)
                if order_result:
                    logger.info(f"Converted {asset_balance} of {asset} to USDT")
                    await send_telegram_message(f"Converted {asset_balance} of {asset} to USDT.")
                    return order_result
            else:
                logger.info(f"Direct conversion pair {conversion_pair} not available. Selling manually.")
                # If direct conversion is not available, sell the asset first
                order_result = await place_market_order(pair, 'sell', asset_balance)
                if order_result:
                    await send_telegram_message(f"Sold {asset_balance} of {asset} manually. Converting to USDT.")
                    await asyncio.sleep(2)  # Allow some time for the market to update
                    return await convert_to_usdt(pair)
        else:
            logger.info(f"No {asset} balance to convert to USDT")
    except Exception as e:
        logger.error(f"An error occurred converting {pair} to USDT: {e}")
    return None

async def rate_limited_fetch(func, *args, **kwargs):
    """
    Wrapper to handle rate limits gracefully for exchange API calls.
    """
    try:
        return await func(*args, **kwargs)
    except ccxt.RateLimitExceeded as e:
        logger.warning("Rate limit exceeded. Sleeping for 1 minute.")
        await asyncio.sleep(60)
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"API request failed: {e}")
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
                trading_signal = simplified_evaluate_trading_signals(historical_prices, order_book)
                logger.info(f"Trading signal for {pair}: {trading_signal}")

                if trading_signal == "buy":
                    usdt_balance = await get_balance('USDT')
                    amount_to_buy = usdt_balance / historical_prices['1m']['close'].iloc[-1]
                    buy_order = await place_market_order(pair, 'buy', amount_to_buy)

                    if buy_order:
                        buy_price = historical_prices['1m']['close'].iloc[-1]
                        higest_price = buy_price
                        base_stop_loss = buy_price * (1 - stop_loss_buffer)
                        logger.info(f"Bought {pair} at {buy_price}")

                        # Dynamic profit-taking loop
                        profit_percentage = settings.TAKE_PROFIT_PERCENTAGE
                        profit_step = settings.PROFIT_STEP
                        max_profit_percentage = settings.MAX_PROFIT_PERCENTAGE
                        stop_loss_buffer = settings.STOP_LOSS_PERCENTAGE

                        score_time = 0

                        while True:
                            try:
                                # Fetch the latest current price
                                ticker = await rate_limited_fetch(exchange.fetch_ticker, pair)
                                current_price = ticker['last']  # Get the latest price from the ticker data

                                #Update higest price observed
                                higest_price = max(higest_price, current_price)

                                #update stop-loss as trailing value
                                trailing_stop_loss = higest_price * (1 - stop_loss_buffer)
                                dynamic_stop_loss = max(trailing_stop_loss, base_stop_loss)

                                if score_time % 7 == 0:
                                    historical_prices = await fetch_historical_prices_for_score(pair)
                                    if historical_prices:
                                    
                                        profit_percentage += calculate_indicator_score(historical_prices) * profit_step
                                        profit_percentage = min(profit_percentage, max_profit_percentage)

                                take_profit_price = buy_price * (1 + profit_percentage)
                                    # stop_loss_price = buy_price * (1 - stop_loss_buffer)

                                # logger.info(f"Current Price: {current_price:.2f}, Take-Profit: {take_profit_price:.2f}, Stop-Loss: {stop_loss_price:.2f}")
                                logger.info(
                                    f"Price: {current_price:.2f} | "
                                    f"Take-Profit: {take_profit_price:.2f} | "
                                    f"Trailing Stop: {dynamic_stop_loss:.2f}"
                                )


                                # Check if price hits take-profit or stop-loss levels
                                if current_price >= take_profit_price:
                                    logger.info(f"Take-Profit triggered! Selling at {current_price}")
                                    selling = await place_market_order(pair, 'sell', amount_to_buy)
                                    if not selling:
                                        await convert_to_usdt(pair)
                                    break
                                elif current_price <= dynamic_stop_loss:
                                    logger.info(f"Stop-Loss triggered! Selling at {current_price}")
                                    stopping = await place_market_order(pair, 'sell', amount_to_buy)
                                    if not stopping:
                                        await convert_to_usdt(pair)
                                    break
                                
                                # Wait before the next iteration
                                await asyncio.sleep(20)
                                score_time += 1

                            except Exception as e:
                                logger.error(f"Error fetching current price or processing trade logic: {e}")
                                await asyncio.sleep(20)  # Retry after a short delay
                        await asyncio.sleep(2)

                # elif 'sell' in trading_signals.values():
                #     continue
                    # asset = pair.split('/')[0]
                    # asset_balance = await get_balance(asset)
                    # await place_market_order(pair, 'sell', asset_balance)
                    # logger.info(f"Sold {pair}")

                    await asyncio.sleep(1)

                await asyncio.sleep(5)

            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"An error occurred during trading: {e}")
            await asyncio.sleep(10)
