import os
import logging
from config.settings import settings

current_dir_name = os.path.basename(os.path.abspath(os.path.dirname(__file__)))
logger = logging.getLogger(current_dir_name)

logger.setLevel(settings.LOG_LEVEL)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.propagate = False

# Example usage:
#  from logger import logger
logger.debug('Logger started.')