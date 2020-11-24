import os
import sys
import logging as _python_logging

from .logger import OpsLogger

PYTHON_VERSION = sys.version_info[0], sys.version_info[1]
DEBUG = bool(os.environ.get('LOGS_DEBUG'))
VERSION = '@PKG_VERSION'


if _python_logging.getLoggerClass() is not OpsLogger:
    _python_logging.setLoggerClass(OpsLogger)
    if PYTHON_VERSION > (2, 6):
        _python_logging.root = OpsLogger("root")


def configure_logs(configuration=None):
    """
    Method configures Ops Logs with configuration parameter if specified
    Else do nothing, just updates root logger with OpsLogger class
    :return: None
    :rtype: NoneType
    """

    from .config import LoggingConfig
    if configuration is not None:
        if DEBUG:
            sys.stderr.write("\nDEBUG: Configuring logs from passed configuration:\n%s\n" % configuration)
        LoggingConfig(configuration).configure()
