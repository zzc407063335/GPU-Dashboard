# 定义一些训练组件和中间件的接口数据
import os

PROTOCOL = 'http://'
# SERVER_IP = '172.18.0.1'
SERVER_IP = os.environ.get('SERVER_IP')
SERVER_PORT = os.environ.get('SERVER_PORT')

USER_NAME = os.environ.get('USER_NAME')# "zzczzc"
USER_PASS = os.environ.get('USER_PASS')# "zzc997997"

LOCAL_PORT = os.environ.get('LOCAL_PORT')
LOCAL_ROOT_DIR = '/data' 
LOCAL_RESULT_DIR = './result'
LOCAL_RESULT_DIR_NAME = 'result'
LOG_INFO_NAME = 'info.log'
LOG_ERROR_NAME = 'error.log'

TASK_COUNTS_MAX = os.environ.get('MAX_TASK_NUMBER')
REGISTER_GPU_COUNT = 0