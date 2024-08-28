import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.DEBUG, log_file='app.log', max_bytes=10**6, backup_count=5):
    """
    Sets up the logging configuration with rotation.

    :param log_level: The logging level (e.g., DEBUG, INFO)
    :param log_file: The file to write logs to
    :param max_bytes: The maximum file size before rotation (in bytes)
    :param backup_count: The number of backup files to keep
    """
    # Create a custom logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Check if handlers are already set up to avoid adding multiple handlers
    if not logger.handlers:
        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)

        # Set levels for handlers
        console_handler.setLevel(logging.INFO)
        file_handler.setLevel(logging.DEBUG)

        # Create formatters and add them to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to the logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

# Configure logging when the module is imported
setup_logging()
