import json
import errno
import os

import ext_logging
from . import BaseTestCase, log


class TraceCase(BaseTestCase):

    def test_multiple_handlers(self):

        log_conf_sysl = {
            'handler': 'ext_logging.handlers.StdOutExtendedSysLogHandler',
            'level': 'DEBUG',
            'json_serializer': json.JSONEncoder,

        }
        log_conf_elk = {
            'handler': 'ext_logging.handlers.ELKFileHandler',
            'level': 'DEBUG',
            'json_serializer': json.JSONEncoder,
            'elkdir': '.'

        }
        ext_logging.configure_logs({
            'MODULES': {
                'test': [log_conf_sysl, log_conf_elk],
            }
        })
        log.info('here test', json_data={'this': {'does not': 'fail'}})
