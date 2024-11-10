"""Utility functions to handle logging in the whole project."""

import logging
from datetime import datetime
from pathlib import Path

from src.constants import LOGS

# Spawn formatter and handler as a singleton to avoid repeated logs if calling `get_logger` from
# multiple modules
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s -  %(funcName)s.%(lineno)d - %(message)s"
)
console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel("INFO")

file = logging.FileHandler(LOGS / f"{datetime.now().isoformat()}.log")
file.setFormatter(formatter)
file.setLevel("DEBUG")

logging.captureWarnings(capture=True)


def get_logger(file_or_name: str, level: str = "INFO") -> logging.Logger:
    """Gets a logger with the given name or one derived from the given file path.

    Usually, you'll call this method like `get_logger(__file__)`, and the logger's name will be the
    file's stem.

    Args:
        file_or_name (str): The full name of the logger or a path-like `str`, whose stem will be
            used to name the logger.
        level (str, optional): The level of the logger. Defaults to "INFO".

    Returns:
        logging.Logger: A logger with the correct name and level set.
    """
    name = Path(file_or_name).stem
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Add the handlers if they are not already added
    if not logger.hasHandlers():
        logger.addHandler(console)
        logger.addHandler(file)

    return logger
