from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from loguru import logger

from app.config import DATA_DIR

DEFAULT_LOG_FILE = DATA_DIR / "logs" / "sis-book.log"

_configured = False
_current_log_file = DEFAULT_LOG_FILE


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 0
        while frame and frame.f_code.co_filename in (logging.__file__, __file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(
    log_file: Path | None = None,
    *,
    level: str | None = None,
    force: bool = False,
) -> Path:
    global _configured, _current_log_file
    if _configured and not force:
        return _current_log_file

    resolved_level = (level or os.getenv("SIS_BOOK_LOG_LEVEL") or "INFO").upper()
    resolved_log_file = log_file or DEFAULT_LOG_FILE
    resolved_log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            level=resolved_level,
            colorize=True,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level:<8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
        )

    logger.add(
        resolved_log_file,
        level=resolved_level,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        serialize=True,
        backtrace=True,
        diagnose=False,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        std_logger = logging.getLogger(logger_name)
        std_logger.handlers.clear()
        std_logger.propagate = True

    _configured = True
    _current_log_file = resolved_log_file
    logger.bind(log_file=str(resolved_log_file)).debug("日志系统已配置")
    return resolved_log_file


configure_logging()

__all__ = ["DEFAULT_LOG_FILE", "configure_logging", "logger"]
