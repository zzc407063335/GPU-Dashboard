# -*- coding: utf-8 -*-
from conn_file_r import *
from pynvml import nvmlInit
from multiprocessing import Pool
import remote_app, local_app

def local_app_start(HOST='0.0.0.0', PORT=8997):
    nvmlInit()

    try:
        local_app.app.run(host=HOST, port=PORT)  # 注意 本机测试和容器内测试端口要变动
    except Exception as err:
        print(err)
    



def remote_app_start(client):
    nvmlInit()
    try:
        remote_app.connect_to_remote_server(client)
    except Exception as err:
        print(err)


if __name__ == '__main__':
    client = remote_app.check_user(USER_NAME,USER_PASS, 
                                PROTOCOL, SERVER_IP, SERVER_PORT)
    if client == False:
        os._exit(-1)
    nvmlInit()
    
    pool=Pool(2)
    pool.apply_async(local_app_start, ('0.0.0.0',LOCAL_PORT,))
    pool.apply_async(remote_app_start,(client,))
    pool.close()
    pool.join()

