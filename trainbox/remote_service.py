# -*-coding:utf-8 -*-
import requests
import time
from threading import Thread
import os, subprocess
import sys
import psutil
import asyncio
from pynvml import *
from pprint import pprint
import conn_profile as cf
from firstquadrants import TaskClient
import local_service as ls

'''
!!!!!!!!!WARNING!!!!!!! 没用到这里
api = '/trainbox2mid/<id>'
@unique
class TBActions(Enum):
    task_over = 0 # 训练组件完成任务后，调用该接口
    json format: 'task_id' 完成的任务名称
                 'model_name' 存下来的模型名称
                 'file_path' 指定到对应的存储
'''


def send_rest_api(url, msg):
    try:
        r = requests.post(url, data=msg)
        return r
    except Exception as e:
        print("Request Error:", e)

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
            z = zipfile.ZipFile(os.path.join(data_dir, modelfile_name), 'w', zipfile.ZIP_DEFLATED)
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

    cmd = 'CUDA_VISIBLE_DEVICES={index} python {script}'.format(index=gpu_index, script=script_name)
    
    # 创建result 文件夹
    os.makedirs(os.path.join(data_dir, cf.LOCAL_RESULT_DIR))
    
    log_file = os.path.join(data_dir,cf.LOCAL_RESULT_DIR, cf.LOG_INFO_NAME)
    err_file = os.path.join(data_dir,cf.LOCAL_RESULT_DIR, cf.LOG_ERROR_NAME)
    # 创建日志和错误文件log
    os.mknod(log_file)
    os.mknod(err_file)

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
        stdout = open(log_file,'w+')
        stderr = open(err_file,'w+')
        subporc = subprocess.Popen(args=cmd,shell=True,stdout=stdout.fileno(),stderr=stderr.fileno(), cwd=data_dir)
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

def train_model(client, task, data_dir):
    try:
        client.get_task_data(task, data_dir=data_dir)
        script_name = task['script_file'].split('/')[-1]  # 默认python文件
        datafile_name = task['data_file'].split('/')[-1]  # 目前默认tar.gz
        compress_method = decompress_datafile(data_dir, datafile_name)
        '''
        fix this place
        '''
        # run_script(data_dir, script_name, task['gpu_id'])
        run_script(data_dir, script_name, 1)
        modelfile_name = compress_model_result(data_dir, compress_method)
        logfile = cf.LOG_INFO_NAME
        client.post_task_result(task['id'], task['gpu_id'],printed_str='',
                                model_file_path=os.path.join(data_dir,modelfile_name), 
                                log_file_path=os.path.join(data_dir,cf.LOCAL_RESULT_DIR,logfile))
    except Exception as err:
        print(err)
    else:
        return data_dir


async def request_for_tasks(client, q_tasks):
    try:
        servers = client.get_server_list()
        # print(servers)
    except Exception as err:
        print(err)
    
    while True:
        await asyncio.sleep(5)
        try:
            tasks = client.request_tasks()
            # print(tasks)
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
            # cur_task['gpu_id'] = servers[0]['id'] # 取出gpu_id
            cur_task['gpu_id'] = servers[0]['id']
            # print(cur_task)
            await q_tasks.put(cur_task)


async def process_tasks(client, q_tasks):

    while True:
        _task = await q_tasks.get()
        _dir = ''.join([hex(i) for i in os.urandom(10)])
        local_dir = cf.LOCAL_ROOT_DIR  # 封装注意修改LOCAL_ROOT_DIR

        # 后面的data_dir 都是这个目录，即用户文件目录
        _dir = os.path.join(local_dir, _dir)
        # print(_dir)
        # print(_task)
        lp = asyncio.get_event_loop()
        try:
            # res 暂时没用
            res = await lp.run_in_executor(None, train_model, client, _task, _dir,)
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
