import logging
from typing import Optional


def getLogger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Simply returns a standard logger."""
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(name)s %(levelname)s %(message)s")
    level = level or logging.INFO

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
