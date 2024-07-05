from flask import Flask
from src.routes import init_routes
from src.logger_config import setup_logging

# Setup logging
setup_logging()

app = Flask(__name__)
init_routes(app)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
