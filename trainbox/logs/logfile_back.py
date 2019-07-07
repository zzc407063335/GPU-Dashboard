# -*- coding: utf-8 -*-

import logging, logging.config
import os,sys
import datetime

error_filename = os.environ.get('ERROR_LOGGER_FILE')
info_filename = os.environ.get('INFO_LOGGER_FILE')

def beijing(sec, what):
    beijing_time = datetime.datetime.now() + datetime.timedelta(hours=8)
    return beijing_time.timetuple()

logging.Formatter.converter = beijing
# log_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'logger.conf')
# logging.config.fileConfig(log_config_path)
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(module)s - %(process)d - %(levelname)s : %(message)s ---> [%(filename)s:%(lineno)s %(funcName)s]',
                    datefmt='%Y-%m-%d %H:%M:%S')

simpleFormatter = logging.Formatter(fmt='%(asctime)s - %(module)s - %(process)d - %(levelname)s : %(message)s ---> [%(filename)s:%(lineno)s %(funcName)s]',
                         datefmt='%Y-%m-%d %H:%M:%S')

consoleHandler = logging.StreamHandler(stream=sys.stdout)
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(simpleFormatter)

fileHandler = logging.handlers.RotatingFileHandler(
                    filename=error_filename,mode='a',
                    maxBytes=1*1024*1024,backupCount=14)
fileHandler.setLevel(logging.ERROR)
fileHandler.setFormatter(simpleFormatter)

timeRotatingFileHandler = logging.handlers.TimedRotatingFileHandler(
    filename=info_filename, when='midnight',interval=1,backupCount=14)
timeRotatingFileHandler.setLevel(logging.INFO)
timeRotatingFileHandler.setFormatter(simpleFormatter)

debugLogger = logging.getLogger()
# debugLogger.addHandler(consoleHandler)
debugLogger.propagate = True

errorLogger = logging.getLogger(name='errorLogger')
errorLogger.setLevel(logging.ERROR)
errorLogger.addHandler(fileHandler)
errorLogger.propagate = False

infoLogger = logging.getLogger(name='infoLogger')
infoLogger.setLevel(logging.INFO)
infoLogger.addHandler(timeRotatingFileHandler)
infoLogger.propagate = False

