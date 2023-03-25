import logging
import config


def create():
    logger = logging.getLogger(__name__)
    f_format = logging.Formatter(config.LOG_FORMAT)
    f_handler = logging.FileHandler(config.LOG_FILE)
    f_handler.setFormatter(f_format)
    logger.setLevel(logging.INFO)
    logger.addHandler(f_handler)
    return logger
