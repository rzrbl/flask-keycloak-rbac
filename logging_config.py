from logging.handlers import RotatingFileHandler
import logging

def setup_logging(log_level, log_file):
    logging_level = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    log_level = logging_level.get(log_level, logging.INFO)

    file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=3)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
