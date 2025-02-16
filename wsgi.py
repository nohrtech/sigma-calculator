import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the application directory to the Python path
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)
logger.info(f"Added to Python path: {app_dir}")

try:
    from app import app
    logger.info("Successfully imported app")
except Exception as e:
    logger.error(f"Failed to import app: {str(e)}")
    logger.error(f"Python path: {sys.path}")
    raise

# Initialize the app if needed
if hasattr(app, 'init_app'):
    app.init_app()
    logger.info("Initialized app")

if __name__ == "__main__":
    app.run()
