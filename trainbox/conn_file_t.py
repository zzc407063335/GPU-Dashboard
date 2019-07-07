# -*- coding: utf-8 -*-

# 定义一些训练组件和中间件的接口数据
import os

USER_NAME = os.environ.get('USER_NAME')# "zzczzc"
USER_PASS = os.environ.get('USER_PASS')# "zzc997997"
CS_ID = os.environ.get('CS_ID')
TASK_ID = os.environ.get('TASK_ID')

QUERY_INTERVAL = 5
TIME_OUT = 24*60*60*7

LOCAL_RESULT_DIR = 'result'
LOCAL_TASKS_DIR = os.path.join('/home/fq-user','tasks')
LOCAL_LOGS_DIR = os.path.join('/home/fq-user','logs')
LOG_INFO_NAME = 'info.log'
LOG_ERROR_NAME = 'error.log'

