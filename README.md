<div align="left">
  <a href="https://www.linkedin.com/in/george-toloraia/" target="_blank">
    <img src="https://raw.githubusercontent.com/maurodesouza/profile-readme-generator/master/src/assets/icons/social/linkedin/default.svg" width="52" height="40" alt="linkedin logo" />
  </a>
  <a href="https://discord.gg/AqDfEdAY" target="_blank">
    <img src="https://raw.githubusercontent.com/maurodesouza/profile-readme-generator/master/src/assets/icons/social/discord/default.svg" width="52" height="40" alt="discord logo" />
  </a>
</div>


# Advanced Trading Bot

This project implements an advanced trading bot using Python. The bot connects to the Binance exchange, evaluates trading signals based on various technical indicators, and executes trades accordingly. It also sends notifications about trading actions and errors to a specified Telegram chat.

## Features

- Fetches historical price data for multiple timeframes
- Analyzes order books and recent trades to determine market sentiment
- Uses technical indicators (e.g., EMA, RSI, MACD, Bollinger Bands) for signal evaluation
- Executes market buy/sell orders on Binance
- Implements stop-loss and take-profit mechanisms
- Sends trade notifications to Telegram

## Project Structure

```less
AutoBC/
├── bot.py                 # Main script to run the trading bot
├── config/
│   └── settings.py        # Configuration file for storing API keys and trading parameters
├── indicators/
│   └── technical_indicators.py  # Module for calculating technical indicators
├── trading/
│   ├── strategy.py        # Module for evaluating trading signals
│   └── trader.py          # Main trading logic, including order execution and monitoring
└── notifications/
    └── telegram_bot.py    # Module for sending notifications to Telegram
```

**Technical Indicators**

The bot uses the following technical indicators:

- Exponential Moving Average (EMA)
- Weighted Moving Average (WMA)
- Bollinger Bands
- TRIX
- Relative Strength Index (RSI)
- Moving Average Convergence Divergence (MACD)
- Average True Range (ATR)
- Stochastic Oscillator (STOCH)
- Commodity Channel Index (CCI)
- On-Balance Volume (OBV)



## Requirements

- Python 3.7+
- Binance account and API keys
- Telegram bot token and chat ID

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/georgetoloraia/AutoBC.git
   cd AutoBC
   ```

2. **Create and activate a virtual environment:**
    - On Linux/Mac

    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

    - On Windows
    ```sh
    python -m venv venv
    .venv/bin/activate
    ```

3. **Install the required Python packages:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up your environment variables:**
    - Create a `.env` file in the root directory of the project and add the following:
    ```env
    API_KEY=your_binance_api_key
    SECRET=your_binance_secret
    TELEGRAM_TOKEN=your_telegram_bot_token
    TELEGRAM_CHAT_ID=your_telegram_chat_id
    ```

## Usage

1. **Activate the virtual environment:**
    ```sh
    source venv/bin/activate  # On Windows use .\venv\Scripts\activate
    ```

2. **Run the bot:**
    ```sh
    python bot.py
    ```

3. **Deactivate the virtual environment when done:**
    ```sh
    deactivate
    ```

## Logging

**The bot logs its activity to results.txt in the root directory. The log includes information about fetched data, evaluated signals, placed orders, and any errors encountered.**

## Contributing

- **Contributions are welcome!**
- **Please fork the repository and submit a pull request with your changes.**

For Discord Server click this invitation [https://discord.gg/F6DuQYXA]

```env
## Contact

For any inquiries or issues, please contact [georgetoloraia@gmail.com].

---

By following these steps, you will be able to set up and run your advanced trading bot efficiently. If you have any questions or need further assistance, feel free to reach out. Happy trading!
```
