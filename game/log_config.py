import logging
import sys
from datetime import datetime

class Formatter(logging.Formatter):
    def format_time(self, record, datefmt=None) -> str:
        now = datetime.fromtimestamp(record.created)
        return f"{now.hour}:{now.minute}:{now.second}"

    def format(self, record) -> str:
        time_str = self.format_time(record)
        return f"[{record.levelname} - {time_str}] {record.filename}:{record.lineno}:{record.funcName} - {record.getMessage()}"

def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(Formatter())

    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.addHandler(ch)