import os
import socket
import sys
import pwd
from logging import Logger
from traceback import format_stack, format_exc

from .config import LoggingConfig


class OpsLogger(Logger):
    """
    Redefines Logger _log method to add ability write an arbitrary kw arguments in log.xxx() method
    """
    SUPPORTED_KW_ARGS = [
        'trace',
        'notify',
        'json_data',
        'repr',
        'stack',
        'shorten',
        'oes'
    ]

    @classmethod
    def get_stack(cls):
        stack = []
        for l in format_stack():
            stack.append(l)
            if 'stack=1' in l:
                break
        return stack

    def _add_stack(self):
        stack = self.get_stack()
        formatted_stack = ''.join(stack)
        return formatted_stack

    def _add_trace(self, trace):
        if isinstance(trace, (tuple, list)):
            trace = '\n'.join(trace)
        else:
            trace = format_exc()
        return trace

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        if extra is None:
            extra = {}
        extra.update({
            'user': pwd.getpwuid(os.getuid()).pw_name if os.getuid() else 'root',
            'application': LoggingConfig.DEFINED_SERVICE,
            'hostname': socket.gethostname(),
            'session_id': LoggingConfig.SESSION_ID,
            'stack': self._add_stack() if extra.get('stack', 0) == 1 else None,
            'trace': self._add_trace(extra.get('trace')) if extra.get('trace', 0) == 1 else None,
        })
        return Logger.makeRecord(self, name, level, fn, lno, msg, args, exc_info, func, extra)

    def exception(self, msg, *args, **kwargs):
        self.error(msg, trace=1, *args, **kwargs)

    def _log(self, level, msg, args, exc_info=None, extra=None, **kwargs):
        """
        Low-level src routine which creates a LogRecord and then calls
        all the handlers of this logger to handle the record.
        """
        if extra is None:
            extra = {}
        for k in kwargs:
            if k not in self.SUPPORTED_KW_ARGS:
                sys.stderr.write("\nERROR: '%s' is not supported src arg\n"
                                 "try to use the following system kw arguments: %s" % (k, self.SUPPORTED_KW_ARGS))
                exit(1)
        extra.update(kwargs)
        Logger._log(self, level, msg, args, exc_info, extra)
