import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
MODEL_PATH = 'lstm_model.h5'

# excluded_columns = ['Open', 'High', 'Low', 'Close', 'Volume',
#                     'fib_0.0', 'fib_0.236', 'fib_0.382', 'fib_0.5',
#                     'fib_0.618', 'fib_0.786', 'fib_1.0', 'rsi', 'sma', 'ema_20', 'ema_9',
#                     'bb_h', 'bb_l', 'vwap', 'atr', 'obv', 'ad_line', 'adx', 'ad_line', 'macd',
#                     'macd_signal', 'macd_diff', 'lag_open_1']

excluded_columns = []

def create_lagged_features(df, look_back=5):
    for i in range(1, look_back + 1):
        df[f'lag_open_{i}'] = df['Open'].shift(i)
        df[f'lag_close_{i}'] = df['Close'].shift(i)
    df.dropna(inplace=True)
    return df


# Function to normalize the features
def normalize_features(df):
    # 'rsi', 'sma', 'ema_20', 'ema_9', 'bb_h', 'bb_l', 'vwap', 'atr', 'obv', 'ad_line', 'adx', 'ad_line', 'macd', 'macd_signal', 'macd_diff'
    columns_to_scale = df.columns.difference(excluded_columns)
    scaler = MinMaxScaler()
    df[columns_to_scale] = scaler.fit_transform(df[columns_to_scale])
    return df, scaler


# Function to prepare LSTM data
def prepare_lstm_data(data, look_back=5):
    X, y = [], []
    for i in range(len(data) - look_back):
        X.append(data[i:(i + look_back), :])
        y.append(data[i + look_back, 3])  # Predicting Close based on Open and other features
    return np.array(X), np.array(y)


# Function to build and train LSTM model
def build_lstm_model(X_train, y_train, epochs=50, batch_size=32):
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(Dropout(0.2))
    model.add(LSTM(50))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_split=0.2, verbose=2)
    return model
