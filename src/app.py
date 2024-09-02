import threading
import time
from datetime import datetime
from flask import Flask
from src.routes import init_routes
from src.logger_config import setup_logging
import schedule
import pytz

from src.data.selected_nifty_companies import selected_companies
from src.trader import Trader

# Setup logging
setup_logging()

app = Flask(__name__)
init_routes(app)

# Define the specific times when the function should run
run_minutes = [16, 31, 46, 1]

def my_function():
    trader = Trader()
    print("Function is called at", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # Stocks to analyze
    stocks = selected_companies.keys()

    # Create threads for each stock
    threads = []

    for stock in stocks:
        thread = threading.Thread(target=trader.trade, args=(stock,))
        threads.append(thread)
        thread.start()

    # Optionally wait for all threads to complete
    for thread in threads:
        thread.join()


def run_scheduled_job():
    # Set the timezone to IST
    ist = pytz.timezone('Asia/Kolkata')

    # Get the current time in IST
    now = datetime.now(ist)

    # Define the start and end times
    start_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=16, second=0, microsecond=0)

    # Check if the current time is within the range and at the specified minutes
    if start_time <= now <= end_time and now.minute in run_minutes:
        my_function()


def schedule_tasks():
    # Schedule the task to check every minute
    schedule.every().minute.do(run_scheduled_job)

    while True:
        schedule.run_pending()
        time.sleep(1)


# Start the scheduler in a separate thread
def start_scheduler():
    scheduler_thread = threading.Thread(target=schedule_tasks)
    scheduler_thread.daemon = True
    scheduler_thread.start()


if __name__ == '__main__':
    if not app.debug or (app.debug and not app.run_reloader):
        start_scheduler()
    app.run(port=8000, debug=True, use_reloader=False)
