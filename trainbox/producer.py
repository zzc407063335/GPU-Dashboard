import requests
import time
from threading import Thread
import os, sys, traceback, random
import subprocess, threading
import json
import asyncio
from pynvml import *
from pprint import pprint
import conn_profile as cf
from firstquadrants import TaskClient
import local_service as ls

sys.path.append('logs')
from logfile import errorLogger,infoLogger,debugLogger

class TaskProducer(object):
    client: TaskClient
    q_tasks: asyncio.Queue # 任务队列
    co_loop: asyncio.unix_events._UnixSelectorEventLoop
    def __init__(self):
        self.all_unfin_tasks = []

    async def request_for_tasks(self):
        client = self.client
        q_tasks = self.q_tasks
        try:
            devices = client.get_server_list()
            devices_cnt = len(devices)
        except Exception:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        '''
        首先请求未完成任务列表
        '''
        all_unfin_tasks = []
        try:
            for device in devices:
                unfin_tasks = client.request_running_tasks(
                    device['user_server_no'])
                for unfin_task in unfin_tasks:
                    exist = False
                    for task in all_unfin_tasks:
                        if task['id'] == unfin_task['id']:
                            exist = True
                            break
                    if not exist:
                        all_unfin_tasks.append(unfin_task)
        except Exception:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        
        if not os.path.exists(os.path.join(cf.LOCAL_TASKS_DIR,
                                                'tasks.txt')):
            os.mknod(os.path.join(cf.LOCAL_TASKS_DIR,'tasks.txt'))
        
        f = open(os.path.join(cf.LOCAL_TASKS_DIR,'tasks.txt'),'r')
        # 注意此处，如果下载数据集的过程中出错了，那么这里会出现bug
        for line in f:
            task = json.loads(line)
            for unfin_task in all_unfin_tasks:
                if task['id'] == unfin_task['id']:
                    infoLogger.info('Continue unfinished task {id}'
                                    .format(id=unfin_task['id']))
                    task['status'] = 'RN'
                    await q_tasks.put(task)
        f.close()
        
        while True:
            await asyncio.sleep(5)
            tasks = []
            try:
                # 目前这块儿还没定下来
                for device in devices:
                    cur_tasks = client.request_tasks(
                                device['user_server_no'])
                    for cur_task in cur_tasks:
                        exist = False
                        for task in tasks:
                            if task['id'] == cur_task['id']:
                                exist = True
                                break
                        if not exist:
                            tasks.append(cur_task)
            except Exception:
                errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                continue
            else:
                if tasks == None:
                    continue
                elif len(tasks) == 0:
                    continue

            pprint(tasks)
            index_clt = 0
            for cur_task in tasks:
                index_clt = (index_clt + 1) % devices_cnt
                _dir = ''.join([hex(i) for i in os.urandom(10)])
                local_dir = cf.LOCAL_DATA_DIR  
                # 封装注意修改LOCAL_DATA_DIR
                # 后面的data_dir 都是这个目录，即用户文件目录
                _dir = os.path.join(local_dir, _dir)
                cur_task['gpu_id'] = index_clt
                cur_task['dir'] = _dir
                # print(type(cur_task))
                f = open(os.path.join(cf.LOCAL_TASKS_DIR, 'tasks.txt'), 'a+')
                f.write(json.dumps(cur_task)+'\n')
                f.close()
                infoLogger.info('Put task {task_id} in queue. Use GPU \
                                    {gpu_id}'
                                    .format(task_id=cur_task['id'],
                                    gpu_id=cur_task['gpu_id']))
                # print(cur_task)
                await q_tasks.put(cur_task)
