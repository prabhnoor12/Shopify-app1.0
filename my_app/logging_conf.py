import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging():
    """Configures a robust logger for the application."""
    log_file_path = "app.log"

    # Create the logging directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Use a rotating file handler to prevent log files from getting too large
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file_path),
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=5,  # Keep up to 5 files
    )

    # Create a formatter for the log messages
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    # Get the root logger and set its level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Add the file handler to the root logger
    root_logger.addHandler(file_handler)

    # Also add a console handler for local development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
