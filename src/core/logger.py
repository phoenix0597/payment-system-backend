from loguru import logger
import sys


def setup_logger():
    # Удаляем стандартный обработчик и добавляем кастомный
    logger.remove()
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}",
        level="INFO",
    )
    logger.add(
        "logs/app.log",
        rotation="1 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} |  {message}",
        level="DEBUG",
    )
    return logger


log = setup_logger()
