import numpy as np
import pandas as pd
from flask import Flask, request
import ta
from ta import add_all_ta_features
from ta.volatility import AverageTrueRange
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import SMAIndicator, EMAIndicator, ADXIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice, OnBalanceVolumeIndicator, AccDistIndexIndicator
from ta.trend import IchimokuIndicator, AroonIndicator, MACD

app = Flask(__name__)


def calculate_fibonacci_levels(df):
    """Calculate Fibonacci levels for the given dataframe."""
    max_price = df['High'].max()
    min_price = df['Low'].min()
    difference = max_price - min_price

    levels = {
        'fib_0.0': max_price,
        'fib_0.236': max_price - difference * 0.236,
        'fib_0.382': max_price - difference * 0.382,
        'fib_0.5': max_price - difference * 0.5,
        'fib_0.618': max_price - difference * 0.618,
        'fib_0.786': max_price - difference * 0.786,
        'fib_1.0': min_price
    }

    for key, value in levels.items():
        df[key] = value

    return df

# def get_indicators(df):
#     # Trend EMA
#     df['ema_200'] = ta.trend.ema_indicator(df['Close'], window=200)
#     df['ema_9'] = ta.trend.ema_indicator(df['Close'], window=9)
#     df['ema_21'] = ta.trend.ema_indicator(df['Close'], window=21)
#     df['ema_55'] = ta.trend.ema_indicator(df['Close'], window=55)
#     df['ema_100'] = ta.trend.ema_indicator(df['Close'], window=100)
#
#     # Supertrend
#     atr_10 = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=10)
#     df['supertrend'] = df['Close'] - atr_10 * 3  # Simplified supertrend for demo
#
#     # HMA
#     def hma(series, length):
#         half_length = length // 2
#         sqrt_length = int(np.sqrt(length))
#         wmaf = ta.trend.wma_indicator(series, window=half_length)
#         wmas = ta.trend.wma_indicator(series, window=length)
#         hma = ta.trend.wma_indicator(2 * wmaf - wmas, window=sqrt_length)
#         return hma
#
#     df['hma_100'] = hma(df['Close'], 100)
#
#     # Parabolic SAR
#     def psar(df, af_step=0.02, af_max=0.2):
#         High = df['High']
#         low = df['Low']
#         length = len(df)
#         psar = np.zeros(length)
#         bull = True
#         af = af_step
#         ep = low[0]
#         psar[0] = High[0]
#         for i in range(1, length):
#             psar[i] = psar[i - 1] + af * (ep - psar[i - 1])
#             reverse = False
#             if bull:
#                 if low[i] < psar[i]:
#                     bull = False
#                     reverse = True
#                     psar[i] = High[i]
#                     ep = low[i]
#                     af = af_step
#             else:
#                 if High[i] > psar[i]:
#                     bull = True
#                     reverse = True
#                     psar[i] = low[i]
#                     ep = High[i]
#                     af = af_step
#             if not reverse:
#                 if bull:
#                     if High[i] > ep:
#                         ep = High[i]
#                         af = min(af + af_step, af_max)
#                     if low[i - 1] < psar[i]:
#                         psar[i] = low[i - 1]
#                     if low[i - 2] < psar[i]:
#                         psar[i] = low[i - 2]
#                 else:
#                     if low[i] < ep:
#                         ep = low[i]
#                         af = min(af + af_step, af_max)
#                     if High[i - 1] > psar[i]:
#                         psar[i] = High[i - 1]
#                     if High[i - 2] > psar[i]:
#                         psar[i] = High[i - 2]
#         return psar
#
#     df['psar'] = psar(df)
#
#     # RSI
#     df['rsi_14'] = ta.momentum.rsi(df['Close'], window=14)
#
#     # MACD
#     macd = ta.trend.MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
#     df['macd'] = macd.macd()
#     df['macd_signal'] = macd.macd_signal()
#     df['macd_hist'] = macd.macd_diff()
#
#     # Wave Trend
#     n1, n2 = 9, 12
#     df['hlc3'] = (df['High'] + df['Low'] + df['Close']) / 3
#     df['esa'] = ta.trend.ema_indicator(df['hlc3'], window=n1)
#     df['d'] = ta.trend.ema_indicator(abs(df['hlc3'] - df['esa']), window=n1)
#     df['ci'] = (df['hlc3'] - df['esa']) / (0.015 * df['d'])
#     df['tci'] = ta.trend.ema_indicator(df['ci'], window=n2)
#     df['wt1'] = df['tci']
#     df['wt2'] = ta.trend.sma_indicator(df['wt1'], window=4)
#
#     # Stochastic
#     stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
#     df['k'] = stoch.stoch()
#     df['d'] = stoch.stoch_signal()
#
#     # Bollinger Bands
#     bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
#     df['bb_upper'] = bb.bollinger_hband()
#     df['bb_middle'] = bb.bollinger_mavg()
#     df['bb_lower'] = bb.bollinger_lband()
#
#     # ATR-based stop levels
#     df['atr_1'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=1)
#     df['long_stop'] = df['High'].rolling(window=1).max() - df['atr_1'] * 1.85
#     df['short_stop'] = df['Low'].rolling(window=1).min() + df['atr_1'] * 1.85
#
#     # Relative Volatility Index
#     df['stddev'] = df['Close'].rolling(window=12).std()
#     df['upper_rvi'] = ta.trend.ema_indicator(pd.Series(np.where(df['Close'].diff() <= 0, 0, df['stddev'])), window=14)
#     df['lower_rvi'] = ta.trend.ema_indicator(pd.Series(np.where(df['Close'].diff() > 0, 0, df['stddev'])), window=14)
#     df['rvi'] = df['upper_rvi'] / (df['upper_rvi'] + df['lower_rvi']) * 100
#
#     # OBV
#     df['obv'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
#
#     # Chaikin Money Flow
#     df['mf_mult'] = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
#     df['mf_vol'] = df['mf_mult'] * df['Volume']
#     df['cmf'] = df['mf_vol'].rolling(window=50).sum() / df['Volume'].rolling(window=50).sum()
#
#     return df

def get_indicators(df):
    # Ensure data length is sufficient for window sizes
    if len(df) < 20:
        raise ValueError("Data length must be at least 20 for the indicator calculations.")

    # Calculate ATR with window size 14 for demonstration purposes
    atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14)
    df['atr'] = atr.average_true_range()

    # Calculate RSI with window size 14 for demonstration purposes
    rsi = RSIIndicator(close=df['Close'], window=14)
    df['rsi'] = rsi.rsi()

    # Calculate SMA with window size 20 for demonstration purposes
    sma = SMAIndicator(close=df['Close'], window=20)
    df['sma'] = sma.sma_indicator()

    # Calculate EMA with window size 20 for demonstration purposes
    ema_20 = EMAIndicator(close=df['Close'], window=20)
    df['ema_20'] = ema_20.ema_indicator()

    # Calculate EMA with window size 9 for demonstration purposes
    ema_9 = EMAIndicator(close=df['Close'], window=9)
    df['ema_9'] = ema_9.ema_indicator()

    # Calculate Bollinger Bands with window size 20 for demonstration purposes
    bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['bb_h'] = bb.bollinger_hband()
    df['bb_l'] = bb.bollinger_lband()

    # Calculate VWAP without window size
    vwap = VolumeWeightedAveragePrice(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
    df['vwap'] = vwap.volume_weighted_average_price()

    # Calculate OBV
    obv = OnBalanceVolumeIndicator(close=df['Close'], volume=df['Volume'])
    df['obv'] = obv.on_balance_volume()

    # Calculate A/D line
    ad_line = AccDistIndexIndicator(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
    df['ad_line'] = ad_line.acc_dist_index()

    # Calculate Average Directional Index (ADX)
    adx = ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=11)
    df['adx'] = adx.adx()

    # Calculate Aroon Oscillator
    aroon = AroonIndicator(high=df['High'], low=df['Low'], window=25)
    df['aroon'] = aroon.aroon_indicator()

    # Calculate MACD
    macd = MACD(close=df['Close'])
    df['macd'] = macd.macd()
    df['macd_diff'] = macd.macd_diff()
    df['macd_signal'] = macd.macd_signal()

    # # Calculate Stochastic Oscillator
    # stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'], window=14)
    # df['stoch'] = stoch.stoch()
    # df['stoch_signal'] = stoch.stoch_signal()

    # Calculate Ichimoku Cloud
    # ichimoku = IchimokuIndicator(high=df['High'], low=df['Low'], window1=9, window2=26, window3=52)
    # df['ichimoku_a'] = ichimoku.ichimoku_a()
    # df['ichimoku_b'] = ichimoku.ichimoku_b()
    # df['ichimoku_base_line'] = ichimoku.ichimoku_base_line()
    # df['ichimoku_conversion_line'] = ichimoku.ichimoku_conversion_line()
    # df['ichimoku_lagging_line'] = ichimoku.ichimoku_base_line()

    # Calculate Fibonacci Levels
    # df = calculate_fibonacci_levels(df)

    return df


def indicators(data):
    df = pd.DataFrame(data)
    try:
        data_ind = get_indicators(df)
        return data_ind.to_json()  # Return JSON directly
    except ValueError as e:
        return {'error': str(e)}, 400
