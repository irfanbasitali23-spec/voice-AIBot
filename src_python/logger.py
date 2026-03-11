import os
import logging
from logging.handlers import RotatingFileHandler
from src_python.config import config

LOG_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "error": logging.ERROR,
}

def setup_logger():
    level = LOG_LEVEL_MAP.get(config["logging"]["level"], logging.INFO)

    logger = logging.getLogger("voice-ai-patient-registration")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Combined log file
    combined_handler = RotatingFileHandler(
        "logs/combined.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )
    combined_handler.setLevel(level)
    combined_handler.setFormatter(formatter)
    logger.addHandler(combined_handler)

    # Error log file
    error_handler = RotatingFileHandler(
        "logs/error.log", maxBytes=5 * 1024 * 1024, backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


logger = setup_logger()
