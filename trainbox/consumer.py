import requests
import time
import os, sys, traceback, random
import subprocess, threading
import json
import asyncio, ctypes, inspect
from pynvml import *
from pprint import pprint
import conn_profile as cf
from firstquadrants import TaskClient
import local_service as ls
from enum import Enum, unique
import shelve

from logs.logfile import errorLogger,infoLogger,debugLogger

import concurrent
@unique
class TaskStatus(Enum):
    TaskFinished = 0
    ScriptError = 1
    DataSetError = 2
    TaskTimeOut = 3
    TaskStopped = 4
    DownloadStopped = 5
    UnKownError = 127

StatusDesc = {
    TaskStatus.TaskFinished.value: 'Task finished.',
    TaskStatus.ScriptError.value: 'An error occurred while running the script.',
    TaskStatus.DataSetError.value: 'There was an error in decompression.',
    TaskStatus.TaskTimeOut.value: 'Task timeout.',
    TaskStatus.TaskStopped.value: 'Task stops.',
    TaskStatus.DownloadStopped.value: 'Download stops',
    TaskStatus.UnKownError.value: 'Unknown error while running the script.'
}

TaskStatusZh2En = {
    '已提交':'SB',
    '已分配':'DT',
    '正在运行':'RN',
    '已完成':'CP',
    '任务无效':'IV',
    '已停止':'ST',
    '代码已更新':'CU',
    '数据已更新':'DU',
    '已恢复':'RC'
}

concurrent.futures.ThreadPoolExecutor
class TaskConsumer(object):
    client: TaskClient
    q_tasks: asyncio.Queue # 任务队列
    co_loop: asyncio.unix_events._UnixSelectorEventLoop
    proc_tasks: list # 正在处理中的任务
    db: shelve.DbfilenameShelf
    co_lock: asyncio.locks.Lock # 共享协程锁，用于操作db
    th_lock = threading.Lock() # 共享线程锁，用于train_model中操作db
    def __init__(self,cs_id):
        self.consumer_id = cs_id
        self.task = None
        self.time_out = cf.TIME_OUT
        self.task_timer: threading.Timer
        self.task_subproc = None
        self.task_status = TaskStatus.UnKownError
        self.task_desc = StatusDesc[self.task_status.value]
    
    def stop_thread_tasks(self, thread, exctype=SystemExit):
        # 这段代码摘录自知乎
        tid = ctypes.c_long(thread.ident)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 
                                        ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're 
            # in trouble,
            # and you should call it again with exc=NULL to 
            # revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def clear_latest_task(self):
        self.proc_tasks.remove(self.task['id'])
        self.task = None
        self.task_subproc = None
        self.task_status = TaskStatus.UnKownError
        self.task_desc = StatusDesc[self.task_status.value]

    def set_status_transfer(self, new_status, last_status):
        self.store_data_in_local(str(self.task['id']),
                                        'status', new_status)
        self.store_data_in_local(str(self.task['id']),
                                        'last_status', last_status)

    def store_data_in_local(self, task_id, task_key, task_value):
        self.th_lock.acquire()
        self.db = shelve.open(os.path.join(cf.LOCAL_TASKS_DIR,
                                'tasks.dat'), writeback=True)
        self.db[str(task_id)][task_key] = task_value
        self.db.close()
        self.th_lock.release()

    def read_data_in_local(self, task_id, task_key):
        self.th_lock.acquire()
        self.db = shelve.open(os.path.join(cf.LOCAL_TASKS_DIR,
                                'tasks.dat'), flag='r')
        res = None
        if str(task_id) in self.db.keys():
            res = self.db[str(task_id)][task_key]
        else:
            res = None
        self.db.close()
        self.th_lock.release()
        return res
    # 设置超时时长
    def set_time_out(self, time):
        self.time_out = time

    def decompress_datafile(self, data_dir, file_name):
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
                infoLogger.info('Task {id} receive wrong data files.'.format(
                    id=self.task['id']))
                self.set_task_desc(TaskStatus.DataSetError)
                suffix_name = 'error'
                # undefined decompress method
        except IndexError:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        except IOError:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        else:
            return suffix_name
    
    def compress_model_result(self, data_dir, method):
        try:
            modelfile_name = 'result.tar.gz'
            if method == 'tar.gz':
                modelfile_name = 'result.tar.gz'
                import tarfile
                tar = tarfile.open(os.path.join(data_dir, modelfile_name), "w:gz")
                startdir = os.path.join(data_dir, cf.LOCAL_RESULT_DIR)
                for dirpath, _, filenames in os.walk(startdir):
                    for filename in filenames:
                        path_file = os.path.join(dirpath, filename)
                        # 去除/data/0x.......的前缀
                        arcname = path_file[len(data_dir):].strip(os.path.sep)
                        tar.add(path_file, arcname)
                tar.close()

            elif method == 'zip':
                modelfile_name = 'result.zip'
                import zipfile
                z = zipfile.ZipFile(os.path.join(
                    data_dir, modelfile_name), 'w', zipfile.ZIP_DEFLATED)
                startdir = os.path.join(data_dir, cf.LOCAL_RESULT_DIR)
                for dirpath, _, filenames in os.walk(startdir):
                    for filename in filenames:
                        path_file = os.path.join(dirpath, filename)
                        # 去除/data/0x.......的前缀
                        arcname = path_file[len(data_dir):].strip(os.path.sep)
                        z.write(path_file, arcname)
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
                        path_file = os.path.join(dirpath, filename)
                        arcname = path_file[len(data_dir):].strip(os.path.sep)
                        z.write(path_file, arcname)
                z.close()
        except Exception:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        else:
            return modelfile_name

    def set_task_desc(self, _task_status):
        self.task_status = _task_status
        self.task_desc = StatusDesc[self.task_status.value]

    def stop_task(self, subproc):
        try:
            self.set_task_desc(TaskStatus.TaskStopped)
            infoLogger.info('Task {id} stop.'.format(id=self.task['id']))
            os.killpg(subproc.pid, 9)
            subproc.kill()
            subproc.communicate()
        except Exception as err:
            debugLogger.debug(err)
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')

    def kill_time_out_task(self, subproc):
        try:
            self.set_task_desc(TaskStatus.TaskTimeOut)
            infoLogger.info('Task {id} time out.'.format(id=self.task['id']))
            os.killpg(subproc.pid, 9)
        except Exception as err:
            debugLogger.debug(err)
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')

    def set_task_timer(self, time, subproc):
        self.time_out = time
        try:
            self.task_timer.cancel()
        except Exception as err:
            # 可能定时器不存在
            debugLogger.debug(err)
            # errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            
        self.task_timer = threading.Timer(self.time_out, self.kill_time_out_task, 
                                            [subproc])
        self.task_timer.start()

    def run_script(self, data_dir, script_name, gpu_index, task_id):
        # 目前支持python训练文件
        # tf keras pytorch 应该分开？

        # PYTHONUNBUFFERED=1 默认不使用缓存，实时获取STDOUT输出 
        cmd = 'CUDA_VISIBLE_DEVICES={index} PYTHONUNBUFFERED=1 python {script}'\
            .format(index=gpu_index, script=script_name)

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
            infoLogger.info('Task {task_id}. Processes more than {count}. Waiting'
                            .format(task_id=task_id,count=cf.TASK_COUNTS_MAX))
            proc_counts = 0
            for index in range(cf.REGISTER_GPU_COUNT):
                proc_counts += ls.GpuGetDeviceProcessCounts(index)['proc_counts']

        try:
            debugLogger.debug("start train")
            # 创建
            stdout = open(log_file, 'w+')
            subproc = subprocess.Popen(args=cmd, bufsize=0, shell=True, 
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                        preexec_fn=os.setsid, cwd=data_dir)
            infoLogger.info('Task {id} start train. Subprocess ID:{pid}'
                            .format(id=task_id, pid=subproc.pid))
            self.task_subproc = subproc
            self.set_task_timer(self.time_out, subproc)
            
            line = ''
            while len(line) >= 1 or subproc.poll() == None:
                # 每次读取512个字符
                line = subproc.stdout.read(512).decode('utf-8')
                stdout.write(line)
                stdout.flush()
                # print(line)
                # 反馈输出
                resp = False
                while not resp:
                    try:
                        # 网络原因可能出错，这里缺乏重传机制，写死一直请求
                        resp = self.client.post_task_output_str(task_id=self.task['id'],
                                            user_server_no=self.task['gpu_id'], 
                                            output_string=line)
                    except Exception as err:
                        resp = False
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} post string error. Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                if TaskStatusZh2En[resp] == 'ST': 
                    self.stop_task(self.task_subproc)
                    self.set_status_transfer('ST','RN')
                    upload_str = '\n' + ': '.join([self.task_status.name,self.task_desc]) + '\n'
                    resp = False
                    # 反馈停止训练
                    while not resp:
                        try:
                            resp = self.client.post_task_output_str(
                                        task_id=self.task['id'],
                                        user_server_no=self.task['gpu_id'], 
                                        output_string=upload_str)
                        except Exception as err:
                            resp = False
                            time.sleep(random.randint(1,2))
                            infoLogger.info('Task {id} stop error. Network error.'\
                                        .format(id=self.task['id']))
                            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                    break

            res = subproc.returncode
            # subproc.communicate()
        except BaseException:
            # 执行过程中出现了错误
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            try:
                os.killpg(subproc.pid,9)
                subproc.kill()
                subproc.communicate()
            except Exception:
                errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        else:
            debugLogger.debug(res)
            if res == 0:
                debugLogger.debug("success")
                infoLogger.info('Finish task. Task {id}'.format(
                                    id=self.task['id']))
            else:
                debugLogger.debug("error when running script")
                # 就要删掉对应的子进程,
                # 这里可能子进程subprocess已经结束了，例如错误的代码内容等
                # 因此killpg时可能会抛出异常，不过不影响服务
                # -9 和 137
                try:
                    infoLogger.info('Error when run the script.\
                                    Task ID: {task_id}.\
                                    Subprocess ID:{pid}.\
                                    Returncode:{returncode}.\
                                    Kill the subprocess.'
                                .format(task_id=task_id,pid=subproc.pid,returncode=res))
                    os.killpg(subproc.pid,9)
                except BaseException:
                    errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            stdout.flush()
            stdout.close()
        finally:
            res = subproc.returncode
            return res
    
    def train_model(self):
        client = self.client
        data_dir = self.task['dir']
        try:
            # 训练过程出错，不需要再重新下载数据集
            # 正在运行状态,注意gpu_id 对应于服务器端的user_server_no
            if TaskStatusZh2En[self.task['status']] == 'SB':
                resp = False
                while not resp:
                    try:
                        resp = client.confirm_request(self.task['id'],self.task['gpu_id'])
                    except Exception:
                        resp = False
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} confirm error. Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                # SB => DT
                self.set_status_transfer('DT', 'SB')
                infoLogger.info('Task {id} start download.'
                                .format(id=self.task['id']))
                
                # 如果client.get_task_data,失败怎么办？
                down_th = threading.Thread(
                                target=client.get_task_data,
                                args=(self.task, 
                                    data_dir,self.task['gpu_id']))
                down_th.start()
                while down_th.isAlive():
                    time.sleep(cf.QUERY_INTERVAL)
                    try:
                        info = client.get_task_info(self.task['id'])
                    except Exception:
                        info = None
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} request task info error. Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                    if info == None:
                        continue
                    status = TaskStatusZh2En[info['status']]
                    if status == 'ST':
                        try:
                            self.set_task_desc(TaskStatus.DownloadStopped)
                            self.stop_thread_tasks(down_th)
                            self.set_status_transfer('ST', 'DT')
                        except Exception:
                            errorLogger.error('\n'+
                                str(traceback.format_exc())+'\n')
                        else:
                            infoLogger.info('Task {task_id} stop download.'
                                            .format(task_id=self.task['id']))
                        
                        resp = False
                        while not resp:
                            try:
                                upload_str = '\n' + ': '.join([
                                                self.task_status.name,
                                                self.task_desc])
                                resp = self.client.post_task_output_str(
                                    task_id=self.task['id'],
                                    user_server_no=self.task['gpu_id'],
                                    output_string=upload_str,
                                    outstr_mode='append',
                                    valid_or_not=True,
                                    is_completed=False)
                            except Exception:
                                resp = False
                                time.sleep(random.randint(1,2))
                                infoLogger.info('Task {id} stop error. Network error.'\
                                        .format(id=self.task['id']))
                                errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                        return data_dir
                
                resp = False
                while not resp:
                    try:
                        resp = client.start_running_task(self.task['id'],
                                                        self.task['gpu_id'])
                    except Exception:
                        resp = False
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} confirm running error. Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')  
                    else:
                        resp = True
                infoLogger.info('Task {id} start train.'.format(id=self.task['id']))
                self.set_status_transfer('RN', 'DT')

            # 下载没有进行完宕机了，需要重新下载
            elif TaskStatusZh2En[self.task['status']] == 'DT':
                infoLogger.info('Task {id} restart download.'
                                .format(id=self.task['id']))

                down_th = threading.Thread(target=client.get_task_data,
                                    args=(self.task, 
                                        data_dir,self.task['gpu_id']))
                down_th.start()
                while down_th.isAlive():
                    time.sleep(cf.QUERY_INTERVAL)
                    try:
                        info = client.get_task_info(self.task['id'])
                    except Exception:
                        info = None
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} request task info error. Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')

                    if info == None:
                        continue
                    status = TaskStatusZh2En[info['status']]
                    if status == 'ST':
                        try:
                            self.set_task_desc(TaskStatus.DownloadStopped)
                            self.stop_thread_tasks(down_th)
                            self.set_status_transfer('ST', 'DT')
                        except Exception:
                            errorLogger.error('\n'+
                                str(traceback.format_exc())+'\n')
                        else:
                            infoLogger.info('Task {task_id} stop download.'
                                            .format(task_id=self.task['id']))
                        
                        resp = False
                        while not resp:
                            try:
                                upload_str = '\n' + ': '.join([
                                                self.task_status.name,
                                                self.task_desc])
                                resp = self.client.post_task_output_str(
                                    task_id=self.task['id'],
                                    user_server_no=self.task['gpu_id'],
                                    output_string=upload_str,
                                    outstr_mode='append',
                                    valid_or_not=True,
                                    is_completed=False)
                            except Exception:
                                resp = False
                                time.sleep(random.randint(1,2))
                                infoLogger.info('Task {id} stop error. Network error.'\
                                        .format(id=self.task['id']))
                                errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                        return data_dir
                
                resp = False
                while not resp:
                    try:
                        resp = client.start_running_task(self.task['id'],
                                                        self.task['gpu_id'])
                    except Exception:
                        resp = False
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} confirm running error. Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')  
                    else:
                        resp = True
                infoLogger.info('Task {id} restart train.'.format(id=self.task['id']))
                self.set_status_transfer('RN', 'DT')

            # 运行当中宕机了，服务重启之后重新跑任务
            elif TaskStatusZh2En[self.task['status']] == 'RN':
                infoLogger.info('Task {id} reload, and restart train.'
                                .format(id=self.task['id']))
                self.set_status_transfer('RN', 'RN')
                resp = False
                while not resp:
                    try:
                        upload_str = 'Reload the task.\n'
                        resp = self.client.post_task_output_str(
                                    task_id=self.task['id'],
                                    user_server_no=self.task['gpu_id'],
                                    output_string=upload_str,
                                    outstr_mode='write',
                                    valid_or_not=True,
                                    is_completed=False)
                    except Exception:
                        resp = False
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} confirm re-running error. Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')  

                    
            # 恢复的任务
            elif TaskStatusZh2En[self.task['status']] == 'RC':
                resp = False
                while not resp:
                    try:
                        resp = client.confirm_request(self.task['id'],self.task['gpu_id'])
                    except Exception:
                        resp = False
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} confirm error (recover). Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')

                f_exist = self.read_data_in_local(
                                        str(self.task['id']),'id') 
                if f_exist == None:
                    # the same as 'SB'
                    infoLogger.info('Task {} save info. (recover)'.format(self.task['id']))
                    self.th_lock.acquire()
                    # 把新来的恢复任务先存下来
                    self.db = shelve.open(os.path.join(cf.LOCAL_TASKS_DIR,
                                            'tasks.dat'), writeback=True)
                    self.db[str(self.task['id'])] = self.task
                    self.db.close()
                    self.th_lock.release()
                    self.set_status_transfer('DT', 'RC')

                    infoLogger.info('Task {id} start download (recover).'
                                .format(id=self.task['id']))
                    down_th = threading.Thread(
                                    target=client.get_task_data,
                                    args=(self.task, 
                                        data_dir,self.task['gpu_id']))
                    down_th.start()
                    while down_th.isAlive():
                        time.sleep(cf.QUERY_INTERVAL)
                        try:
                            info = client.get_task_info(self.task['id'])
                        except Exception:
                            info = None
                            time.sleep(random.randint(1,2))
                            infoLogger.info('Task {id} request task info error (recover). Network error.'\
                                        .format(id=self.task['id']))
                            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                        if info == None:
                            continue
                        status = TaskStatusZh2En[info['status']]
                        if status == 'ST':
                            try:
                                self.set_task_desc(TaskStatus.DownloadStopped)
                                self.stop_thread_tasks(down_th)
                                self.set_status_transfer('ST', 'DT')
                            except Exception:
                                errorLogger.error('\n'+
                                    str(traceback.format_exc())+'\n')
                            else:
                                infoLogger.info('Task {task_id} stop download (recover).'
                                                .format(task_id=self.task['id']))
                            resp = False
                            while not resp:
                                try:
                                    upload_str = '\n'+': '.join([self.task_status.name,
                                                self.task_desc])
                                    resp = self.client.post_task_output_str(
                                        task_id=self.task['id'],
                                        user_server_no=self.task['gpu_id'],
                                        output_string=upload_str,
                                        outstr_mode='append',
                                        valid_or_not=True,
                                        is_completed=False)
                                except Exception:
                                    resp = False
                                    time.sleep(random.randint(1,2))
                                    infoLogger.info('Task {id} stop error (recover).\
                                                    Network error.'\
                                        .format(id=self.task['id']))
                                    errorLogger.error('\n'+str(traceback.format_exc())+'\n')

                            return data_dir
                else:
                    last_status = self.read_data_in_local(str(self.task['id']),'last_status')
                    self.set_status_transfer('DT', 'RC')
                    need_code = True
                    need_data = True
                    print(last_status)
                    # 看一下是下载过程中断还是运行过程中断
                    # 运行过程中断，需要判断哪个需要更新
                    if last_status == 'RN':
                        sc_local_time = self.read_data_in_local(str(self.task['id']),
                                    'script_last_update')
                        dt_local_time = self.read_data_in_local(str(self.task['id']),
                                    'data_last_update')
                        need_code = True if sc_local_time != self.task['script_last_update'] \
                                            else False
                        need_data = True if dt_local_time != self.task['data_last_update'] \
                                            else False
                        if need_code :
                            self.store_data_in_local(str(self.task['id']),
                                                        'script_last_update',
                                                        self.task['script_last_update'])
                        if need_data :
                            self.store_data_in_local(str(self.task['id']),'data_last_update',
                                                        self.task['data_last_update'])
                        print('sc_local_time:',sc_local_time)
                        print('dt_local_time:',dt_local_time)
                        print('sc_new_time:',self.task['script_last_update'])
                        print('dt_new_time:',self.task['data_last_update'])
                    print(need_code,need_data)
                    
                    infoLogger.info('Task {id} start download (recover).'
                                .format(id=self.task['id']))
                    down_th = threading.Thread(
                                target=client.get_task_data,
                                args=(self.task, 
                                    data_dir,self.task['gpu_id'],
                                    need_data, need_code,))
                    down_th.start()
                    while down_th.isAlive():
                        time.sleep(cf.QUERY_INTERVAL)
                        try:
                            info = client.get_task_info(self.task['id'])
                        except Exception:
                            info = None
                            time.sleep(random.randint(1,2))
                            infoLogger.info('Task {id} request task info error (recover).\
                                             Network error.'\
                                        .format(id=self.task['id']))
                            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                        if info == None:
                            continue
                        status = TaskStatusZh2En[info['status']]
                        if status == 'ST':
                            try:
                                self.set_task_desc(TaskStatus.DownloadStopped)
                                self.stop_thread_tasks(down_th)
                                self.set_status_transfer('ST', 'DT')
                            except Exception:
                                errorLogger.error('\n'+
                                    str(traceback.format_exc())+'\n')
                            else:
                                infoLogger.info('Task {task_id} stop download (recover).'
                                                .format(task_id=self.task['id']))
                            resp = False
                            while not resp:
                                try:
                                    upload_str = '\n' + ': '.join([self.task_status.name,
                                                self.task_desc])
                                    resp = self.client.post_task_output_str(
                                        task_id=self.task['id'],
                                        user_server_no=self.task['gpu_id'],
                                        output_string=upload_str,
                                        outstr_mode='append',
                                        valid_or_not=True,
                                        is_completed=False)
                                except Exception:
                                    resp = False
                                    time.sleep(random.randint(1,2))
                                    infoLogger.info('Task {id} stop error (recover).\
                                                     Network error.'\
                                                    .format(id=self.task['id']))
                                    errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                            return data_dir
                
                resp = False
                while not resp:
                    try:
                        resp = client.start_running_task(self.task['id'],
                                                        self.task['gpu_id'])
                    except Exception:
                        resp = False
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} confirm running error (recover).\
                                         Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')  
                    else:
                        resp = True
                infoLogger.info('Task {id} start train (recover).'.format(id=self.task['id']))
                self.set_status_transfer('RN', 'DT')


            # 默认python文件
            script_name = self.task['script_file'].split('/')[-1]  
            # 目前默认tar.gz
            datafile_name = self.task['data_file'].split('/')[-1]  
            compress_method = self.decompress_datafile(data_dir, datafile_name)
            #解压出错
            if compress_method == 'error':
                resp = False
                while not resp:
                    try:
                        upload_str = '\n' + ': '.join([
                                    self.task_status.name,
                                    self.task_desc])
                        resp = self.client.post_task_output_str(
                                    task_id=self.task['id'],
                                    user_server_no=self.task['gpu_id'],
                                    output_string=upload_str,
                                    valid_or_not=False,
                                    is_completed=True )
                    except Exception:
                        resp = False
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} post decompress error.\
                                         Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                        
                    
                self.set_status_transfer('IV', 'RN')

                debugLogger.debug('upload error info to server')
                return data_dir
            '''
            fix this place
            '''
            # run_script(data_dir, script_name, task['gpu_id'])
            res = -1
            try_time = 0
            script_res = False
            # 这里的写法可以改进，tenacity retry 后面可以改进一下写法
            while res != 0:
                try_time += 1
                res = self.run_script(data_dir, script_name, 
                                        self.task['gpu_id'], self.task['id'])
                # 没有正常结束,retry
                if res == 0:
                    script_res = True
                    self.set_task_desc(TaskStatus.TaskFinished)
                # 运行出错
                elif res == 1:
                    script_res = False
                    self.set_task_desc(TaskStatus.ScriptError)
                else:
                    script_res = False
                    # 看一下是否是超时或者服务器要求退出
                    # 如果是，则马上结束训练
                    if self.task_status == TaskStatus.TaskStopped or \
                        self.task_status == TaskStatus.TaskTimeOut:
                        
                        return data_dir
                    
                if try_time >= 1:
                    infoLogger.info('Retry {times} times. Post latest retry log.'
                                    .format(times=try_time))
                    self.task_desc += ' Upload after {} retries.'.format(try_time)
                    break
                if res != 0:
                    sleep_time = random.randint(30,90)
                    infoLogger.info('Task {id} return no-zero code.\
                                    Sleep {time}s and re-run the script.'
                                    .format(id=self.task['id'],time=sleep_time))
                    time.sleep(sleep_time)
                    
            uploadfile_name = self.compress_model_result(data_dir, compress_method)
            infoLogger.info('Post result to server. Task {task_id}'
                            .format(task_id=self.task['id']))

            # 上传结果不能停止
            upload_str = ': '.join([self.task_status.name,self.task_desc])
            resp = False
            while not resp:
                try:
                    client.post_task_result(self.task['id'], self.task['gpu_id'], 
                                    output_string=upload_str,
                                    valid_or_not=script_res,
                                    output_file=os.path.join(
                                        data_dir, uploadfile_name)
                                    )
                except Exception:
                    resp = False
                    time.sleep(random.randint(1,2))
                    infoLogger.info('Task {id} post result error. Network error.'\
                                        .format(id=self.task['id']))
                    errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                else:
                    # 上传成功就退出呗
                    resp = True
            
            if script_res:
                self.set_status_transfer('CP', 'RN')
            else:
                self.set_status_transfer('IV', 'RN')

        except Exception:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        else:
            return data_dir

    async def process_tasks(self):
        q_tasks = self.q_tasks

        while True:
            self.task = await q_tasks.get()
            # print('consumer{} process task in {}'.format(self.consumer_id,
            #                                     self.task['dir']))
            try:
                task_id = str(self.task['id'])
                # 新提交的任务或者恢复的任务，需要下载新的数据集
                # 写入本地数据库,带有文件夹
                # 改变本地数据库要加锁
                if TaskStatusZh2En[self.task['status']] == 'SB':
                    async with self.co_lock:
                        self.db = shelve.open(os.path.join(cf.LOCAL_TASKS_DIR,
                                                'tasks.dat'), writeback=True)
                        self.db[task_id] = self.task
                        self.db.close()
                elif TaskStatusZh2En[self.task['status']] == 'DT' or \
                    TaskStatusZh2En[self.task['status']] == 'RN':
                    async with self.co_lock:
                        self.db = shelve.open(os.path.join(cf.LOCAL_TASKS_DIR,
                                                    'tasks.dat'))
                        self.task['gpu_id'] = self.db[task_id]['gpu_id']
                        self.task['dir'] = self.db[task_id]['dir']
                        self.db.close()
                elif TaskStatusZh2En[self.task['status']] == 'RC':
                    async with self.co_lock:
                        self.db = shelve.open(os.path.join(cf.LOCAL_TASKS_DIR,
                                                    'tasks.dat'), writeback=True)
                        if str(self.task['id']) in self.db.keys():
                            self.task['gpu_id'] = self.db[task_id]['gpu_id']
                            self.task['dir'] = self.db[task_id]['dir']
                        # else:
                        #     self.db[task_id] = self.task
                        self.db.close()
                else:
                    errorLogger.error('Error task status')
                    self.clear_latest_task()
                    continue
                
                infoLogger.info('Process task {task_id}. Use GPU {index}. Start.'
                                .format(task_id= self.task['id'],
                                        index=self.task['gpu_id']))
                await self.co_loop.run_in_executor(
                                    None, self.train_model,)
                infoLogger.info('Process task {task_id}. Use GPU {index}. Over.'
                                .format(task_id= self.task['id'],
                                        index=self.task['gpu_id']))
                
                await asyncio.sleep(cf.QUERY_INTERVAL - 3) # 释放缓冲
                self.clear_latest_task()
            except Exception:
                errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                break
    