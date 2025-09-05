# utils/logger.py
from enum import Enum
import logging
import os
from datetime import datetime

class LogType(Enum):
    INFO = "INFO"
    IMPORTANT = "IMPORTANT"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

os.makedirs("logs", exist_ok=True)

# Configuration du logger avec timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/log_{timestamp}.log"

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def log_msg(msg: str, type: LogType = LogType.INFO, print_console=True):
    logging.info(msg)
    if not print_console:
        return
    print(f"[{type.value}] {msg}")  

