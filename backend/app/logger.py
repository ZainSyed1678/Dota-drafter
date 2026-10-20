import json
import logging
import sys
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Formats log records as structured key-value or JSON strings."""
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        base = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        if hasattr(record, "props"):
            base.update(record.props)
        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)
        return json.dumps(base)


def get_logger(name: str = "dota-api") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger
