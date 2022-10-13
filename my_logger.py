import logging
import sys

from pythonjsonlogger import jsonlogger


def get_logger(name=None, level=logging.INFO, format='%(asctime)s %(name)s {%(filename)s %(lineno)d} %(levelname)s - %(message)s'):
    logger = logging.getLogger(name)

    if not hasattr(logger, 'is_stdout_handler_configured'):
        logger.setLevel(level)
        logger.is_stdout_handler_configured = True

        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        if format:
            stdout_handler.setFormatter(jsonlogger.JsonFormatter(format))
        else:
            stdout_handler.setFormatter(logging.Formatter('%(message)s'))
        stdout_handler.setLevel(level)

        logger.addHandler(stdout_handler)

    return logger
