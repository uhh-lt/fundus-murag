import logging
import sys
from pathlib import Path

from loguru import logger

from fundus_murag.config import load_config


class LoguruHandler(logging.Handler):
    def __init__(self, lib_name: str, log_level: str):
        super().__init__()
        self.lib_name = lib_name
        self.log_level = log_level

        # Map logging levels between logging and loguru
        self._levels = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL",
        }

    def emit(self, record):
        level = self._levels.get(record.levelno, self.log_level)

        msg = f"[{self.lib_name}.{record.name}] {record.getMessage()}"

        # Use the loguru logger to log the message
        logger.opt(depth=1).log(level, msg)


def setup_logging():
    cfg = load_config()
    log_dir = Path(cfg.logging_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_level = cfg.logging_level

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS zz}</green> | "
        "<level>{level: <6}</level> | "
        "<yellow>{name}.{module}::{function}::{line}</yellow> "
        "<b>{message}</b>"
    )

    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        format=log_format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    logger.add(
        str(log_dir / "fundus_api_{time}.log"),
        level=log_level,
        format=log_format,
        colorize=False,
        backtrace=True,
        diagnose=True,
    )

    # replace the handlers for the weaviate and httpx loggers
    for lib in ("httpx", "httpcore", "weaviate"):
        lib_logger = logging.getLogger(lib)
        lib_logger.handlers.clear()
        lib_logger.addHandler(LoguruHandler(lib, log_level))
        lib_logger.propagate = False  # Prevent double logging
