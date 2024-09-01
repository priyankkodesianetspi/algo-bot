from src.data.selected_nifty_companies import selected_companies
from src.trader import Trader
from src.utils.util import read_from_csv


def initialize_backtest_data():
    for key in selected_companies.keys():
        _data = read_from_csv(key)
        winrate = backtest_prediction_model(_data, 20, key)
        print(f"Win rate for {key}: {winrate:.2f}%")


def backtest_prediction_model(df, x, instrument_key):
    """
    Backtests a prediction model on a DataFrame.

    :param df: DataFrame containing stock data with 'Close' column.
    :param x: Number of rows to use for each prediction.
    :param model: Prediction model with a `predict` method that returns ('Buy'/'Sell', predicted_close).
    :return: Win rate percentage.
    """
    trader = Trader()
    predictions = []
    wins = 0
    total_predictions = 0

    for i in range(x, len(df) - 250):
        # Take the first `x` rows for prediction
        historical_data = df.iloc[i - x:i]

        # Predict the next action and predicted close value
        action, predicted_close = trader.generate_recommendation(instrument_key, True, historical_data)
        if action != 'Buy' and action != 'Sell':
            continue

        # Record the prediction
        df.at[i, 'Prediction_Action'] = action
        df.at[i, 'Predicted_Close'] = predicted_close

        # Determine the target price based on the action
        if action == 'Buy':
            target_price = df.iloc[i]['close'] * 1.002  # 0.2% increase
        elif action == 'Sell':
            target_price = df.iloc[i]['close'] * 0.997  # 0.3% decrease
        else:
            continue  # Skip if the action is not recognized

        # Check if the target price was hit
        subsequent_data = df.iloc[i + 1:i + x + 1]

        if not subsequent_data.empty:
            if action == 'Buy' and subsequent_data['close'].max() >= target_price:
                wins += 1
                df.at[i, 'Win/Loss'] = 'Win'
            elif action == 'Sell' and subsequent_data['close'].min() <= target_price:
                wins += 1
                df.at[i, 'Win/Loss'] = 'Loss'

        total_predictions += 1

    # Calculate win rate
    win_rate = (wins / total_predictions) * 100 if total_predictions > 0 else 0
    df.to_csv(f"data/{instrument_key}.csv", index=False)

    return win_rate


if __name__ == '__main__':
    # Initialize data
    initialize_backtest_data()
