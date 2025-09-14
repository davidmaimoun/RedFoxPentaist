# utils/logger.py
from enum import Enum
import logging
import os
from datetime import datetime
from sqlite3 import DatabaseError

from dev.utils.icons import Icons

class LogType(Enum):
    INFO        = "INFO"
    WARNING     = "WARNING"
    SUCCESS     = "SUCCESS"
    ERROR       = "ERROR"
    PE          = "PE"
    COMMAND     = "COMMAND"
    ANALYZE     = "ANALYZE"
    CONNECT     = "CONNECT"
    PROCESSING  = "PROCESSING"
    PORT        = "PORT"
    KEY         = "KEY"
    DATA        = "DATA"
    WEB         = "WEB"



def log_msg(log: str, type=None, skip_line=False):
    msg = ''
    if skip_line:
        msg += '\n'

    if type == LogType.INFO:
        msg += Icons.INFO + '  '
    elif type == LogType.ERROR:
        msg += Icons.ERROR + '  '
    elif type == LogType.WARNING:
        msg += Icons.WARNING + '  '
    elif type == LogType.SUCCESS:
        msg += Icons.SUCCESS + '  '
    elif type == LogType.PE:
        msg += Icons.FIRE + '  '
    elif type == LogType.COMMAND:
        msg += Icons.TERMINAL + '  '
    elif type == LogType.ANALYZE:
        msg += Icons.ANALYSE + '  ' 
    elif type == LogType.CONNECT:
        msg += Icons.CONNECT + '  '
    elif type == LogType.PROCESSING:
        msg += Icons.GEAR + '  '
    elif type == LogType.PORT:
        msg += Icons.PORT + '  '
    elif type == LogType.KEY:
        msg += Icons.KEY + '  ' 
    elif type == LogType.WEB:
        msg += Icons.WEB + '  ' 
    elif type == LogType.DATA:
        msg += Icons.DATA + '  ' 

    logging.info(f"{msg} {log}")

    print(msg, log)  

