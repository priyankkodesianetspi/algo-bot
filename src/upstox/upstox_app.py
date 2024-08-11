import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from flask import Flask, request, redirect, jsonify
from src.indicators import indicators, get_indicators
from src.upstox.upstox_order_apis import UpstoxOrderClient
from src.utils.util import get_access_token, load_data, save_to_csv

app = Flask(__name__)

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Load environment variables
UPSTOX_API_KEY = os.getenv('UPSTOX_API_KEY', 'e154869b-0ffe-4c95-9103-86b8200cc5ca')
UPSTOX_API_SECRET = os.getenv('UPSTOX_API_SECRET', 'n2x3go8trh')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://127.0.0.1:8000/callback')

# Print environment variable info for verification
print(f"Upstox Client ID: {UPSTOX_API_KEY}")
print(f"Upstox Client Secret: {UPSTOX_API_SECRET}")
print(f"Redirect URI: {REDIRECT_URI}")


@app.route('/')
def login():
    authorization_url = f'https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={UPSTOX_API_KEY}&redirect_uri={REDIRECT_URI}'
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return 'Authorization code not found', 400

    token_url = 'https://api.upstox.com/v2/login/authorization/token'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'code': code, 'client_id': UPSTOX_API_KEY, 'client_secret': UPSTOX_API_SECRET, 'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'}
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        with open('access_token.txt', 'w+') as token_file:
            token_file.write(access_token)
        return jsonify(response.json())
    else:
        return jsonify(response.json()), response.status_code


@app.route('/historical-data/upstox', methods=['POST'])
def historical_data():
    data = request.get_json()
    instrument_key = data.get('instrument_key', 'NSE_EQ|INE238A01034')
    interval = data.get('interval', '30minute')

    # Calculate the dates for the last 5 days
    to_date = data.get('to_date', datetime.now().strftime('%Y-%m-%d'))
    from_date = data.get('from_date', (datetime.now() - timedelta(days=21)).strftime('%Y-%m-%d'))

    client = UpstoxOrderClient(get_access_token())
    historical_data_response = client.get_historical_candle_data(instrument_key=instrument_key, interval=interval,
                                                                 to_date=to_date, from_date=from_date)
    if historical_data_response is None:
        return "Failed to fetch historical data", 500

    df = pd.DataFrame(historical_data_response.data.candles,
                      columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Open Interest'])
    df = df.drop(['Open Interest'], axis=1)
    df.dropna(inplace=True)
    response = get_indicators(df)
    print(df.head(50).to_json(orient='records'))
    # df = pd.read_json(response)
    save_to_csv(response, instrument_key)
    return jsonify({"message": "Dataframe saved to CSV file successfully"}), 200


def load_data(file_path):
    df = pd.read_csv(file_path)
    df['Close'] = df['Close'].astype(float)
    return df


# # Function to predict and update CSV
# def predict_and_update_csv(model, X_test, df_test, file_path, scaler):
#
#     predictions = model.predict(X_test)
#
#     # Create a dummy DataFrame to hold the predictions in the same structure
#     dummy_df = pd.DataFrame(np.zeros((predictions.shape[0], df_test.shape[1])), columns=df_test.columns)
#     dummy_df['Close'] = predictions.flatten()
#
#     # Inverse transform only the columns that were scaled
#     columns_to_scale = df_test.columns.difference(excluded_columns)
#     # dummy_df[columns_to_scale] = scaler.inverse_transform(dummy_df[columns_to_scale])
#
#     df_test['Predicted_Close'] = dummy_df['Close']
#
#     # Generate signals and evaluate success
#     target_threshold = 0.005  # 0.5%
#     stop_loss_threshold = -0.003  # -0.3%
#     df_test['Signal'] = np.where(df_test['Predicted_Close'] > df_test['Open'], 'BUY', 'SELL')
#     df_test['Success'] = 'HOLD'
#
#     for i in range(df_test.shape[0]):
#         if df_test.at[df_test.index[i], 'Signal'] == 'BUY':
#             if df_test.at[df_test.index[i], 'Close'] >= df_test.at[df_test.index[i], 'Open'] * (1 + target_threshold):
#                 df_test.at[df_test.index[i], 'Success'] = True
#             elif df_test.at[df_test.index[i], 'Close'] <= df_test.at[df_test.index[i], 'Open'] * (
#                     1 + stop_loss_threshold):
#                 df_test.at[df_test.index[i], 'Success'] = False
#
#     df_test.to_csv(file_path, index=False)
#     return df_test
#

# @app.route('/predict-and-update', methods=['POST'])
# def predict_and_update():
#     data = request.get_json()
#
#     # Load data from CSV
#     instrument_key = data.get('instrument_key', 'NSE_EQ|INE238A01034')
#     file_path = f"{instrument_key.split('|')[1]}.csv"
#     df = load_data(file_path)
#
#     # Feature engineering
#     look_back = data.get('look_back', 5)
#     df = create_lagged_features(df, look_back)
#
#     # Normalize features
#     # df, scaler = normalize_features(df)
#
#     # Prepare data for LSTM
#     X, y = prepare_lstm_data(df.values, look_back)
#
#     # Reshape input to be [samples, time steps, features]
#     X = np.reshape(X, (X.shape[0], look_back, df.shape[1]))
#
#     # Split into train and test sets
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#
#     # Build and train LSTM model if not exists
#     if not os.path.exists(MODEL_PATH):
#         model = build_lstm_model(X_train, y_train)
#         model.save(MODEL_PATH)
#     else:
#         model = load_model(MODEL_PATH)
#
#     # Predict and update CSV
#     df_test = df.iloc[-len(X_test):].reset_index(drop=True)  # Corresponding test DataFrame portion
#     result_df = predict_and_update_csv(model, X_test, df_test, file_path, None)
#
#     return jsonify({"message": "Predictions added and CSV updated successfully"}), 200

# Function to update CSV with signals
# def predict_and_update_csv(df_test, file_path):
#     # Generate buy and sell signals using the calculate_signals function
#     df_test = calculate_signals(df_test)
#
#     # Evaluate success based on signals and price movements
#     target_threshold = 0.005  # 0.5%
#     stop_loss_threshold = -0.003  # -0.3%
#     # df_test['Signal'] = np.where(df_test['buy_signal'], 'BUY', np.where(df_test['sell_signal'], 'SELL', 'HOLD'))
#     # df_test['Success'] = 'HOLD'
#     #
#     # for i in range(df_test.shape[0]):
#     #     if df_test.at[df_test.index[i], 'Signal'] == 'BUY':
#     #         if df_test.at[df_test.index[i], 'Close'] >= df_test.at[df_test.index[i], 'Open'] * (1 + target_threshold):
#     #             df_test.at[df_test.index[i], 'Success'] = True
#     #         elif df_test.at[df_test.index[i], 'Close'] <= df_test.at[df_test.index[i], 'Open'] * (
#     #                 1 + stop_loss_threshold):
#     #             df_test.at[df_test.index[i], 'Success'] = False
#     #     elif df_test.at[df_test.index[i], 'Signal'] == 'SELL':
#     #         if df_test.at[df_test.index[i], 'Close'] <= df_test.at[df_test.index[i], 'Open'] * (1 - target_threshold):
#     #             df_test.at[df_test.index[i], 'Success'] = True
#     #         elif df_test.at[df_test.index[i], 'Close'] >= df_test.at[df_test.index[i], 'Open'] * (
#     #                 1 - stop_loss_threshold):
#     #             df_test.at[df_test.index[i], 'Success'] = False
#
#     df_test.to_csv(file_path, index=False)
#     return df_test


# @app.route('/predict-and-update', methods=['POST'])
# def predict_and_update():
#     data = request.get_json()
#
#     # Load data from CSV
#     instrument_key = data.get('instrument_key', 'NSE_EQ|INE238A01034')
#     file_path = f"{instrument_key.split('|')[1]}.csv"
#     df = load_data(file_path)
#
#     # Feature engineering
#     # look_back = data.get('look_back', 5)
#     # df = create_lagged_features(df, look_back)
#
#     # Calculate technical indicators
#     df = get_indicators(df)
#
#     # Predict and update CSV
#     # df_test = df.iloc[-len(df):].reset_index(drop=True)  # Corresponding test DataFrame portion
#     result_df = predict_and_update_csv(df, file_path)
#
#     return jsonify({"message": "Signals generated and CSV updated successfully"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

# Historical Price Data:
#
# Open, high, low, close (OHLC) prices.
# Intraday price patterns (minute-by-minute, hourly).
#
# Technical Indicators:
#
# Moving Averages (SMA, EMA).
# Relative Strength Index (RSI).
# Bollinger Bands.
# Moving Average Convergence Divergence (MACD).
# Volume-Weighted Average Price (VWAP).
# Stochastic Oscillator.
# Average True Range (ATR).
#
# Volume Data:
#
# Trade volume.
# On-balance volume (OBV).
# Volume spikes and trends.
#
# Market Sentiment:
#
# News sentiment analysis.
# Social media sentiment (e.g., Twitter, StockTwits).
# Analyst ratings and reports.
#
# Order Book Data:
#
# Bid-ask spread.
# Order book depth.
# Trade order flow.
#
# Economic Indicators:
#
# Interest rates.
# Inflation rates.
# GDP growth rates.
# Employment data.
#
# Sector and Industry Data:
#
# Sector performance.
# Industry trends and news.
#
# Corporate Actions and News:
#
# Earnings reports.
# Dividends.
# Stock splits.
# Mergers and acquisitions.
# Regulatory changes.
#
# Time and Calendar Features:
#
# Time of day.
# Day of the week.
# Month of the year.
# Trading sessions (pre-market, regular trading hours, post-market).
#
# Macroeconomic Events:
#
# Central bank announcements.
# Economic reports (e.g., CPI, PPI).
# Geopolitical events.
#
# Market Sentiment Indicators:
#
# VIX (Volatility Index).
# Put/Call ratio.
#
# Intermarket Data:
#
# Correlation with other assets (commodities, currencies, bonds).
# Global market indices (e.g., S&P 500, FTSE 100)
