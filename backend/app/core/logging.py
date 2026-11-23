"""Structured logging configuration."""
import logging
import sys
from app.core.config import settings


def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Custom filter to strip sensitive data
    class SensitiveDataFilter(logging.Filter):
        SENSITIVE_KEYWORDS = {"password", "token", "secret", "key", "credential", "auth"}

        def filter(self, record: logging.LogRecord) -> bool:
            msg = str(record.getMessage()).lower()
            for keyword in self.SENSITIVE_KEYWORDS:
                if keyword in msg:
                    record.msg = "[REDACTED - message contained sensitive data]"
                    record.args = ()
            return True

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Silence noisy libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
