import sys
import os
import logging
from . import constants

LOGGER_INSTANCE = logging.getLogger(constants.BRAND)

debug = LOGGER_INSTANCE.debug
info = LOGGER_INSTANCE.info
warning = LOGGER_INSTANCE.warning
warn = LOGGER_INSTANCE.warn
error = LOGGER_INSTANCE.error
critical = LOGGER_INSTANCE.critical


def create_setup_logger(name: str = None, log_file: str = "", log_level=logging.DEBUG):
    if name:
        logger = logging.getLogger(name)

    else:
        logger = logging.getLogger()

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        except:
            pass
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.addHandler(stdout_handler)
    logger.setLevel(log_level)

    return logger


def setup_logger(log_file: str = "", log_level=logging.DEBUG):
    create_setup_logger(constants.BRAND, log_file, log_level)


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_unhandled_exception
