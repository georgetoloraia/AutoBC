import ccxt.async_support as ccxt
import asyncio
import logging
import pandas as pd
from config import settings
from trading.strategy import simplified_evaluate_trading_signals
from notifications.telegram_bot import send_telegram_message
from indicators.technical_indicators import calculate_indicators

import json

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

async def fetch_historical_prices(pair, timeframes=['1m', '5m', '1h', '1d'], limit=1000):
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
    bids = order_book.get('bids', [])
    asks = order_book.get('asks', [])
    
    if not bids or not asks:
        logger.info("Order book is empty.")
        return 0, 0, 0
    
    total_bid_volume = sum([bid[1] for bid in bids])
    total_ask_volume = sum([ask[1] for ask in asks])
    
    bid_ask_spread = asks[0][0] - bids[0][0] if bids and asks else 0
    
    # logger.info(f"Order Book Analysis - Total Bid Volume: {total_bid_volume}, Total Ask Volume: {total_ask_volume}, Bid-Ask Spread: {bid_ask_spread}")
    
    return total_bid_volume, total_ask_volume, bid_ask_spread

async def fetch_recent_trades(pair, limit=1000):
    try:
        trades = await exchange.fetch_trades(pair, limit=limit)
        return trades
    except Exception as e:
        logger.error(f"Error fetching recent trades for {pair}: {e}")
        return None

def analyze_recent_trades(trades):
    buy_volume = 0
    sell_volume = 0
    
    if not trades:
        logger.info("Recent trades list is empty.")
        return buy_volume, sell_volume
    
    for trade in trades:
        if trade['side'] == 'buy':
            buy_volume += trade['amount']
        elif trade['side'] == 'sell':
            sell_volume += trade['amount']
    
    logger.info(f"Recent Trades Analysis - Buy Volume: {buy_volume}, Sell Volume: {sell_volume}")
    
    return buy_volume, sell_volume

def determine_final_signal(order_book, trades, historical_prices):
    try:
        total_bid_volume, total_ask_volume, bid_ask_spread = analyze_order_book(order_book)
    except Exception as e:
        logger.error(f"Error analyzing order book: {e}")
        total_bid_volume, total_ask_volume, bid_ask_spread = 0, 0, 0

    try:
        buy_volume, sell_volume = analyze_recent_trades(trades)
    except Exception as e:
        logger.error(f"Error analyzing recent trades: {e}")
        buy_volume, sell_volume = 0, 0

    try:
        historical_prices_signal = simplified_evaluate_trading_signals(historical_prices)
    except Exception as e:
        logger.error(f"Error evaluating historical prices: {e}")
        historical_prices_signal = {}

    # Determine the final signal based on all timeframes
    final_actions = []
    confidence_scores = []
    for timeframe, (action, confidence) in historical_prices_signal.items():
        final_actions.append(action)
        confidence_scores.append(confidence)

    # Use the most frequent action as the final action
    final_action = max(set(final_actions), key=final_actions.count) if final_actions else None
    final_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    # print(f"\nfin***all**\n{confidence_scores}\nfinall***")

    # logger.info(f"Order Book - Total Bid Volume: {total_bid_volume}, Total Ask Volume: {total_ask_volume}, Bid-Ask Spread: {bid_ask_spread}")
    # logger.info(f"Recent Trades - Buy Volume: {buy_volume}, Sell Volume: {sell_volume}")
    # logger.info(f"Historical Prices Signal: {historical_prices_signal}")
    # logger.info(f"Final Action before confirmation: {final_action}, Confidence: {final_confidence}")

    # Calculate the percentage of bid volume over total volume
    bid_ratio = total_bid_volume / (total_bid_volume + total_ask_volume) if (total_bid_volume + total_ask_volume) > 0 else 0
    # Calculate the percentage of buy volume over total trade volume
    buy_ratio = buy_volume / (buy_volume + sell_volume) if (buy_volume + sell_volume) > 0 else 0

    # logger.info(f"========\n\
    #             bid_ratio: {bid_ratio}\n\
    #             buy_ratio: {buy_ratio}\n\
    #             final_action: {final_action}\n\
    #             final_confidence: {final_confidence}\n\
    #             ==========")

    # Check if more than 55% of the volume are bids and buys respectively
    if bid_ratio > 0.65 or buy_ratio > 0.65 and final_action == 'buy' and final_confidence < 0.5:
        logger.info("Final decision: BUY - bid and buy volumes are both above 55%")
        return 'buy'
    elif bid_ratio < 0.3 and buy_ratio < 0.3 and final_action == 'sell': #and final_confidence > 0.75:
        logger.info("Final decision: SELL - ask and sell volumes are both above 70%")
        return 'sell'
    else:
        logger.info("Final decision: NONE - conditions not met for either buy or sell")
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
    current_price = await get_current_price(pair)
    needPrice = current_price * (1 + settings.take_profit_percentage)
    if amount <= 0:
        logger.error(f"Invalid amount for {side} order: {amount}")
        return None
    try:
        if side == 'buy':
            order = await exchange.create_market_buy_order(pair, amount)
        elif side == 'sell':
            order = await exchange.create_market_sell_order(pair, amount)
        logger.info(f"Market {side} order placed for {pair}: {amount} units at market price.")
        await send_telegram_message(f"Market {side} order placed for {pair}: {amount} units at market price.\ncurrent: {current_price}\nneed: {needPrice}")
        return order
    except Exception as e:
        logger.error(f"An error occurred placing a {side} order for {pair}: {e}")
        await send_telegram_message(f"An error occurred placing a {side} order for {pair}: {e}")
        return None

async def convert_to_usdt(pair):
    try:
        asset = pair.split('/')[0]
        asset_balance = await get_balance(asset)
        if asset_balance > 0:
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
                order_result = await place_market_order(pair, 'sell', asset_balance)
                if order_result:
                    await send_telegram_message(f"Sold {asset_balance} of {asset} manually. Converting to USDT.")
                    await asyncio.sleep(2)
                    return await convert_to_usdt(pair)
        else:
            logger.info(f"No {asset} balance to convert to USDT")
    except Exception as e:
        logger.error(f"An error occurred converting {pair} to USDT: {e}")
    return None

async def get_desired_tradeable_pairs():
    try:
        await exchange.load_markets()
        return [symbol for symbol in settings.DESIRED_COINS if symbol in exchange.symbols]
    except Exception as e:
        logger.error(f"Error loading markets: {e}")
        return []

async def get_current_price(pair, retries=100, delay=10):
    for attempt in range(retries):
        try:
            ticker = await exchange.fetch_ticker(pair)
            current_price = ticker['last']
            # logger.info(f"Current market price for {pair}: {current_price}")
            return current_price
        except Exception as e:
            logger.error(f"Error fetching current price for {pair}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                return None

async def advanced_trade():
    if settings.quote_currency:
        quote_currency = 'USDT'
        pairs = await get_tradeable_pairs(quote_currency)
    else:
        pairs = await get_desired_tradeable_pairs()
    while True:
        try:
            for pair in pairs:
                logger.info(f"\n= = = = = = = =\n")
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
                        amount_to_buy = (usdt_balance * (1 - settings.commission_rate)) / order_book['asks'][0][0] if order_book['asks'] else 0
                        if amount_to_buy <= 0:
                            logger.error("Calculated amount to buy is zero or negative.")
                            continue
                        logger.info(f"Available USDT balance: {usdt_balance}")
                        print(f"amount_to_buy = {amount_to_buy} $")

                        # Check if the calculated amount meets Binance's minimum notional value
                        current_price = await get_current_price(pair)
                        first_price = current_price

                        try:
                            # Place the buy order
                            buy_order = await place_market_order(pair, 'buy', amount_to_buy)
                            if buy_order:
                                buy_price = await get_current_price(pair)
                                logger.info(f"Buy order placed for {pair} at {buy_price}")

                                # Monitor position for take-profit
                                while True:
                                    try:
                                        current_price = await get_current_price(pair)
                                        
                                        if current_price is None:
                                            logger.error("Failed to fetch current price during monitoring.")
                                            await asyncio.sleep(10)  # Retry after a short delay
                                            continue
                                        
                                        # Check if take-profit condition is met
                                        if current_price >= buy_price * (1 + settings.take_profit_percentage):
                                            logger.info(f"Take-profit triggered for {pair} at {current_price}")

                                            asset = pair.split('/')[0]  # Extract the base currency (e.g., BTC in BTC/USDT)
                                            asset_balance = await get_balance(asset)

                                            if asset_balance > 0:
                                                try:
                                                    # If the pair ends in USDT, sell directly
                                                    if pair.endswith('/USDT'):
                                                        logger.info(f"Direct pair {pair} available. Selling directly...")
                                                        sell_order = await place_market_order(pair, 'sell', asset_balance)
                                                        if sell_order:
                                                            logger.info(f"Successfully sold {asset_balance} of {asset} at {current_price}.")
                                                            await send_telegram_message(f"Sold {asset_balance} of {asset} at {current_price}.")
                                                    else:
                                                        # If no direct pair is available, convert to USDT
                                                        logger.info(f"Direct pair {pair} unavailable. Converting {asset} to USDT...")
                                                        conversion_result = await convert_to_usdt(pair)
                                                        if conversion_result:
                                                            logger.info(f"Successfully converted {asset_balance} of {asset} to USDT.")
                                                            await send_telegram_message(f"Converted {asset_balance} of {asset} to USDT.")
                                                        else:
                                                            logger.error(f"Failed to convert {asset} to USDT.")
                                                            await send_telegram_message(f"Conversion of {asset_balance} of {asset} to USDT failed.")
                                                except Exception as e:
                                                    logger.error(f"An error occurred while processing sell/conversion for {pair}: {e}")
                                                    await send_telegram_message(f"An error occurred while processing sell/conversion for {pair}: {e}")
                                            else:
                                                logger.error(f"Insufficient balance of {asset} to sell or convert.")
                                                await send_telegram_message(f"Insufficient balance of {asset} to sell or convert.")

                                            break  # Exit the monitoring loop after processing the sell

                                        counted = current_price - first_price
                                        print(f"Progress: {counted} $")
                                        
                                        # Log the current status
                                        logger.info(f"Monitoring {pair}: Current price {current_price}, Target price {buy_price * (1 + settings.take_profit_percentage)}")
                                        await asyncio.sleep(60)  # Check every minute
                                    except Exception as e:
                                        logger.error(f"An error occurred during price monitoring for {pair}: {e}")
                                        await asyncio.sleep(10)  # Retry after a short delay
                        except Exception as e:
                            logger.error(f"An error occurred placing a buy order for {pair}: {e}")
                            await send_telegram_message(f"Failed to place a buy order for {pair}: {e}")

                        await asyncio.sleep(2)  # Short delay to prevent hitting rate limits
        except Exception as e:
            logger.error(f"An error occurred during trading: {e}")
            await asyncio.sleep(60)  # Wait for 1 minute before retrying






# async def advanced_trade():
#     # pairs = await get_tradeable_pairs(settings.quote_currency)
#     if settings.quote_currency:
#         quote_currency = 'USDT'
#         pairs = await get_tradeable_pairs(quote_currency)
#     else:
#         pairs = await get_desired_tradeable_pairs()
#     while True:
#         try:
#             for pair in pairs:
#                 logger.info(f"\n= = = = = = = =\n")
#                 logger.info(f"Processing pair: {pair}")

#                 # Fetch and analyze order book
#                 order_book = await fetch_order_book(pair)
#                 if not order_book:
#                     continue

#                 # Fetch and analyze recent trades
#                 recent_trades = await fetch_recent_trades(pair)
#                 if not recent_trades:
#                     continue

#                 # Fetch historical prices for multiple timeframes
#                 historical_prices = await fetch_historical_prices(pair)
#                 if not historical_prices:
#                     continue

#                 # Determine the final signal
#                 final_action = determine_final_signal(order_book, recent_trades, historical_prices)
#                 logger.info(f"Final action for {pair}: {final_action}")

#                 if final_action:
#                     usdt_balance = await get_balance('USDT')
#                     if final_action == 'buy' and usdt_balance > settings.initial_investment:
#                         amount_to_buy = (usdt_balance * (1 - settings.commission_rate)) / order_book['asks'][0][0] if order_book['asks'] else 0
#                         if amount_to_buy <= 0:
#                             logger.error("Calculated amount to buy is zero or negative.")
#                             continue
                        
#                         # Ensure the amount to buy meets the minimum notional value
#                         minimum_notional = 5  # Set this to the exchange's minimum notional value (e.g., $5)
#                         if amount_to_buy * order_book['asks'][0][0] < minimum_notional:
#                             logger.error(f"Order value {amount_to_buy * order_book['asks'][0][0]} is below the minimum notional value {minimum_notional}.")
#                             continue
                        
#                         buy_order = await place_market_order(pair, 'buy', amount_to_buy)
#                         if buy_order:
#                             buy_price = await get_current_price(pair)
#                             # need_sell = buy_price * (1 - settings.stop_loss_percentage)
#                             # Monitor position for stop-loss or take-profit
#                             while True:
#                                 current_price = await get_current_price(pair)
#                                 if current_price is None:
#                                     logger.error("Failed to fetch current price during monitoring.")
#                                     break
#                                 # if current_price <= need_sell: #buy_price * (1 - settings.stop_loss_percentage):
#                                 #     logger.info(f"Stop-loss triggered for {pair} at {current_price}")
#                                 #     await convert_to_usdt(pair)
#                                 #     await send_telegram_message(f"Stop-loss triggered for {pair} at {current_price}.")
#                                 #     break
#                                 elif current_price >= buy_price * (1 + settings.take_profit_percentage):
#                                     needPrice = buy_price * (1 + settings.take_profit_percentage)
#                                     logger.info(f"Take-profit triggered for {pair} at {current_price}")
#                                     await convert_to_usdt(pair)
#                                     await send_telegram_message(f"BUY: {pair} at {current_price}.\nBuy-price: {buy_price}\nNeedPrice: {needPrice}")
#                                     break
#                                 # if current_price > buy_price:
#                                 #     buy_price = current_price
#                                 #     need_sell = round(need_sell - 0.001)

#                                 logger.info(f"Current market price for {pair}: {current_price} || Buy price is: {buy_price}")
                                    
#                                 await asyncio.sleep(60)  # Check every minute
#                     elif final_action == 'sell':
#                         asset = pair.split('/')[0]
#                         asset_balance = await get_balance(asset)
#                         if asset_balance > 1:
#                             # await place_market_order(pair, 'sell', asset_balance)
#                             await convert_to_usdt(pair)
#                             await send_telegram_message(f"The {pair} : Converted in USDT.")
#                 await asyncio.sleep(1)  # Short delay to prevent hitting rate limits
#         except Exception as e:
#             logger.error(f"An error occurred during trading: {e}")
#             await asyncio.sleep(60)  # Wait for 1 minute before retrying
