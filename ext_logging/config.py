import os
import random
import sys
import traceback
import logging
import logging.handlers
from traceback import print_exc

PYTHON_VERSION = sys.version_info[0], sys.version_info[1]
DEBUG = bool(os.environ.get('LOGS_DEBUG'))


class LoggingConfig(object):
    """
    Configure loggers according Ops Logs
    """

    CONFIGURATION = {}
    DEFINED_SERVICE = None
    SESSION_ID = None

    def __init__(self, configuration, service=None):
        """
        Method configures Logs
        :param configuration: LOGGING dict
        :type configuration: dict
        :param service: Name of service that executes. If not specified - name of started script will be specified
        :type service: str
        :return: None
        :rtype: NoneType
        """
        self.configuration = configuration
        if service is not None:
            self.service = service
        else:
            self.service = self.define_service()

    def _clean_configuration(self):
        """
        Method removes previously configured handlers
        :return:None
        :rtype:NoneType
        """
        previous_loggers = self.configuration.keys()
        if len(previous_loggers) > 0:
            for logger_name in previous_loggers:
                logger = logging.getLogger(logger_name)
                for handler in logger.handlers:
                    stream = getattr(handler, 'stream', None)
                    if stream and stream not in (sys.stdout, sys.stderr):
                        try:
                            stream.close()
                        except (ValueError, IOError):
                            pass
                        handler.stream = None
                    try:
                        handler.close()
                    except Exception as e:
                        print("_clean_configuration() exception occured while closing handler: %s" % e)

                    logger.removeHandler(handler)

    def configure(self):
        """
            Configure loggers using a LOGGING style dictionary. If configuring is success - CONFIGURATION will
            be updated configuring process performed only once for constant configuration.
        """
        if LoggingConfig.CONFIGURATION != self.configuration:
            self._clean_configuration()
            logger = logging.getLogger()
            # must have at least one handler

            # logger.addHandler(logging.NullHandler())
            # logging.basicConfig()
            logger.propagate = False

            for logger_label, configs in self.configuration['MODULES'].items():
                if not isinstance(configs, list):
                    configs = [configs]
                for config in configs:
                    config = config.copy()

                    if logger_label:
                        _logger = logging.getLogger(logger_label)
                    else:
                        _logger = logging.getLogger()

                    level = config.pop('level', 'DEBUG')
                    if level is not None:
                        # python versions here
                        if PYTHON_VERSION <= (2, 6):
                            _logger.setLevel(logging._levelNames[level] if isinstance(level, str) else level)
                        else:
                            _logger.setLevel(level)
                    disabled = config.pop('disabled', None)
                    if disabled is not None:
                        _logger.disabled = disabled

                    handler = config.pop('handler', None)
                    if handler is not None:
                        klass = self.handler_from_string(handler)
                        # format setted for only non empty handler in configuration
                        formatter = config.pop('formatter', None)
                        handler_obj = klass(**config)
                        if formatter:
                            formatter_obj = logging.Formatter(formatter, '%Y-%m-%d %H:%M:%S')
                            handler_obj.setFormatter(formatter_obj)
                        _logger.addHandler(handler_obj)
            LoggingConfig.CONFIGURATION = self.configuration

    @staticmethod
    def handler_from_string(string):
        """
        Method loads handler classes specified in string
        :param string: Name of class
        :type string: str
        :return: Handler class
        :rtype: class
        """
        try:
            dot = string.rindex('.')
        except ValueError:
            raise ImportError('%s isn\'t a handler module' % string)
        module, classname = string[:dot], string[dot + 1:]
        try:
            __import__(module)
            mod = sys.modules[module]
        except ImportError as e:
            print_exc()
            raise ImportError('Error importing handler %s: "%s"' % (module, e))
        try:
            klass = getattr(mod, classname)
        except AttributeError:
            raise ImportError('Module "%r" does not define a "%s" class' % (module, classname))
        return klass

    @staticmethod
    def define_service():
        """
            Get name of executed process
            Assume that we didn't pass log records between processes
        """
        if LoggingConfig.DEFINED_SERVICE is None:
            LoggingConfig.DEFINED_SERVICE = traceback.extract_stack()[0][0].split('/')[-1]
            LoggingConfig.SESSION_ID = hex(random.randrange(2**255, 2**256))[2:]
        return LoggingConfig.DEFINED_SERVICE

