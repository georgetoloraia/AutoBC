import pandas as pd
import numpy as np
import logging
from datetime import timedelta
from indicators.technical_indicators import calculate_indicators
from trading.strategy import define_short_term_strategy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, historical_data, initial_balance=1000):
        """
        Initialize the backtester.

        Parameters:
            historical_data (pd.DataFrame): DataFrame containing OHLCV data.
            initial_balance (float): Initial USDT balance for backtesting.
        """
        self.historical_data = historical_data
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = None  # Current position (None, 'buy', or 'sell')
        self.entry_price = None  # Price at which the position was opened
        self.trades = []  # List to store trade history

    def run_backtest(self):
        """
        Run the backtest on the historical data.
        """
        logger.info("Starting backtest...")

        for i in range(len(self.historical_data)):
            current_data = self.historical_data.iloc[:i+1]  # Data up to the current timestamp
            current_row = self.historical_data.iloc[i]

            # Evaluate trading signals
            signal = self.evaluate_signals(current_data)

            # Execute buy or sell based on the signal
            if signal == "buy" and self.position is None:
                self.execute_buy(current_row)
            if self.position == "buy" and (current_row['close'] - self.entry_price) / self.entry_price >= 0.01:
                # Sell when the profit target (5%) is met
                self.execute_sell(current_row)

        logger.info("Backtest completed.")
        self.generate_report()


    def execute_buy(self, row):
        """
        Execute a buy order.

        Parameters:
            row (pd.Series): Current row of historical data.
        """
        if self.balance <= 0:
            logger.warning("Insufficient balance to buy.")
            return
        self.position = "buy"
        self.entry_price = row['close']
        self.balance = 0  # Assume we use the entire balance for simplicity
        logger.info(f"Buy order executed at {row['close']}")

    def execute_sell(self, row):
        """
        Execute a sell order.
    
        Parameters:
            row (pd.Series): Current row of historical data.
        """
        if self.position != "buy":
            logger.warning("No open position to sell.")
            return
        exit_price = row['close']
        profit = (exit_price - self.entry_price) / self.entry_price * self.initial_balance
        self.balance = self.initial_balance + profit
        self.trades.append({
            'entry_price': self.entry_price,
            'exit_price': exit_price,
            'profit': profit
        })
        self.position = None
        logger.info(f"Sell order executed at {exit_price}. Profit: {profit:.2f}")


    def evaluate_signals(self, data):
        """
        Evaluate trading signals based on the strategy.s

        Parameters:
            data (pd.DataFrame): Historical data up to the current timestamp.

        Returns:
            str: "buy", "sell", or None.
        """
        # Ensure enough data points for indicators
        if len(data) < 4:
            return None

        # Calculate indicators (you can reuse your existing functions)
        data = calculate_indicators(data)

        # Evaluate buy/sell signals
        buy_signal = define_short_term_strategy(data, mode="buy")
        # sell_signal = define_short_term_strategy(data, mode="sell")
        # sell_signall = execute_sell()

        if buy_signal:
            return "buy"
        # elif sell_signal:
        #     return "sell"
        else:
            return None


    def generate_report(self):
        """
        Generate a backtest report with key metrics.
        """
        total_trades = len(self.trades)
        winning_trades = len([trade for trade in self.trades if trade['profit'] > 0])
        losing_trades = total_trades - winning_trades
        total_profit = sum(trade['profit'] for trade in self.trades)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        logger.info("\n=== Backtest Report ===")
        logger.info(f"Initial Balance: {self.initial_balance:.2f} USDT")
        logger.info(f"Final Balance: {self.balance:.2f} USDT")
        logger.info(f"Total Profit: {total_profit:.2f} USDT")
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Winning Trades: {winning_trades}")
        logger.info(f"Losing Trades: {losing_trades}")
        logger.info(f"Win Rate: {win_rate:.2f}%")

        print(self.trades)

# Example usage
if __name__ == "__main__":
    # Load historical data (replace with your actual data)
    historical_data = pd.read_csv('SOL_USDT_1h_historical_data.csv', parse_dates=['timestamp'], index_col='timestamp')

    # Initialize and run backtester
    backtester = Backtester(historical_data, initial_balance=100000)
    backtester.run_backtest()

    import matplotlib.pyplot as plt
    balance_over_time = [backtester.initial_balance] + [trade['profit'] + backtester.initial_balance for trade in backtester.trades]
    plt.plot(balance_over_time)
    plt.title("Balance Over Time")
    plt.xlabel("Trade Number")
    plt.ylabel("Balance (USDT)")
    plt.show()
