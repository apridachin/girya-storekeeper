import datetime
import json
import logging

from backend.utils.config import get_settings


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
            'level': record.levelname,
            'message': record.getMessage()
        }

        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                          'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated',
                          'stack_info', 'thread', 'threadName']:
                log_entry[key] = value

        if record.exc_info:
            log_entry['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logger(name: str = "app") -> logging.Logger:
    """Set up a logger with JSON formatting."""
    settings = get_settings()
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    logger.handlers.clear()
    logger.addHandler(handler)
    
    logger.propagate = False
    
    return logger

logger = setup_logger()
