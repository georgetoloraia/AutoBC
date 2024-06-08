# Advanced Trading Bot

This project implements an advanced trading bot using Python. The bot connects to the Binance exchange, evaluates trading signals based on various technical indicators, and executes trades accordingly. It also sends notifications about trading actions and errors to a specified Telegram chat.

## Features

- Fetches historical price data for multiple timeframes
- Analyzes order books and recent trades to determine market sentiment
- Uses technical indicators (e.g., EMA, RSI, MACD, Bollinger Bands) for signal evaluation
- Executes market buy/sell orders on Binance
- Implements stop-loss and take-profit mechanisms
- Sends trade notifications to Telegram

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
