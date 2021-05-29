import logging
from logging.handlers import TimedRotatingFileHandler

LOG_FORMAT = "%(asctime)s - %(threadName)-11s - [%(levelname)s] - %(message)s"
logFormatter = logging.Formatter(LOG_FORMAT)
rootLogger = logging.getLogger()
rootLogger.level = logging.INFO

# fileHandler = logging.FileHandler("WRPI.log")
fileHandler = TimedRotatingFileHandler("WRPI.log", encoding='utf-8', when='midnight',backupCount=0)
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

