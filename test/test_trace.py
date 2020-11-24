
from logging import getLogger
import json

import ext_logging
from . import BaseTestCase, log, key_error, grep_line_nr

FILENAME = __file__
INIT_FILENAME = '/'.join(FILENAME.split('/')[:-1] + ['__init__.py'])
TRACE = """Traceback (most recent call last):
  File "%s", line %%s, in %%s
    key_error()
  File "%s", line %%s, in key_error
    dict()['nokey']  # KeyError
KeyError: 'nokey'
""" % (FILENAME, INIT_FILENAME)


ERROR_LINE_NR = grep_line_nr(INIT_FILENAME, '# KeyError')


class TraceCase(BaseTestCase):

    def test_log_trace_eq_1(self):
        """Log trace with trace=1"""
        try:
            key_error()
        except Exception:  # Use this line number - 1 as line_nr to format TRACE Line:2
            log.error('Ooops', trace=1)

        line_nr = grep_line_nr(FILENAME, 'Line:2') - 1
        fn_name = 'test_log_trace_eq_1'
        self.log_assert.msg_equal('Ooops')
        self.log_assert.attr_equal('trace', TRACE % (line_nr, fn_name, ERROR_LINE_NR))

    def test_log_trace_eq_0(self):
        """Do not log trace with trace=0"""
        try:
            key_error()  # Use this line number as line_nr to format TRACE
        except Exception:
            log.error('Ooops', trace=0)

        self.log_assert.msg_equal('Ooops')
        self.log_assert.attr_equal('trace', '')

    def test_json_serialization_for_stdout_accepted(self):
        log_conf = {
            'handler': 'ext_logging.handlers.StdOutExtendedSysLogHandler',
            'level': 'DEBUG',
            'json_serializer': json.JSONEncoder,

        }
        ext_logging.configure_logs({
            'MODULES': {
                '': log_conf,
                'test': log_conf,
            }
        })
        log.info('here test', json_data={'this': {'does not': 'fail'}})

    def test_multiple_handlers(self):
        log_conf1 = {
            'handler': 'ext_logging.handlers.StdOutExtendedSysLogHandler',
            'level': 'DEBUG',
            'json_serializer': json.JSONEncoder,

        }
        log_conf = {
            'handler': 'ext_logging.handlers.StdOutExtendedSysLogHandler',
            'level': 'DEBUG',
            'json_serializer': json.JSONEncoder,

        }
        ext_logging.configure_logs({
            'MODULES': {
                '': log_conf,
                'test': log_conf,
            }
        })
        log.info('here test', json_data={'this': {'does not': 'fail'}})
