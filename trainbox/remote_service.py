# -*-coding:utf-8 -*-
import requests
import time
from threading import Thread
import os, sys, traceback, random
import subprocess, threading
import json
import psutil
import asyncio
from pynvml import *
from pprint import pprint
import conn_profile as cf
from firstquadrants import TaskClient
import local_service as ls

sys.path.append('logs')
from logfile import errorLogger,infoLogger,debugLogger

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
            print('undefined decompress method')
            pass
    except IndexError:
        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
    except IOError:
        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
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
        # 默认zip
        else:
            modelfile_name = 'result.zip'
            import zipfile
            z = zipfile.ZipFile(os.path.join(
                data_dir, modelfile_name), 'w', zipfile.ZIP_DEFLATED)
            startdir = os.path.join(data_dir, cf.LOCAL_RESULT_DIR)
            for dirpath, _, filenames in os.walk(startdir):
                for filename in filenames:
                    z.write(os.path.join(dirpath, filename))
            z.close()
    except Exception:
        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
    else:
        return modelfile_name

def kill_time_out_task(subproc):
    try:
        os.killpg(subproc.pid, 9)
    except Exception as err:
        debugLogger.debug(err)
        errorLogger.error('\n'+str(traceback.format_exc())+'\n')

def run_script(data_dir, script_name, gpu_index, task_id):
    # 目前支持python训练文件
    # tf keras pytorch 应该分开？

    # PYTHONUNBUFFERED=1 默认不使用缓存，实时获取STDOUT输出 
    cmd = 'CUDA_VISIBLE_DEVICES={index} PYTHONUNBUFFERED=1 python {script}'.format(
        index=gpu_index, script=script_name)

    # 创建result 文件夹
    if not os.path.exists(os.path.join(data_dir, cf.LOCAL_RESULT_DIR)):
        os.makedirs(os.path.join(data_dir, cf.LOCAL_RESULT_DIR))

    log_file = os.path.join(data_dir, 
                            cf.LOCAL_RESULT_DIR, 
                            cf.LOG_INFO_NAME)
    err_file = os.path.join(data_dir, 
                            cf.LOCAL_RESULT_DIR, 
                            cf.LOG_ERROR_NAME)

    proc_counts = 0
    for index in range(cf.REGISTER_GPU_COUNT):
        proc_counts += ls.GpuGetDeviceProcessCounts(index)['proc_counts']

    while proc_counts > cf.TASK_COUNTS_MAX:
        time.sleep(60)  # 等待释放
        proc_counts = 0
        for index in range(cf.REGISTER_GPU_COUNT):
            proc_counts += ls.GpuGetDeviceProcessCounts(index)['proc_counts']

    try:
        debugLogger.debug("start train")
        # 创建
        stdout = open(log_file, 'w+')
        stderr = open(err_file, 'w+')
        subporc = subprocess.Popen(args=cmd, shell=True, stdout=subprocess.PIPE,
                    stderr=stderr.fileno(), preexec_fn=os.setsid, cwd=data_dir)
        infoLogger.info('Start train. Subprocess ID:{pid}'
                        .format(pid=subporc.pid))
        time_out = cf.TIME_OUT
        task_timer = threading.Timer(time_out, kill_time_out_task, [subporc])
        task_timer.start()     
        line = []
        while len(line) > 1 or subporc.poll() == None:
            line = subporc.stdout.readline().decode('utf-8').split('\n')
            stdout.write(line[0] + '\n')
            print(line[0])
            # client.post_line() 实时输出反馈给服务器
        res = subporc.returncode
        # subporc.communicate()
    except BaseException:
        task_timer.cancel()
        # 执行过程中出现了错误,例如ctl+c
        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        os.killpg(subporc.pid,9)
        subporc.kill()
        subporc.communicate()
    else:
        task_timer.cancel()
        debugLogger.debug(res)
        if res == 0:
            debugLogger.debug("success")
            infoLogger.info('Finish task. Subprocess ID:{pid}'.format(
                                pid=subporc.pid))
        else:
            debugLogger.debug("error when running script")
            # 就要删掉对应的子进程,
            # 这里可能子进程subprocess已经结束了，例如错误的代码内容等，因此killpg时可能会抛出异常，不过不影响服务
            # -9 和 137
            try:
                infoLogger.info('Error when run the script.\
                                Task ID: {task_id}.\
                                Subprocess ID:{pid}.\
                                Returncode:{returncode}.\
                                Kill the subprocess.'
                            .format(task_id=task_id,pid=subporc.pid,returncode=res))
                os.killpg(subporc.pid,9)
            except BaseException:
                errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        stdout.flush()
        stderr.flush()
        stdout.close()
        stderr.close()
    finally:
        return res

# state是任务状态，查看当前训练是否需要下载
def train_model(client, task, data_dir):
    try:
        # 训练过程出错，不需要再重新下载数据集
        # 注意:目前没有增加数据集下载过程出错的差错控制
        # 正在运行状态,注意gpu_id 对应于服务器端的user_server_no
        if(task['status'] != 'RN'):
            client.confirm_request(task['id'],task['gpu_id'])
            client.get_task_data(task=task, 
                                data_dir=data_dir, 
                                user_server_no=task['gpu_id'])
            
        script_name = task['script_file'].split('/')[-1]  # 默认python文件
        datafile_name = task['data_file'].split('/')[-1]  # 目前默认tar.gz
        compress_method = decompress_datafile(data_dir, datafile_name)
        '''
        fix this place
        '''
        # run_script(data_dir, script_name, task['gpu_id'])
        res = -1
        try_time = 0
        script_res = False
        while res != 0:
            try_time += 1
            client.start_running_task(task['id'],task['gpu_id'])
            res = run_script(data_dir, script_name, task['gpu_id'],task['id'])
            # 没有正常结束,retry
            if res == 0:
                script_res = True
            if try_time >= 10:
                infoLogger.info('Retry {times} times. Post latest retry log.'
                                .format(times=try_time))
                break
            if res != 0:
                sleep_time = random.randint(60,180)
                infoLogger.info('Task {id} return no-zero code.\
                                Sleep {time}s and re-run the script.'
                                .format(id=task['id'],time=sleep_time))
                time.sleep(sleep_time)
                
        uploadfile_name = compress_model_result(data_dir, compress_method)
        infoLogger.info('Post result to server. Task {task_id}'
                        .format(task_id=task['id']))
        client.post_task_result(task['id'], task['gpu_id'], 
                                output_string='task finished',
                                valid_or_not=script_res,
                                output_file=os.path.join(
                                    data_dir, uploadfile_name)
                                )
    except Exception:
        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
    else:
        return data_dir


async def request_for_tasks(client, q_tasks):
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
    
    if not os.path.exists(os.path.join(cf.LOCAL_TASKS_DIR,'tasks.txt')):
        os.mknod(os.path.join(cf.LOCAL_TASKS_DIR,'tasks.txt'))
    
    f = open(os.path.join(cf.LOCAL_TASKS_DIR,'tasks.txt'),'r')
    # 注意此处，如果下载数据集的过程中出错了，那么这里会出现bug
    for line in f:
        task = json.loads(line)
        for unfin_task in all_unfin_tasks:
            if task['id'] == unfin_task['id']:
                infoLogger.info('Continue unfinished task {id}'.format(
                                                id=unfin_task['id']))
                task['status'] = 'RN'
                await q_tasks.put(task)
    f.close()
    
    while True:
        await asyncio.sleep(5)
        tasks = []
        try:
            # 目前这块儿还没定下来
            for device in devices:
                cur_tasks = client.request_tasks(device['user_server_no'])
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
                                {gpu_id}'.format(task_id=cur_task['id'],
                                gpu_id=cur_task['gpu_id']))
            # print(cur_task)
            await q_tasks.put(cur_task)

async def process_tasks(client, q_tasks):
    while True:
        _task = await q_tasks.get()
        lp = asyncio.get_event_loop()
        try:
            infoLogger.info('Process task {task_id}. Use GPU {gpu_id}'
                    .format(task_id=_task['id'],gpu_id=_task['gpu_id']))
            res = await lp.run_in_executor(None, train_model, 
                                            client, _task, _task['dir'],)
        except Exception:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            break

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
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            debugLogger.debug('\n'+str(traceback.format_exc())+'\n')
            infoLogger.info('Stop service.')
            break

            # main_loop.close()


if __name__ == '__main__':
    nvmlInit()
