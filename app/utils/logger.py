"""
Centralized logging setup with Rich for beautiful terminal output.
"""
import logging
from rich.logging import RichHandler


def setup_logger():
    """Configure the root logger with Rich for production-style output."""
    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )

    # Quieten noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger("bible-api")
    logger.info("📋 Logger initialized")
    return logger
