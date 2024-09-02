import json
import re

from logzero import logger

from src.data.selected_nifty_companies import selected_companies
from src.kite.kite_service import KiteService
from src.llm._types import Message, Role
from src.llm.models import agent_setup

"""
An LLM Based Trader that uses the LLM to generate buy/sell recommendations for a given stock based on the stock data.
Flow :
Ticks for the last 5 days are provided.
app receives the ticks from the Kite service and stores them inside a file for each stock
after every 15 min, a new tick is received, a function gets the previous 5 days ticks and 
sends them to the trader. The trader generates a buy/sell recommendation and sends it back to the app.
This is done is parallel for 5 such stocks.



"""


class Trader:
    def __init__(self):
        """
        Initialize the CPE Analyzer with model configuration and iteration limit.

        Args:
            model (str): The model name for the CPE Analyzer.
            temp (float): The temperature for the CPE Analyzer model.
            top_p (float): The top_p for the CPE Analyzer model.
            max_tokens (int): The maximum tokens for the CPE Analyzer model.
        """
        self.chat = agent_setup(agent_model='gpt-4o',
                                agent_temp=0.4,
                                agent_top_p=1,
                                agent_max_tokens=4096)
        self.online_chat = agent_setup(agent_model='perplexity_large',
                                       agent_temp=0.4,
                                       agent_top_p=1,
                                       agent_max_tokens=4096)

        self.kite_service = KiteService()

    @staticmethod
    def get_system_prompt() -> str:
        example = '''
            [{
            "Open": 809.380005,
            "High": 812.750000,
            "Low": 806.599976,
            "Close": 808.630005,
            "ema_200": 773.115523,
            "ema_9": 795.222143,
            "ema_21": 789.955800,
            "ema_55": 784.648250,
            "ema_100": 780.243495
        }]
        '''
        output = '''
            [
                {
                    "predicted_close": 1138.0,
                    "confidence_score": 0.78,
                    "decision": "Buy",
                    "target_price": 1145.0,
                    "stop_loss": 1130.0
                }
            ]
        '''
        system_prompt_template = f"""`You are an expert stock trader who does scalping on a 15 min timeframe chart. 
        When given stock market data. You look at the last 10-15 days of provided 15-minute tick data and deeply analyze the provided indicators, volatility, volume 
        to provide informed buy or sell recommendations. Study the moving averages, RSI, MACD, and other indicators to provide a buy or sell signal. 
        Refer the below example for the data format.`\n{example}. Output should be in the format of \n{output}. Do not send the analysis. Only the predicted result as json."""
        return system_prompt_template

    @staticmethod
    def get_user_prompt(tick_data: str) -> str:
        user_prompt_template = f"""Here are the 15-minute tick prices for the last X days of a given stock. 
        Please analyze the data and provide a buy or sell signal with a target price, stop-loss value, and predicted next close.
        Also provide a confidence score of your prediction. Only generate a buy or sell signal if the confidence score is more than 75 percent. Ticker data is : {tick_data}. Output should be only the values as json array."""
        return user_prompt_template

    @staticmethod
    def get_system_prompt_news() -> str:
        output = '''
                {
                    "rating": 4
                }
        '''
        system_prompt_template = f"""You are an expert stock trader and news analyst who can get the latest news about a provided stock and analyze it to give a rating from 0-5. 
        Where 1 represents very bad news and 5 represents very good news. Output should strictly be in json format like {output}. 
        Only consider latest one news from last 2 days. Ignore the news if it is about subsidiary or parent company. We are only concerned about the asked company. If you are not sure about the news or are not able to find any news less than 2 days old, you can give a rating of 0."""
        return system_prompt_template

    @staticmethod
    def get_user_prompt_news(ticker_symbol: str) -> str:
        full_company_name = selected_companies[ticker_symbol][1]
        user_prompt_template = f"""Here is the ticker symbol : {ticker_symbol} and full company name : {full_company_name}."""
        return user_prompt_template

    def generate_tick_data(self, ticker_symbol: str):
        data = self.kite_service.get_historical_data_for_stock(ticker_symbol)
        return data

    # {"TT":"BUY","TS":"SBIN", "PRICE": 123}
    def trade(self, ticker_symbol: str):
        action, predicted_close = self.generate_recommendation(ticker_symbol)
        if action != 'Buy' and action != 'Sell':
            return

        positions = self.kite_service.kite.positions()['day']
        if positions:
            for position in positions:
                if position['tradingsymbol'] == ticker_symbol:
                    if action == 'Buy':
                        if position['quantity'] < 0:
                            # If we have a short position, close it
                            # {"TT":"BUY","TS":"SBIN", "PRICE": 123, "QTY": 1}
                            self.kite_service.place_order(
                                {"TT": "BUY", "TS": ticker_symbol, "QTY": abs(position['quantity']), "PRICE": None})
                    elif action == 'Sell':
                        if position['quantity'] > 0:
                            # If we have a long position, close it
                            self.kite_service.place_order(
                                {"TT": "SELL", "TS": ticker_symbol, "QTY": abs(position['quantity']), "PRICE": None})
                else:
                    # We don't have an open position for this stock
                    if action == 'Buy':
                        self.kite_service.place_order({"TT": "BUY", "TS": ticker_symbol, "PRICE": None, "QTY": None})
                    elif action == 'Sell':
                        self.kite_service.place_order({"TT": "SELL", "TS": ticker_symbol, "PRICE": None, "QTY": None})
        else:
            # We don't have an open position for this stock
            if action == 'Buy':
                self.kite_service.place_order({"TT": "BUY", "TS": ticker_symbol, "PRICE": None, "QTY": None})
            elif action == 'Sell':
                self.kite_service.place_order({"TT": "SELL", "TS": ticker_symbol, "PRICE": None, "QTY": None})

    def get_news_rating(self, ticker_symbol):
        messages = [
            Message(role=Role.system, content=self.get_system_prompt_news()),
            Message(role=Role.user, content=self.get_user_prompt_news(ticker_symbol)),
        ]
        response = self.online_chat(messages)
        match = re.search(r'"rating":\s*(\d+)', response.content)

        if match:
            rating = int(match.group(1))
            return rating
        else:
            return None

    def generate_recommendation(self, ticker_symbol: str, is_backtest: bool = False, historical_data: str = None):
        system_prompt = self.get_system_prompt()

        if not is_backtest:
            messages = [
                Message(role=Role.system, content=system_prompt),
                Message(role=Role.user, content=self.get_user_prompt(self.generate_tick_data(ticker_symbol))),
            ]
        else:
            messages = [
                Message(role=Role.system, content=system_prompt),
                Message(role=Role.user, content=self.get_user_prompt(historical_data)),
            ]

        successful = False
        response = None
        try:
            logger.debug(
                f"Attempting to produce Prediction for {ticker_symbol}")
            # Get News data from Perplexity
            # news_rating = self.get_news_rating(ticker_symbol)

            # Get prediction from gpt-4o
            response = self.chat(messages)

            # Get prediction from Perplexity
            online_response = self.online_chat(messages)

            # Remove the ```json and ``` markers from the content
            json_str = response.content.strip('```json\n').strip('```')
            json_str_online = online_response.content.strip('```json\n').strip('```')

            # Parse the JSON string
            res = json.loads(json_str)[0]
            res_online = json.loads(json_str_online)[0]

            if res.get('confidence_score') < 0.75 or res_online.get('confidence_score') < 0.75:
                logger.debug(f"Confidence score is less than 75%")
                return None, None
            if res.get('decision') != res_online.get('decision'):
                logger.debug(f"Decision is different in online and offline model")
                return None, None
            successful = True
            return res.get('decision'), min(res.get('predicted_close'), res_online.get('predicted_close'))
        except ValueError:
            logger.warning(f"Invalid JSON response from LLM. ")

        if not successful:
            logger.error(f"Failed to parse a valid JSON response from model {response.content}")
