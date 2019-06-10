# -*-coding:utf-8 -*-
import requests
import time
from threading import Thread
import os
import subprocess
import json
import sys
import psutil
import asyncio
from pynvml import *
from pprint import pprint
import conn_profile as cf
from firstquadrants import TaskClient
import local_service as ls


def decompress_datafile(data_dir, file_name):
    # 文件名错误怎么办？
    try:
        spilt_name = file_name.split('.')
        suffix_name = spilt_name[-1]
        if suffix_name == 'gz':
            suffix_name = 'tar.gz' if spilt_name[-2] == 'tar' else 'gz'

        if suffix_name == 'tar.gz':
            import tarfile
            tar = tarfile.open(os.path.join(data_dir, file_name))
            names = tar.getnames()
            for name in names:
                tar.extract(name, path=os.path.join(
                    data_dir, file_name.split('.')[0]))
            tar.close()
        elif suffix_name == 'zip':
            import zipfile
            zip_ref = zipfile.ZipFile(os.path.join(data_dir, file_name), 'r')
            zip_ref.extractall(os.path.join(data_dir, file_name.split('.')[0]))
            zip_ref.close()
        # 其他解压缩方法
        else:
            pass
    except IndexError:
        print('error file name')
    except IOError:
        print('error file path')
    else:
        return suffix_name


def compress_model_result(data_dir, method):
    try:
        modelfile_name = 'result.tar.gz'
        if method == 'tar.gz':
            modelfile_name = 'result.tar.gz'
            import tarfile
            tar = tarfile.open(os.path.join(data_dir, modelfile_name), "w:gz")
            startdir = os.path.join(data_dir, cf.LOCAL_RESULT_DIR)
            for root, _, files in os.walk(startdir):
                for file in files:
                    pathfile = os.path.join(root, file)
                    tar.add(pathfile)
            tar.close()

        elif method == 'zip':
            modelfile_name = 'result.zip'
            import zipfile
            z = zipfile.ZipFile(os.path.join(
                data_dir, modelfile_name), 'w', zipfile.ZIP_DEFLATED)
            startdir = os.path.join(data_dir, cf.LOCAL_RESULT_DIR)
            for dirpath, _, filenames in os.walk(startdir):
                for filename in filenames:
                    z.write(os.path.join(dirpath, filename))
            z.close()
        else:
            pass
    except Exception as err:
        print(err)
    else:
        return modelfile_name


def run_script(data_dir, script_name, gpu_index):
    # 目前支持python训练文件
    # tf keras pytorch 应该分开？

    cmd = 'CUDA_VISIBLE_DEVICES={index} python {script}'.format(
        index=gpu_index, script=script_name)

    # 创建result 文件夹
    if not os.path.exists(os.path.join(data_dir, cf.LOCAL_RESULT_DIR)):
        os.makedirs(os.path.join(data_dir, cf.LOCAL_RESULT_DIR))

    log_file = os.path.join(data_dir, cf.LOCAL_RESULT_DIR, cf.LOG_INFO_NAME)
    err_file = os.path.join(data_dir, cf.LOCAL_RESULT_DIR, cf.LOG_ERROR_NAME)

    proc_counts = 0
    for index in range(cf.REGISTER_GPU_COUNT):
        proc_counts += ls.GpuGetDeviceProcessCounts(index)['proc_counts']

    while proc_counts > cf.TASK_COUNTS_MAX:
        time.sleep(60)  # 等待释放
        proc_counts = 0
        for index in range(cf.REGISTER_GPU_COUNT):
            proc_counts += ls.GpuGetDeviceProcessCounts(index)['proc_counts']

    try:
        print("start train")
        # 创建
        stdout = open(log_file, 'w+')
        stderr = open(err_file, 'w+')
        subporc = subprocess.Popen(args=cmd, shell=True, stdout=stdout.fileno(
        ), stderr=stderr.fileno(), cwd=data_dir)
        subporc.communicate()
        res = subporc.returncode
        if res == 0:
            print("success")
        else:
            print("error when running script")
        stdout.flush()
        stderr.flush()
        stdout.close()
        stderr.close()
    except Exception as e:
        print("error:", e)
    else:
        return res

# state是任务状态，查看当前训练是否需要下载


def train_model(client, task, data_dir):
    try:
        # 训练过程出错，不需要再重新下载数据集
        if(task['state'] != 'running'):
            client.get_task_data(task, data_dir=data_dir)
        script_name = task['script_file'].split('/')[-1]  # 默认python文件
        datafile_name = task['data_file'].split('/')[-1]  # 目前默认tar.gz
        compress_method = decompress_datafile(data_dir, datafile_name)
        '''
        fix this place
        '''
        # run_script(data_dir, script_name, task['gpu_id'])
        res = 255
        while res != 0:
            res = run_script(data_dir, script_name, 1)
            # 没有正常结束，是否用上报？
            if res != 0:
                time.sleep(60)

        modelfile_name = compress_model_result(data_dir, compress_method)
        logfile_name = cf.LOG_INFO_NAME
        client.post_task_result(task['id'], task['gpu_id'], printed_str='',
                                model_file_path=os.path.join(
                                    data_dir, modelfile_name),
                                log_file_path=os.path.join(data_dir, cf.LOCAL_RESULT_DIR, logfile_name))
    except Exception as err:
        print(err)
    else:
        return data_dir


async def request_for_tasks(client, q_tasks):
    try:
        servers = client.get_server_list()
    except Exception as err:
        print(err)

    '''
    首先请求未完成任务列表
    '''
    unfin_tasks = [
        # {"id": 24, "name": "keras",
        #  "task_desc": "123",
        #  "script_file": "/media/2019/6/0xb40x4c0x5c0x160xe80x530xb0x370x680xab/cifar10_cnn_keras_docker_test.py",
        #  "data_file": "/media/2019/6/0xd40xe80xfb0xfc0x3b0x1d0x680x500xa00xda/cifar-10-batches-py.tar.gz",
        #  "add_time": "2019-06-10T13:19:10.953Z",
        #  "gpu_id": 349,
        #  "dir": "/data/0x2f0xf30x7f0xc10xe80x570x130xad0x7d0x3",
        #  "state": "running"},
        # {"id": 25,
        #  "name": "pytorch",
        #  "task_desc": "123",
        #  "script_file": "/media/2019/6/0xc40x700xd50x470xcc0x250x900xab0x9c0x44/gpu_test.py",
        #  "data_file": "/media/2019/6/0x150xf60x450x810x90xfa0xd10x690x260xd3/ywb_MNIST.tar.gz",
        #  "add_time": "2019-06-10T13:19:07.256Z",
        #  "gpu_id": 349,
        #  "dir": "/data/0x9f0x200x6a0xf80xf0x2b0x2d0xcb0xe00xb8",
        #  "state": "running"}
    ]

    f = open(os.path.join(cf.LOCAL_TASKS_DIR, 'tasks.txt'), 'r')
    for line in f:
        task = json.loads(line)
        for unfin_task in unfin_tasks:
            if task['id'] == unfin_task['id']:
                await q_tasks.put(unfin_task)
    f.close()

    while True:
        await asyncio.sleep(5)
        try:
            tasks = client.request_tasks()
        except Exception as err:
            print(err)
            continue
        else:
            if tasks == None:
                continue
            elif len(tasks) == 0:
                continue

        for i in range(0, len(tasks)):
            cur_task = tasks[i]  # 取出任务
            _dir = ''.join([hex(i) for i in os.urandom(10)])
            local_dir = cf.LOCAL_ROOT_DIR  # 封装注意修改LOCAL_ROOT_DIR
            # 后面的data_dir 都是这个目录，即用户文件目录
            _dir = os.path.join(local_dir, _dir)
            cur_task['gpu_id'] = servers[0]['id']
            cur_task['dir'] = _dir
            cur_task['state'] = 'down'
            # print(type(cur_task))
            f = open(os.path.join(cf.LOCAL_TASKS_DIR, 'tasks.txt'), 'a+')
            f.write(json.dumps(cur_task)+'\n')
            f.close()
            # print(cur_task)
            await q_tasks.put(cur_task)


async def process_tasks(client, q_tasks):

    while True:
        _task = await q_tasks.get()
        lp = asyncio.get_event_loop()
        try:
            # res 暂时没用
            res = await lp.run_in_executor(None, train_model, client, _task, _task['dir'],)
        except Exception as err:
            print(err)
            break


def connect_to_remote_server(username, password, protocol='http://', server_ip='127.0.0.1', port=8000):
    print("start remote service")
    domain = ':'.join([protocol + server_ip, str(port)])

    client = TaskClient(username=username, password=password,
                        domain=domain)

    gpu_count = ls.GpuGetCounts()['counts']  # 获取设备数量

    div_gb_factor = (1024.0 ** 3)
    pc_mem = int(psutil.virtual_memory().total / div_gb_factor)  # Int GB

    hd_size = 50  # GB 目前写死硬盘大小 后面需要根据docker的数据卷大小分配

    gpu_support = True if gpu_count > 0 else False

    register_gpu_index = []

    cf.REGISTER_GPU_COUNT = gpu_count

    # 目前把设备都注册到服务器上
    for i in range(0, gpu_count):
        register_gpu_index.append(i)
        gpu_mem = float(ls.GpuGetDeviceMemory(i)['mem_total'])
        try:
            flag = client.register_server(memory_size=pc_mem, hdisk_size=hd_size,
                                          support_gpu=gpu_support, gpu_memory_size=gpu_mem)
        except Exception as err:
            print(err)
        else:
            print(flag)

    main_loop = asyncio.get_event_loop()
    q_tasks = asyncio.Queue(
        loop=main_loop, maxsize=cf.TASK_COUNTS_MAX)
    coroutines = []

    req_co = request_for_tasks(client, q_tasks)
    coroutines.append(req_co)

    # 开启多个消费者
    for _ in range(cf.TASK_COUNTS_MAX):
        proc_co = process_tasks(client, q_tasks)
        coroutines.append(proc_co)

    while True:
        try:
            main_loop.run_until_complete(asyncio.gather(*coroutines))
        except Exception as err:
            print(err)
        finally:
            print("close")
            # main_loop.close()


if __name__ == '__main__':
    nvmlInit()
    connect_to_remote_server('zzczzc', 'zzc997997')
