from __future__ import print_function

import pprint
import urllib
from json import dumps
from traceback import format_exc, print_exc

import random
import re

from .config import DEBUG, PYTHON_VERSION
from .thirdparty.loggerglue import rfc5424
from .thirdparty.loggerglue.rfc5424 import *


class ExtenedSysLogFormatter(object):
    """
        IETF-syslog format (see RFC 5424-5428 http://tools.ietf.org/html/rfc5424) with multiline support.
        Turning url_encode resulting logs will be fully RFC 5424-5428 compatible
    """

    def __init__(self, url_encode=False, add_pri=True, escape_rfc5424_special_chars=False, readable_strings=False,
                 json_serializer=None):
        """
        :param url_encode: format will perform url-encoding of MSG and SDATA-VALUE
        :type url_encode: bool
        :param add_pri: format will add <PRI> to result string
        :type add_pri: bool
        :param escape_rfc5424_special_chars: format will escape chars restricted by RFC 5424-5428
        :type escape_rfc5424_special_chars: bool
        """
        self.url_encode = url_encode
        self.add_pri = add_pri
        self.escape_rfc5424_special_chars = escape_rfc5424_special_chars
        self.readable_strings = readable_strings
        self.json_serializer = json_serializer

    MAX_SD_VALUE_LEN = 256 * 1024
    MAX_MSG_LEN = 256
    MAX_STRUCT_LEN = 100

    RECORD_PARAMS = [
        'levelname',
        'funcName',
    ]

    _REPLACE_PRI_RE = re.compile("^<\d+>")

    @classmethod
    def remove_dots(cls, o):
        """
        if routed to ES
        """
        if isinstance(o, dict):
            new = {}
            for k, v in o.iteritems():
                new[k.replace('.', '->')] = cls.remove_dots(v)
            return new
        elif isinstance(o, list):
            return [cls.remove_dots(e) for e in o]
        else:
            return o

    @classmethod
    def _shorten_big_struct(cls, obj):
        if isinstance(obj, dict):
            if len(obj) > cls.MAX_STRUCT_LEN:
                return 'long dict: %s' % len(obj)
            else:
                return dict([(k, cls._shorten_big_struct(v)) for k, v in obj.items()])
        else:
            if isinstance(obj, list):
                if len(obj) > cls.MAX_STRUCT_LEN:
                    return 'long list: %s' % len(obj)
                else:
                    return [cls._shorten_big_struct(i) for i in obj]
            else:
                return obj

    def shorten(self, struct, record):
        if record.levelname == 'CRITICAL' or (hasattr(record, 'shorten') and record.shorten == 0):
            return struct
        else:
            return self._shorten_big_struct(struct)

    def _encode(self, s):
        """
        Method encodes unicode to encoded as utf-8 url-encoded string and inserts \n's in suitable places if
        class configured for readable strings
        :param s: unicode to encode
        :type s: unicode
        :return:
        :rtype: str
        """
        if self.readable_strings and s.find("\n") > -1:
            s = "\n%s\n" % s.strip('\n')
        if self.url_encode:
            return urllib.quote(s)
        else:
            return s

    def _encode_truncate(self, s, limit, record, what):
        """
        Method encodes unicode to encoded as utf-8 url-encoded string and inserts \n's in suitable places if
        class configured for readable strings
        :param s: unicode to encode
        :type s: unicode
        :return:
        :rtype: str
        """
        if limit < 20:
            raise AssertionError('Limit is too short')
        try:
            if not PYTHON_VERSION > (2, 7):
                s = str(s.encode("utf8"))
            else:
                s = str(s)
        except UnicodeDecodeError:
            return 'ERROR_TRUNCATION_UNICODE_DECODE'
        delimiter = ' ... '
        tr_rate = limit // 6
        encoded = self._encode(s)
        if len(encoded) > limit:
            if not hasattr(record, 'truncated'):
                record.truncated = []
            record.truncated.append(what)
            encoded = self._encode(s[:tr_rate] + delimiter + s[-tr_rate:])
            if len(encoded) > limit:
                return 'ERROR_TRUNCATION_LIMIT'
        return encoded

    @classmethod
    def _generate_id(cls, record):
        """
        Generates random id
        :param cls:
        :type cls:
        :param record: src Log.Record
        :type record:
        :return:
        :rtype:
        """
        return "%d%d" % (record.created, random.randint(10 ** 7, 10 ** 8 - 1))

    def _append_json_data(self, default_params, record, path):
        if getattr(record, 'json_data', None) is not None:
            try:
                default_params.append((
                    'json_data',
                    self._encode_truncate(dumps(
                        self.shorten(record.json_data, record), indent=4, cls=self.json_serializer),
                        self.MAX_SD_VALUE_LEN, record, 'json_data'
                    )
                ))
            except Exception:
                print_exc()
                sys.stderr.write("CANT PROCESS JSON DATA ARGUMENT AT: %s\n" % path)

    def _add_trace(self, default_params, record, suffix):
        if record.trace:
            suffix.append(record.trace.split('\n')[-2])
            trace = self._encode_truncate(record.trace, self.MAX_SD_VALUE_LEN, record, 'trace')
            default_params.append(('trace', trace))

    def _format_msg(self, record, suffix):
        return ''.join(self._encode_truncate(
            m, self.MAX_MSG_LEN, record, 'message_%d' % i
        ) for i, m in enumerate([record.getMessage()] + list(map(lambda s: "[%s]" % s, suffix))))

    def _format_sd_default(self, record, suffix):
        skip_encoding = ['json_data', 'trace']
        default_params = []
        path = "%s:%s" % (record.pathname, record.lineno)
        default_params.append(('application', record.application))
        default_params.append(('path', self._encode(path)))
        default_params.append(('user', record.user))
        default_params += [
            (kw, self._encode_truncate(getattr(record, kw), self.MAX_SD_VALUE_LEN, record, kw))
            for kw in self.RECORD_PARAMS if kw not in skip_encoding and hasattr(record, kw)
            # and getattr(record, kw) is not None
        ]
        self._append_json_data(default_params, record, path)
        self._add_trace(default_params, record, suffix)
        if hasattr(record, 'repr'):
            dumped = pprint.pformat(self.shorten(record.repr, record))
            default_params.append(('repr', self._encode_truncate(dumped, self.MAX_SD_VALUE_LEN, record, 'repr')))
        if record.stack is not None:
            default_params.append(('stack',
                                   self._encode_truncate(record.stack, self.MAX_SD_VALUE_LEN, record, 'stack')))
        if hasattr(record, 'truncated'):
            default_params.append(('truncated', repr(record.truncated)))
        return SDElement("default", default_params)

    def _format(self, record):
        """
        Method formats log message according to IETF logs format
        :param record:
        :type record: logging.LogRecord
        :return: formatted message with removed <pri> part, because syslog driver do this
        :rtype: str
        """
        if DEBUG:
            sys.stderr.write("\nDEBUG: Formatting log record: %s\n" % record)
        suffix = []
        se = SyslogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            hostname=record.hostname,
            app_name=record.application,
            procid=record.process,
            msgid="MSGID" + self._generate_id(record),
            structured_data=StructuredData([
                self._format_sd_default(record, suffix),
                # self._format_sd_aggregation(record)
            ]),
            msg=self._format_msg(record, suffix)
        )
        if not record.getMessage():
            sys.stderr.write("\nERROR: Got log line %s without message" % msgid)
            ret = str(se)
        else:
            ret = str(se)
        if not self.add_pri:
            # because this is the easiest way to deal with SysLogHandler
            # because it adds <pri> when emit message
            ret = self._REPLACE_PRI_RE.sub("", str(se), count=1)
        if DEBUG:
            print("DEBUG: Formatted log is: %s" % ret, file=sys.stderr)
        return ret

    def format(self, record):
        try:
            if not self.escape_rfc5424_special_chars:
                rfc5424.ESCAPE_SDATA_VALUES = False
            formatted = self._format(record)
            rfc5424.ESCAPE_SDATA_VALUES = True
        except Exception:
            print("Unable to format log record %r %s" % (record.__dict__, format_exc()), file=sys.stderr)
            return ''
        else:
            return formatted


class ColoredSyslogFormatter(ExtenedSysLogFormatter):
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    # The background is set with 40 plus the number of the color, and the foreground with 30

    # These are the sequences need to get colored ouput
    RESET_SEQ = "\033[0m"
    COLOR_SEQ = "\033[1;%dm"
    BOLD_SEQ = "\033[1m"

    @classmethod
    def formatter_message(cls, message, use_color=True):
        if use_color:
            message = message.replace("$RESET", cls.RESET_SEQ).replace("$BOLD", cls.BOLD_SEQ)
        else:
            message = message.replace("$RESET", "").replace("$BOLD", "")
        return message

    COLORS = {
        'WARNING': MAGENTA,
        'INFO': GREEN,
        'DEBUG': BLUE,
        'CRITICAL': RED,
        'ERROR': YELLOW
    }

    def __init__(self, json_serializer=None):
        ExtenedSysLogFormatter.__init__(
            self, url_encode=False, add_pri=True, escape_rfc5424_special_chars=False, readable_strings=True,
            json_serializer=json_serializer
        )

    def format(self, record):
        levelname = record.levelname
        formatted = ExtenedSysLogFormatter.format(self, record)[2:]
        if levelname in self.COLORS:
            formatted = self.COLOR_SEQ % (30 + self.COLORS[levelname]) + formatted + self.RESET_SEQ
        formatted += '\n'
        return formatted


class ELKJsonFormatter(object):
    """
    Json ELK formatter supporting extended ops logging attributes
    """

    def __init__(self, json_serializer=None):
        """
        :param json_serializer:
        :type json_serializer: object
        """
        self.json_serializer = json_serializer

    def _format(self, record):
        log_struct = dict(
            timestamp=datetime.fromtimestamp(record.created).strftime('%Y-%m-%dT%H:%M:%S+0000'),
            hostname=record.hostname,
            app_name=record.application,
            procid=record.process,
            message=record.getMessage(),
            path="%s:%s" % (record.pathname, record.lineno),
            application=record.application,
            levelname=record.levelname,
            funcName=record.funcName
        )
        if getattr(record, 'json_data', None) is not None:
            log_struct['json_data'] = record.json_data
        if hasattr(record, 'repr'):
            log_struct['repr'] = pprint.pformat(record.repr)
        if record.stack is not None:
            log_struct['stack'] = record.stack
        if record.trace:
            log_struct['trace'] = record.trace
        if not record.getMessage():
            sys.stderr.write("\nERROR: Got log line %s without message" % msgid)
        return dumps(log_struct, cls=self.json_serializer)

    def format(self, record):
        try:
            formatted = self._format(record)
        except Exception:
            print("Unable to format log record %r %s" % (record.__dict__, format_exc()), file=sys.stderr)
            return ''
        else:
            return formatted
