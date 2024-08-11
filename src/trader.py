import json
import sys

from logzero import logger

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
    def __init__(self, model: str,
                 temp: float,
                 top_p: float,
                 max_tokens: int,
                 ):
        """
        Initialize the CPE Analyzer with model configuration and iteration limit.

        Args:
            model (str): The model name for the CPE Analyzer.
            temp (float): The temperature for the CPE Analyzer model.
            top_p (float): The top_p for the CPE Analyzer model.
            max_tokens (int): The maximum tokens for the CPE Analyzer model.
        """
        self.chat = agent_setup(agent_model=model,
                                agent_temp=temp,
                                agent_top_p=top_p,
                                agent_max_tokens=4096)

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
        [{
        "predicted_close": 810.0,
        "confidence_score": 0.85,
        "decision": "Buy"
        }]
        '''
        system_prompt_template = f"""`You are an expert financial analyst and an expert stock trader. 
        When given stock market data, you analyze trends, provided indicators, volatility, volume 
        to provide informed buy or sell recommendations. 
        Suggest target prices or stop-loss values where applicable. 
        Refer the below example for the data format.`\n{example}. Output should be in the format of \n{output}"""
        return system_prompt_template

    @staticmethod
    def get_user_prompt(tick_data: str) -> str:
        user_prompt_template = f"""Here are the 15-minute tick prices for the last X days of a given stock. 
        Please analyze the data and provide a buy or sell signal with a target price, stop-loss value, and predicted next close.
        Also provide a confidence score of your prediction. Only generate a buy or sell signal if the confidence score is more than 75 percent. Ticker data is : {tick_data}. Output should be only the values as json array."""
        return user_prompt_template

    def generate_recommendation(self, ticker_symbol: str, tick_data: str):
        system_prompt = self.get_system_prompt()

        messages = [
            Message(role=Role.system, content=system_prompt),
            Message(role=Role.user, content=self.get_user_prompt(tick_data))
        ]

        successful = False
        response = None
        try:
            logger.debug(
                f"Attempting to produce Prediction for {ticker_symbol}")
            response = self.chat(messages)
            print(response.content)
            res = json.loads(response.content.strip("```"))[0]
            print(res)
            print(res.get('confidence_score'))
            print(res.get('predicted_close'))
            print(res.get('target'))
            print(res.get('stop_loss'))

        except ValueError:
            logger.warning(f"Invalid JSON response from LLM. ")

        if not successful:
            logger.error(f"Failed to parse a valid JSON response from model {response.content}")


if __name__ == '__main__':
    trader = Trader(model='gpt-4o',
                    temp=0.4,
                    top_p=1.0,
                    max_tokens=10000)
    trader.generate_recommendation(ticker_symbol='ICICIBANK', tick_data='''
    [
    {
        "Timestamp": "2024-08-07T14:45:00+05:30",
        "Open": 1132.35,
        "High": 1138.65,
        "Low": 1131.3,
        "Close": 1137.55,
        "Volume": 1382379,
        "atr": 6.9927164441,
        "rsi": 48.9400613302,
        "sma": 1138.5575,
        "ema_20": 1137.3493151587,
        "ema_9": 1135.4131015883,
        "bb_h": 1152.7823822491,
        "bb_l": 1124.3326177509,
        "vwap": 1135.0514926143,
        "obv": 2956543,
        "ad_line": -116774.6802449673,
        "adx": 14.2811930658,
        "aroon": -52.0,
        "macd": -2.4013714799,
        "macd_diff": null,
        "macd_signal": null
    },
    {
        "Timestamp": "2024-08-07T14:15:00+05:30",
        "Open": 1133.9,
        "High": 1136.0,
        "Low": 1130.65,
        "Close": 1132.35,
        "Volume": 1481513,
        "atr": 6.986093841,
        "rsi": 43.14822407,
        "sma": 1137.59,
        "ema_20": 1136.8731899055,
        "ema_9": 1134.8004812706,
        "bb_h": 1150.695899435,
        "bb_l": 1124.484100565,
        "vwap": 1134.1192895828,
        "obv": 1475030,
        "ad_line": -656765.3998712203,
        "adx": 14.3874138258,
        "aroon": -52.0,
        "macd": -2.5022036892,
        "macd_diff": null,
        "macd_signal": null
    },
    {
        "Timestamp": "2024-08-07T13:45:00+05:30",
        "Open": 1134.05,
        "High": 1135.6,
        "Low": 1131.75,
        "Close": 1133.9,
        "Volume": 609145,
        "atr": 6.7620871381,
        "rsi": 45.2289549227,
        "sma": 1136.73,
        "ema_20": 1136.5900289621,
        "ema_9": 1134.6203850165,
        "bb_h": 1148.3500430292,
        "bb_l": 1125.1099569708,
        "vwap": 1133.8490492724,
        "obv": 2084175,
        "ad_line": -585566.6336374093,
        "adx": 14.4839781531,
        "aroon": -52.0,
        "macd": -2.429041418,
        "macd_diff": null,
        "macd_signal": null
    },
    {
        "Timestamp": "2024-08-07T13:15:00+05:30",
        "Open": 1132.75,
        "High": 1135.0,
        "Low": 1130.8,
        "Close": 1134.05,
        "Volume": 537633,
        "atr": 6.5790809139,
        "rsi": 45.4370748953,
        "sma": 1136.0,
        "ema_20": 1136.3481214419,
        "ema_9": 1134.5063080132,
        "bb_h": 1146.2914041802,
        "bb_l": 1125.7085958198,
        "vwap": 1133.652739284,
        "obv": 2621808,
        "ad_line": -291148.5622088469,
        "adx": 14.8941475435,
        "aroon": -52.0,
        "macd": -2.3320733546,
        "macd_diff": null,
        "macd_signal": null
    },
    {
        "Timestamp": "2024-08-07T12:45:00+05:30",
        "Open": 1133.65,
        "High": 1135.0,
        "Low": 1130.9,
        "Close": 1132.7,
        "Volume": 413130,
        "atr": 6.4020037058,
        "rsi": 43.8231134558,
        "sma": 1135.0875,
        "ema_20": 1136.0006813046,
        "ema_9": 1134.1450464106,
        "bb_h": 1142.8373306433,
        "bb_l": 1127.3376693567,
        "vwap": 1133.4454111744,
        "obv": 2208678,
        "ad_line": -341530.2695259211,
        "adx": 15.2670288075,
        "aroon": -52.0,
        "macd": -2.3372171983,
        "macd_diff": null,
        "macd_signal": null
    },
    {
        "Timestamp": "2024-08-07T12:15:00+05:30",
        "Open": 1128.55,
        "High": 1136.4,
        "Low": 1128.5,
        "Close": 1133.65,
        "Volume": 344054,
        "atr": 6.5090034411,
        "rsi": 45.2956932211,
        "sma": 1134.6,
        "ema_20": 1135.7768068946,
        "ema_9": 1134.0460371285,
        "bb_h": 1141.3603993965,
        "bb_l": 1127.8396006035,
        "vwap": 1133.3589962429,
        "obv": 2552732,
        "ad_line": -237007.5353487032,
        "adx": 16.4428618765,
        "aroon": -52.0,
        "macd": -2.2388288456,
        "macd_diff": null,
        "macd_signal": null
    },
    {
        "Timestamp": "2024-08-07T11:45:00+05:30",
        "Open": 1130.45,
        "High": 1131.5,
        "Low": 1128.3,
        "Close": 1128.55,
        "Volume": 275562,
        "atr": 6.426217481,
        "rsi": 39.3345852027,
        "sma": 1134.3275,
        "ema_20": 1135.0885395713,
        "ema_9": 1132.9468297028,
        "bb_h": 1141.583840331,
        "bb_l": 1127.071159669,
        "vwap": 1133.0907651952,
        "obv": 2277170,
        "ad_line": -469512.9728487039,
        "adx": 17.5790937939,
        "aroon": -52.0,
        "macd": -2.5430678418,
        "macd_diff": 0.0588786869,
        "macd_signal": -2.6019465287
    },
    {
        "Timestamp": "2024-08-07T11:15:00+05:30",
        "Open": 1129.15,
        "High": 1130.7,
        "Low": 1127.0,
        "Close": 1130.45,
        "Volume": 390481,
        "atr": 6.2314876609,
        "rsi": 42.3771040016,
        "sma": 1133.9475,
        "ema_20": 1134.6467738979,
        "ema_9": 1132.4474637622,
        "bb_h": 1141.1802363425,
        "bb_l": 1126.7147636575,
        "vwap": 1132.9232996983,
        "obv": 2667651,
        "ad_line": -131799.6755514059,
        "adx": 19.0555232321,
        "aroon": -52.0,
        "macd": -2.600883946,
        "macd_diff": 0.0008500662,
        "macd_signal": -2.6017340121
    },
    {
        "Timestamp": "2024-08-07T10:45:00+05:30",
        "Open": 1136.7,
        "High": 1137.45,
        "Low": 1127.0,
        "Close": 1129.35,
        "Volume": 490659,
        "atr": 6.5328099709,
        "rsi": 41.0921868661,
        "sma": 1133.4525,
        "ema_20": 1134.1423192409,
        "ema_9": 1131.8279710098,
        "bb_h": 1140.5190744884,
        "bb_l": 1126.3859255116,
        "vwap": 1132.8681187825,
        "obv": 2176992,
        "ad_line": -401779.5080873006,
        "adx": 17.6753003348,
        "aroon": -52.0,
        "macd": -2.7042910482,
        "macd_diff": -0.0820456288,
        "macd_signal": -2.6222454193
    },
    {
        "Timestamp": "2024-08-07T10:15:00+05:30",
        "Open": 1136.25,
        "High": 1141.0,
        "Low": 1132.1,
        "Close": 1136.9,
        "Volume": 438270,
        "atr": 6.8983235444,
        "rsi": 51.8774638679,
        "sma": 1133.4475,
        "ema_20": 1134.4049555037,
        "ema_9": 1132.8423768078,
        "bb_h": 1140.5041617462,
        "bb_l": 1126.3908382538,
        "vwap": 1133.4845294723,
        "obv": 2615262,
        "ad_line": -367308.8339299841,
        "adx": 17.6450199368,
        "aroon": -52.0,
        "macd": -2.1522106747,
        "macd_diff": 0.3760277957,
        "macd_signal": -2.5282384704
    },
    {
        "Timestamp": "2024-08-07T09:45:00+05:30",
        "Open": 1142.6,
        "High": 1143.4,
        "Low": 1133.4,
        "Close": 1136.25,
        "Volume": 655904,
        "atr": 7.1198718626,
        "rsi": 51.011543498,
        "sma": 1133.3675,
        "ema_20": 1134.5806740272,
        "ema_9": 1133.5239014463,
        "bb_h": 1140.2570046992,
        "bb_l": 1126.4779953008,
        "vwap": 1134.068450215,
        "obv": 1959358,
        "ad_line": -649347.5539299961,
        "adx": 18.3266022669,
        "aroon": -48.0,
        "macd": -1.746994306,
        "macd_diff": 0.6249953315,
        "macd_signal": -2.3719896375
    },
    {
        "Timestamp": "2024-08-07T09:15:00+05:30",
        "Open": 1138.8,
        "High": 1144.8,
        "Low": 1134.0,
        "Close": 1142.65,
        "Volume": 702969,
        "atr": 7.3827381582,
        "rsi": 58.3782138146,
        "sma": 1133.8,
        "ema_20": 1135.3491812627,
        "ema_9": 1135.349121157,
        "bb_h": 1141.7918708698,
        "bb_l": 1125.8081291302,
        "vwap": 1134.801323629,
        "obv": 2662327,
        "ad_line": -226264.3594855351,
        "adx": 19.3347689701,
        "aroon": 56.0,
        "macd": -0.8990670165,
        "macd_diff": 1.1783380968,
        "macd_signal": -2.0774051133
    },
    {
        "Timestamp": "2024-08-06T15:15:00+05:30",
        "Open": 1125.3,
        "High": 1129.25,
        "Low": 1125.25,
        "Close": 1127.3,
        "Volume": 844307,
        "atr": 8.0982568611,
        "rsi": 42.0468072335,
        "sma": 1133.2325,
        "ema_20": 1134.582592571,
        "ema_9": 1133.7392969256,
        "bb_h": 1141.3766558801,
        "bb_l": 1125.0883441199,
        "vwap": 1134.1384734013,
        "obv": 1818020,
        "ad_line": -205156.6844855543,
        "adx": 18.2192252473,
        "aroon": -4.0,
        "macd": -1.4489921656,
        "macd_diff": 0.5027303582,
        "macd_signal": -1.9517225238
    },
    {
        "Timestamp": "2024-08-06T14:45:00+05:30",
        "Open": 1126.2,
        "High": 1128.2,
        "Low": 1123.1,
        "Close": 1125.3,
        "Volume": 1926769,
        "atr": 7.8840956568,
        "rsi": 40.4586606345,
        "sma": 1132.7475,
        "ema_20": 1133.6985361356,
        "ema_9": 1132.0514375405,
        "bb_h": 1141.5421844742,
        "bb_l": 1123.9528155258,
        "vwap": 1132.2271252616,
        "obv": -108749,
        "ad_line": -469615.1746816429,
        "adx": 17.8032237361,
        "aroon": -8.0,
        "macd": -2.0228766309,
        "macd_diff": -0.0569232857,
        "macd_signal": -1.9659533452
    },
    {
        "Timestamp": "2024-08-06T14:15:00+05:30",
        "Open": 1129.2,
        "High": 1132.65,
        "Low": 1126.2,
        "Close": 1126.2,
        "Volume": 823708,
        "atr": 7.845945967,
        "rsi": 41.5289365557,
        "sma": 1132.5575,
        "ema_20": 1132.984389837,
        "ema_9": 1130.8811500324,
        "bb_h": 1141.7371663883,
        "bb_l": 1123.3778336117,
        "vwap": 1131.4038234919,
        "obv": 714959,
        "ad_line": -1293323.174681643,
        "adx": 16.3785173294,
        "aroon": -8.0,
        "macd": -2.3776536151,
        "macd_diff": -0.3293602159,
        "macd_signal": -2.0482933992
    },
    {
        "Timestamp": "2024-08-06T13:45:00+05:30",
        "Open": 1134.2,
        "High": 1134.85,
        "Low": 1128.0,
        "Close": 1129.2,
        "Volume": 612879,
        "atr": 7.9033783979,
        "rsi": 45.0731914628,
        "sma": 1132.425,
        "ema_20": 1132.6239717573,
        "ema_9": 1130.5449200259,
        "bb_h": 1141.7174969734,
        "bb_l": 1123.1325030266,
        "vwap": 1131.0942609944,
        "obv": 1327838,
        "ad_line": -1691470.8462144788,
        "adx": 15.7078078163,
        "aroon": -8.0,
        "macd": -2.3892007837,
        "macd_diff": -0.2727259076,
        "macd_signal": -2.1164748761
    },
    {
        "Timestamp": "2024-08-06T13:15:00+05:30",
        "Open": 1135.55,
        "High": 1138.5,
        "Low": 1130.05,
        "Close": 1134.15,
        "Volume": 662486,
        "atr": 8.0031370838,
        "rsi": 50.4140516365,
        "sma": 1132.7125,
        "ema_20": 1132.7693077804,
        "ema_9": 1131.2659360207,
        "bb_h": 1141.8434843391,
        "bb_l": 1123.5815156609,
        "vwap": 1131.1449102886,
        "obv": 1990324,
        "ad_line": -1711071.0237292538,
        "adx": 16.0374264954,
        "aroon": -8.0,
        "macd": -1.9761485565,
        "macd_diff": 0.1122610557,
        "macd_signal": -2.0884096122
    },
    {
        "Timestamp": "2024-08-06T12:45:00+05:30",
        "Open": 1135.5,
        "High": 1137.35,
        "Low": 1134.0,
        "Close": 1135.55,
        "Volume": 213978,
        "atr": 7.6707701492,
        "rsi": 51.8403732875,
        "sma": 1133.06,
        "ema_20": 1133.0341356109,
        "ema_9": 1132.1227488166,
        "bb_h": 1142.0666419936,
        "bb_l": 1124.0533580064,
        "vwap": 1131.123391283,
        "obv": 2204302,
        "ad_line": -1727039.5311919409,
        "adx": 16.3370798399,
        "aroon": -8.0,
        "macd": -1.518331016,
        "macd_diff": 0.456062877,
        "macd_signal": -1.9743938929
    },
    {
        "Timestamp": "2024-08-06T12:15:00+05:30",
        "Open": 1138.35,
        "High": 1138.6,
        "Low": 1134.5,
        "Close": 1135.3,
        "Volume": 264906,
        "atr": 7.4157151386,
        "rsi": 51.5551875002,
        "sma": 1133.11,
        "ema_20": 1133.2499322193,
        "ema_9": 1132.7581990533,
        "bb_h": 1142.1546448244,
        "bb_l": 1124.0653551756,
        "vwap": 1131.1935854686,
        "obv": 1939396,
        "ad_line": -1888567.5799724322,
        "adx": 16.9390394984,
        "aroon": -8.0,
        "macd": -1.1622821621,
        "macd_diff": 0.6496893847,
        "macd_signal": -1.8119715468
    }
]
''')
