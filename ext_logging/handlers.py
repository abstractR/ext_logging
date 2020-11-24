import atexit
import time
import logging
import socket
import threading
import os
import pwd
import sys


from json import dumps
from logging import Handler
from logging.handlers import HTTPHandler, WatchedFileHandler
from multiprocessing import Queue

from .formatters import ELKJsonFormatter
from .formatters import ExtenedSysLogFormatter, ColoredSyslogFormatter
from .config import LoggingConfig

log = logging.getLogger(__name__)


class ConcurrentFileExtendedSysLogHandler(WatchedFileHandler):
    """
        The message corresponds to the following format:

        <priority>VERSION ISOTIMESTAMP HOSTNAME APPLICATION PID MESSAGEID STRUCTURED-DATA MSG
    """

    def __init__(self, filename, mode='a', encoding=None, delay=0, formatter=None, json_serializer=None):
        WatchedFileHandler.__init__(self, filename, mode, encoding, delay)
        if not formatter:
            formatter = ExtenedSysLogFormatter(json_serializer=json_serializer)
        self.formatter = formatter



class StdOutExtendedSysLogHandler(logging.StreamHandler):
    FORMAT = "[$BOLD%(name)-20s$RESET][%(levelname)-18s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
    COLOR_FORMAT = ColoredSyslogFormatter.formatter_message(FORMAT, True)

    def __init__(self, stream=None, json_serializer=None):
        if not stream:
            stream = sys.stdout
        logging.StreamHandler.__init__(self, stream)
        self.formatter = ColoredSyslogFormatter(json_serializer=json_serializer)
