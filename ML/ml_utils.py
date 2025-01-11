import openai
from config import settings

openai.api_key = settings.OPENAI_API_KEY

def get_chatgpt_decision(market_data, trade_history):
    """
    Fetch trading suggestions from ChatGPT via OpenAI API.

    Parameters:
        market_data (dict): Latest market data and indicators.
        trade_history (list): List of recent trades.

    Returns:
        dict: ChatGPT decision with action and reasoning.
    """
    prompt = f"""
    You are a trading bot assistant. Analyze the following market data:
    {market_data}

    Recent trade history:
    {trade_history}

    Decide whether to 'buy', 'sell', or 'wait'. Provide a confidence level (0-100%) and reasoning.
    """
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.7,
        max_tokens=200
    )
    decision_text = response['choices'][0]['text'].strip()
    return decision_text
