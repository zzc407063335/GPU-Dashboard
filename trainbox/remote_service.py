# -*-coding:utf-8 -*-
import requests
import time
from threading import Thread
import os, sys, traceback, random
import subprocess, threading
import json
import psutil, shelve
import asyncio
from pynvml import *
from pprint import pprint
import conn_profile as cf
from firstquadrants import TaskClient
import local_service as ls
from producer import TaskProducer
from consumer import TaskConsumer

sys.path.append('logs')
from logfile import errorLogger,infoLogger,debugLogger

def check_user(username, password, protocol='http://', 
                            server_ip='127.0.0.1', port=8000):
    domain = protocol + server_ip
    client = TaskClient(username=username, 
                        password=password,
                        domain=domain)
    client._login()
    if client.am_i_login():
        return client
    else:
        errorLogger.error('Wrong username and/or password.')
        return False

def connect_to_remote_server(client):
    infoLogger.info('service start')
    gpu_count = ls.GpuGetCounts()['counts']  # 获取设备数量

    div_gb_factor = (1024.0 ** 3)
    pc_mem = int(psutil.virtual_memory().total / div_gb_factor)  # Int GB

    hd_size = 50  # GB 目前写死硬盘大小 后面需要根据docker的数据卷大小分配

    gpu_support = True if gpu_count > 0 else False

    register_gpu_index = []

    cf.REGISTER_GPU_COUNT = gpu_count

    devices = client.get_server_list()
    # 目前把设备都注册到服务器上
    for i in range(0, gpu_count):
        ctl = False
        for device in devices:
            # 已经注册过本机的某块GPU
            if device['user_server_no'] == i:
                debugLogger.debug('exists')
                ctl = True
                break
        if ctl:
            continue
        register_gpu_index.append(i)
        gpu_mem = float(ls.GpuGetDeviceMemory(i)['mem_total'])
        gpu_name = ls.GpuGetDeviceName(i)['device_name']
        gpu_brand = ls.GpuGetDeviceBrand(i)['brand_name']
        try:
            flag = client.register_server(memory_size=pc_mem, 
                                   hdisk_size=hd_size,
                                   device_name=gpu_name,
                                   device_series=gpu_brand,
                                   user_server_no=i,
                                   support_gpu=gpu_support, 
                                   gpu_memory_size=gpu_mem)
        except Exception:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        else:
            infoLogger.info('Register GPU {index} to server.'
                            .format(index=i))
            if flag != None:
                debugLogger.debug('true')
    producer = TaskProducer()
    
    main_loop = asyncio.get_event_loop()
    q_tasks = asyncio.Queue(
        loop=main_loop, maxsize=cf.TASK_COUNTS_MAX)

    # 协程列表    
    coroutines = []
    # 正在进行的任务
    processing_list = []
    TaskProducer.client = client
    TaskProducer.q_tasks = q_tasks
    TaskProducer.co_loop = main_loop
    TaskProducer.proc_tasks = processing_list

    TaskConsumer.client = client
    TaskConsumer.q_tasks = q_tasks
    TaskConsumer.co_loop = main_loop
    TaskConsumer.proc_tasks = processing_list

    coroutines.append(producer.request_for_tasks())

    # 开启多个消费者
    for i in range(cf.TASK_COUNTS_MAX):
        consumer = TaskConsumer(i)
        coroutines.append(consumer.process_tasks())

    while True:
        try:
            main_loop.run_until_complete(asyncio.gather(*coroutines))
        except Exception as err:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            debugLogger.debug('\n'+str(traceback.format_exc())+'\n')
            infoLogger.info('Stop service.')
            main_loop.close()
            db.close()
            break
            # main_loop.close()


if __name__ == '__main__':
    nvmlInit()
