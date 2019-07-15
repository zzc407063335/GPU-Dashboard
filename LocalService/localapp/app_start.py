# -*- coding: utf-8 -*-
from DockerApp.conn_file_r import *
from pynvml import nvmlInit
from multiprocessing import Pool
import DockerApp.local_app as l_app

def local_app_start(HOST='0.0.0.0', PORT=8997):
    try:
        nvmlInit()
    except Exception as err:
        print(err)
    try:
        l_app.app.run(host=HOST, port=PORT)  # 注意 本机测试和容器内测试端口要变动
    except Exception as err:
        print(err)


if __name__ == '__main__':
    try:
        nvmlInit()
    except Exception as err:
        print(err) 
    pool=Pool(1)
    pool.apply_async(local_app_start, ('0.0.0.0',LOCAL_PORT,))
    pool.close()
    pool.join()

