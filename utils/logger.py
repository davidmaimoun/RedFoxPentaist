# utils/logger.py
from enum import Enum
import logging
import os

class LogType(Enum):
    INFO = "INFO"
    IMPORTANT = "IMPORTANT"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

os.makedirs("logs", exist_ok=True)

# Configuration du logger
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def log_msg(msg: str, type: LogType = LogType.INFO, gui=None):
    if gui:
        if type == LogType.INFO:
            gui.info(msg)
        elif type == LogType.IMPORTANT:
            gui.warning(msg)
        elif type == LogType.SUCCESS:
            gui.success(msg)
        elif type == LogType.ERROR:
            gui.error(msg)

    print(f"[{type.value}] {msg}")  
    logging.info(msg)

