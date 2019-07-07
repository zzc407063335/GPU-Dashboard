# -*- coding: utf-8 -*-

# 定义一些任务请求组件和中间件的接口数据
import os


# PROTOCOL = 'http://'
# SERVER_IP = '172.18.0.1'

PROTOCOL = os.environ.get('CONNECT_PROTOCOL')
SERVER_IP = os.environ.get('SERVER_IP')
SERVER_PORT = os.environ.get('SERVER_PORT')
USER_NAME = os.environ.get('USER_NAME')# "zzczzc"
USER_PASS = os.environ.get('USER_PASS')# "zzc997997"
LOCAL_PORT = os.environ.get('LOCAL_PORT')
TASK_COUNTS_MAX = int(os.environ.get('TASK_COUNTS_MAX'))
CURRENT_UID = os.environ.get('CURRENT_UID')
HOME_DIR = os.environ.get('HOME_DIR')
APP_HOME_DIR = os.environ.get('APP_HOME_DIR')
# PROTOCOL= 'http://'
# SERVER_IP= 'www.tsingtsingai.com'
# SERVER_PORT= 8000
# USER_NAME= 'username'
# USER_PASS= 'password'
# LOCAL_PORT= 8997
# TASK_COUNTS_MAX = 5

QUERY_INTERVAL = 5
TIME_OUT = 24*60*60*7

# LOCAL_DATA_DIR = '/data' 
# LOCAL_RESULT_DIR = 'result'
# LOCAL_TASKS_DIR = '/tasks' 
# LOG_INFO_NAME = 'info.log'
# LOG_ERROR_NAME = 'error.log'

LOCAL_DATA_DIR = os.path.join(APP_HOME_DIR,'data')
LOCAL_RESULT_DIR = 'result'
LOCAL_TASKS_DIR = os.path.join(APP_HOME_DIR,'tasks')
LOCAL_LOGS_DIR = os.path.join(APP_HOME_DIR,'logs')
LOG_INFO_NAME = 'info.log'
LOG_ERROR_NAME = 'error.log'

REGISTER_GPU_COUNT = 0
