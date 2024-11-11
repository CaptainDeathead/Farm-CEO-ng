# Source: ChatGPT
import logging

from data import BUILD
if not BUILD: from colorama import Fore, Style, init

import sys

# Initialize colorama
if not BUILD: init(autoreset=True)

class Formatter(logging.Formatter):
    def format(self, record):
        record.levelname = record.levelname[0]

        # Format the log message with color and timestamp
        log_fmt = (
            f"[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: "
            f"%(message)s"
        )
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)

if not BUILD:
    class ColoredFormatter(logging.Formatter):
        COLORS = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.MAGENTA,
        }

        def format(self, record):
            # Get the color based on the log level
            log_color = self.COLORS.get(record.levelname, Fore.WHITE)

            record.levelname = record.levelname[0]

            # Format the log message with color and timestamp
            log_fmt = (
                f"{log_color}[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: "
                f"%(message)s{Style.RESET_ALL}"
            )
            formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
            return formatter.format(record)

def setup_logging():
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set root level to DEBUG or any desired level
    
    # Check if there are no handlers (prevents duplicate handlers)
    if not logger.hasHandlers():
        # Set up console handler with colorized formatter
        console_handler = logging.StreamHandler(sys.stdout)

        print(BUILD)
        if BUILD: console_handler.setFormatter(Formatter())
        else: console_handler.setFormatter(ColoredFormatter())

        logger.addHandler(console_handler)

# Call setup_logging once when the application starts
setup_logging()
