import ccxt.async_support as ccxt
import asyncio
import logging
import pandas as pd
from config import settings
from trading.strategy import simplified_evaluate_trading_signals
from notifications.telegram_bot import send_telegram_message
from indicators.technical_indicators import calculate_indicators

logger = logging.getLogger(__name__)

# Initialize Binance exchange connection
exchange = ccxt.binance({
    'apiKey': settings.API_KEY,
    'secret': settings.SECRET,
    'enableRateLimit': True,
    'options': {'adjustForTimeDifference': True}
})

async def get_tradeable_pairs(quote_currency):
    try:
        await exchange.load_markets()
        return [symbol for symbol in exchange.symbols if quote_currency in symbol.split('/')]
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

async def fetch_historical_prices(pair, timeframes=['3m', '5m', '15m'], limit=100):
    data = {}
    try:
        for timeframe in timeframes:
            ohlcv = await exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
            if ohlcv is None or len(ohlcv) == 0:
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

async def fetch_order_book(pair, limit=None, params={}):
    try:
        order_book = await exchange.fetch_order_book(pair, limit, params)
        return order_book
    except Exception as e:
        logger.error(f"Error fetching order book for {pair}: {e}")
        return None

def analyze_order_book(order_book):
    bids = order_book['bids']
    asks = order_book['asks']
    
    total_bid_volume = sum([bid[1] for bid in bids])
    total_ask_volume = sum([ask[1] for ask in asks])
    
    bid_ask_spread = asks[0][0] - bids[0][0]
    
    logger.info(f"Total Bid Volume: {total_bid_volume}")
    logger.info(f"Total Ask Volume: {total_ask_volume}")
    logger.info(f"Bid-Ask Spread: {bid_ask_spread}")
    
    return total_bid_volume, total_ask_volume, bid_ask_spread

async def fetch_recent_trades(pair, limit=100):
    try:
        trades = await exchange.fetch_trades(pair, limit=limit)
        return trades
    except Exception as e:
        logger.error(f"Error fetching recent trades for {pair}: {e}")
        return None

def analyze_recent_trades(trades):
    buy_volume = 0
    sell_volume = 0
    
    for trade in trades:
        if trade['side'] == 'buy':
            buy_volume += trade['amount']
        elif trade['side'] == 'sell':
            sell_volume += trade['amount']
    
    logger.info(f"Buy Volume: {buy_volume}")
    logger.info(f"Sell Volume: {sell_volume}")
    
    return buy_volume, sell_volume

def determine_final_signal(order_book, trades, historical_prices):
    total_bid_volume, total_ask_volume, bid_ask_spread = analyze_order_book(order_book)
    buy_volume, sell_volume = analyze_recent_trades(trades)
    historical_prices_signal = simplified_evaluate_trading_signals(historical_prices)
    # Determine the final signal based on all timeframes
    if 'buy' in historical_prices_signal.values():
        final_action = 'buy'
    elif 'sell' in historical_prices_signal.values():
        final_action = 'sell'
    else:
        final_action = None
    
    if total_bid_volume > total_ask_volume and buy_volume > sell_volume and final_action == 'buy':
        return 'buy'
    elif total_ask_volume > total_bid_volume and sell_volume > buy_volume and final_action == 'sell':
        return 'sell'
    else:
        return None

async def get_balance(currency):
    try:
        balance = await exchange.fetch_balance()
        available_balance = balance['free'][currency]
        logger.info(f"Available balance for {currency}: {available_balance}")
        return available_balance
    except Exception as e:
        logger.error(f"Error fetching balance for {currency}: {e}")
        return 0

async def place_market_order(pair, side, amount):
    if amount <= 0:
        logger.error(f"Invalid amount for {side} order: {amount}")
        return None
    try:
        if side == 'buy':
            order = await exchange.create_market_buy_order(pair, amount)
        elif side == 'sell':
            order = await exchange.create_market_sell_order(pair, amount)
        logger.info(f"Market {side} order placed for {pair}: {amount} units at market price.")
        await send_telegram_message(f"Market {side} order placed for {pair}: {amount} units at market price.")
        return order
    except Exception as e:
        logger.error(f"An error occurred placing a {side} order for {pair}: {e}")
        return None

async def convert_to_usdt(pair):
    try:
        asset = pair.split('/')[0]
        asset_balance = await get_balance(asset)
        if asset_balance > 0:
            order_result = await place_market_order(pair, 'sell', asset_balance)
            if order_result:
                logger.info(f"Converted {asset_balance} of {asset} to USDT")
                await send_telegram_message(f"Converted {asset_balance} of {asset} to USDT.")
                return order_result
        else:
            logger.info(f"No {asset} balance to convert to USDT")
    except Exception as e:
        logger.error(f"An error occurred converting {pair} to USDT: {e}")
    return None

async def get_current_price(pair):
    try:
        ticker = await exchange.fetch_ticker(pair)
        current_price = ticker['last']
        logger.info(f"Current market price for {pair}: {current_price}")
        return current_price
    except Exception as e:
        logger.error(f"Error fetching current price for {pair}: {e}")
        return None

async def advanced_trade():
    pairs = await get_tradeable_pairs(settings.quote_currency)
    while True:
        try:
            for pair in pairs:
                logger.info(f"Processing pair: {pair}")

                # Fetch and analyze order book
                order_book = await fetch_order_book(pair)
                if not order_book:
                    continue

                # Fetch and analyze recent trades
                recent_trades = await fetch_recent_trades(pair)
                if not recent_trades:
                    continue

                # Fetch historical prices for multiple timeframes
                historical_prices = await fetch_historical_prices(pair)
                if not historical_prices:
                    continue

                # Determine the final signal
                final_action = determine_final_signal(order_book, recent_trades, historical_prices)
                logger.info(f"Final action for {pair}: {final_action}")

                if final_action:
                    usdt_balance = await get_balance('USDT')
                    if final_action == 'buy' and usdt_balance > settings.initial_investment:
                        amount_to_buy = (usdt_balance * (1 - settings.commission_rate)) / order_book['asks'][0][0]
                        buy_order = await place_market_order(pair, 'buy', amount_to_buy)
                        if buy_order:
                            buy_price = await get_current_price(pair)
                            # Monitor position for stop-loss or take-profit
                            while True:
                                current_price = await get_current_price(pair)
                                if current_price <= buy_price * (1 - settings.stop_loss_percentage):
                                    logger.info(f"Stop-loss triggered for {pair} at {current_price}")
                                    await place_market_order(pair, 'sell', amount_to_buy)
                                    await send_telegram_message(f"Stop-loss triggered for {pair} at {current_price}.")
                                    break
                                elif current_price >= buy_price * (1 + settings.take_profit_percentage):
                                    logger.info(f"Take-profit triggered for {pair} at {current_price}")
                                    await place_market_order(pair, 'sell', amount_to_buy)
                                    await send_telegram_message(f"Take-profit triggered for {pair} at {current_price}.")
                                    break
                                await asyncio.sleep(60)  # Check every minute
                    elif final_action == 'sell':
                        asset = pair.split('/')[0]
                        asset_balance = await get_balance(asset)
                        if asset_balance > 0:
                            await place_market_order(pair, 'sell', asset_balance)
                            await convert_to_usdt(pair)
                            await send_telegram_message(f"The {pair} : Converted in USDT.")
                await asyncio.sleep(1)  # Short delay to prevent hitting rate limits
        except Exception as e:
            logger.error(f"An error occurred during trading: {e}")
            await asyncio.sleep(60)  # Wait for 1 minute before retrying
