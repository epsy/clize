import logging

from sigtools import wrappers
from clize import run, parser, util


levels = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NOTSET': logging.NOTSET
}


@parser.value_converter
def loglevel(arg):
    try:
        return int(arg)
    except ValueError:
        try:
            return levels[arg.upper()]
        except KeyError:
            raise ValueError(arg)


class LogLevelParameter(parser.FlagParameter):
    def __init__(self, conv, value=logging.INFO, **kwargs):
        super(LogLevelParameter, self).__init__(
            conv=loglevel, value=value, **kwargs)

    def help_parens(self):
        if self.default is not util.UNSET:
            for k, v in levels.items():
                if v == self.default:
                    default = k
                    break
            else:
                default = self.default
            yield 'default: {0}'.format(default)


log_level = parser.use_class(named=LogLevelParameter)


def try_log(logger):
    logger.debug("Debug")
    logger.info("Info")
    logger.warning("Warning")
    logger.error("Error")
    logger.critical("Critical")


@wrappers.decorator
def with_logger(wrapped, *args, log:log_level=logging.CRITICAL, **kwargs):
    """
    Logging options:

    :param log: The desired log level"""
    logger = logging.getLogger('myapp')
    logger.setLevel(log)
    logger.addHandler(logging.StreamHandler())
    return wrapped(*args, logger=logger, **kwargs)


@with_logger
def main(*, logger):
    """Tries out the logging system"""
    try_log(logger)


run(main)
