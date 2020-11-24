
import ext_logging

log_conf = {
    'handler': 'ext_logging.handlers.StdOutExtendedSysLogHandler',
    'level': 'DEBUG',
}

ext_logging.configure_logs({
    'MODULES': {
        '': log_conf,
        'test': log_conf,
    }
})

from logging import getLogger
from logging.handlers import BufferingHandler
from unittest import TestCase

log = getLogger(__name__)

MSG = """Value of attribute '%s' differs from expectation:
============== PROVIDED ===============
%s
============== EXPECTED ===============
%s
======================================="""

def key_error():
    dict()['nokey']  # KeyError


class AssertingHandler(BufferingHandler):

    def __init__(self, test_case, capacity=50):
        BufferingHandler.__init__(self, capacity)
        self.test_case = test_case

    def msg_equal(self, msg):
        for record in self.buffer:
            line = self.format(record)
            if line == msg:
                return
        self.test_case.assertTrue(False, 'Failed to find log message: %s' % msg)

    def attr_equal(self, attr, value):
        for record in self.buffer:
            line = getattr(record, attr, '') or ''
            if line == value:
                return
        self.test_case.assertTrue(False, MSG % (attr, value, line))


class BaseTestCase(TestCase):

    def setUp(self):
        self.log_assert = AssertingHandler(self)
        log.addHandler(self.log_assert)

    def tearDown(self):
        log.removeHandler(self.log_assert)


def grep_line_nr(filename, pattern):
    with open(filename) as filehandle:
        for number, line in enumerate(filehandle):
            if pattern in line:
                return number + 1
