from app.logging import DEFAULT_LOG_FILE as LOG_FILE
from app.logging import logger


def log(message: str) -> None:
    logger.info(message)
