
from logging import getLogger
from . import BaseTestCase, log


class SimpleCase(BaseTestCase):

    def test_debug(self):
        msg = 'This is debug'
        log.debug(msg)
        self.log_assert.msg_equal(msg)

    def test_info(self):
        msg = 'This is info'
        log.info(msg)
        self.log_assert.msg_equal(msg)

    def test_warning(self):
        msg = 'This is warning'
        log.warning(msg)
        self.log_assert.msg_equal(msg)

    def test_error(self):
        msg = 'This is error'
        log.error(msg)
        self.log_assert.msg_equal(msg)
