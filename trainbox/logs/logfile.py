import logging, logging.config
import os
import datetime


def beijing(sec, what):
    beijing_time = datetime.datetime.now() + datetime.timedelta(hours=8)
    return beijing_time.timetuple()

logging.Formatter.converter = beijing
log_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'logger.conf')
logging.config.fileConfig(log_config_path)

debugLogger = logging.getLogger()
errorLogger = logging.getLogger(name='errorLogger')
infoLogger = logging.getLogger(name='infoLogger')
