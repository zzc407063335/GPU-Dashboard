# -*- coding: utf-8 -*-

import requests
import time
import os, sys, traceback, random, fcntl
import subprocess, threading
import json
import asyncio, ctypes, inspect
from pynvml import *
from pprint import pprint
import conn_file_r as cf
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
    '已恢复':'RC',
    '已完成':'CP'
}

class TaskConsumer(object):
    client=TaskClient(cf.USER_NAME,cf.USER_PASS)
    q_tasks: asyncio.Queue # 任务队列
    co_loop: asyncio.unix_events._UnixSelectorEventLoop
    proc_tasks: list # 正在处理中的任务
    db: shelve.DbfilenameShelf
    co_lock: asyncio.locks.Lock # 共享协程锁，用于操作db
    # th_lock = threading.Lock() # 共享线程锁，用于train_model中操作db
    
    def __init__(self,cs_id):
        self.consumer_id = cs_id
        self.task = None
        self.time_out = cf.TIME_OUT
        self.task_timer: threading.Timer
        self.task_subproc = None
        self.task_status = TaskStatus.UnKownError
        self.task_desc = StatusDesc[self.task_status.value]
        self.owner = 'zzc407063335'
    
    def _opendb(self,filename,mode='c'):       
        lockfilemode = 'a'
        lockmode = fcntl.LOCK_EX  
        self.lockfd = open(filename+'.lck', lockfilemode)
        
        try:
            fcntl.flock(self.lockfd.fileno(), lockmode)
        except Exception:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            return (None, None)
        self.db = shelve.open(filename, flag=mode,\
                        writeback=True)

    def _closedb(self):
        self.db.close()
        fcntl.flock(self.lockfd.fileno(),fcntl.LOCK_UN)
        self.lockfd.close()

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
        # self.th_lock.acquire()
        self._opendb(filename=os.path.join(cf.LOCAL_TASKS_DIR,
                                'tasks.dat'),mode='c')
        self.db[str(task_id)][task_key] = task_value
        self._closedb()
        # self.th_lock.release()

    def read_data_in_local(self, task_id, task_key):
        # self.th_lock.acquire()
        self._opendb(filename=os.path.join(cf.LOCAL_TASKS_DIR,
                                'tasks.dat'),mode='c')
        res = None
        if str(task_id) in self.db.keys():
            res = self.db[str(task_id)][task_key]
        else:
            res = None
        self._closedb()
        # self.th_lock.release()
        return res
    # 设置超时时长

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
            errorLogger.error('\n'+str(traceback.format_exc())+'\21:56n')
        except IOError:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        else:
            return suffix_name

    def set_task_desc(self, _task_status):
        self.task_status = _task_status
        self.task_desc = StatusDesc[self.task_status.value]

    def run_script_in_container(self):
        user_data_dir = self.task['dir'].split('/')[-1]
        # 映射宿主机
        home_dir = cf.HOME_DIR
        owner = self.owner
        if 'framework' not in self.task:
            framework = 'all_in_one'
            version = 'v0.0.1'
        else:
            framework = self.task['framework']
            version = self.task['version']
        imagename = '/'.join([owner,framework]) + ':' + version
        containername = 'trainbox{cs_id}'.format(
                                    cs_id=self.consumer_id)
        cur_user = cf.CURRENT_UID
        # 注意taskdb需要虚拟文件路径一致
        
        # 有没有结束的容器
        try:
            check_out = os.popen('docker ps -a | \
                        grep -w {name}'.format(name=containername)).read()
            if check_out != '':
                _id = check_out.split()[0][:10]
                clear_cont = 'docker rm -f {cont_id}'.format(
                                    cont_id=_id)
                os.system(clear_cont)
        except:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            

        docker_cmd = ('docker run -d \
                        -v {host_data_dir}:{cont_data_dir} \
                        -v {host_task_dir}:{cont_task_dir} \
                        -v {host_log_dir}:{cont_logs_dir} \
                        -v /home/zzc/docker_test/app:/home/fq-user/zzc_test/   \
                        -e \"TASK_ID={task_id}\" \
                        -e \"CS_ID={cs_id}\" \
                        -e \"USER_NAME\"={username} \
                        -e \"USER_PASS\"={password} \
                        --name {cont_name} \
                        --user {user} \
                        --pid=host \
                        --runtime=nvidia \
                        {imagename}'.format(
                            host_data_dir=os.path.join(home_dir, 'data'
                                            ,user_data_dir),
                            cont_data_dir=os.path.join(cf.APP_HOME_DIR
                                            ,user_data_dir),
                            host_task_dir=os.path.join(home_dir,'tasks'),
                            cont_task_dir=os.path.join(cf.APP_HOME_DIR
                                            , 'tasks'),
                            host_log_dir=os.path.join(home_dir, 'logs'),
                            cont_logs_dir=os.path.join(cf.APP_HOME_DIR
                                            , 'logs'),
                            task_id=self.task['id'],
                            cs_id=self.consumer_id,
                            username=cf.USER_NAME,
                            password=cf.USER_PASS,
                            cont_name=containername,
                            user=cur_user,
                            imagename=imagename
                        ))
        # 取出容器id的前10位位置
        try:
            # 在训练前应该尝试关闭所有db操作
            self._closedb()
        except Exception:
            pass

        try:
            cont_id = os.popen(docker_cmd).read().split('\n')[0][:10]
            status = os.popen('docker ps | grep {id}'
                            .format(id=cont_id)).read()
            ctl = 0
            # 看看本地是不是训练结束了
            while ctl < 3:
                if status == '':
                    ctl = ctl + 1
                else:
                    ctl = 0
                time.sleep(2)
                status = os.popen('docker ps | grep {id}'
                            .format(id=cont_id)).read()
        except :
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                
        try:
            clear_cont = 'docker rm -f {cont_id}'.format(
                                cont_id=cont_id)
            res = os.system(clear_cont)
            infoLogger.info('Task {task_id} clear trainbox{cs_id}.'
                            .format(task_id=self.task['id'],
                                    cs_id=self.consumer_id))
        except Exception:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        else:
            if res != 0:
                errorLogger.error('Task {task_id} clear trainbox{cs_id} error.'
                                    .format(task_id=self.task['id'],
                                    cs_id=self.consumer_id))

    def train_model(self):
        client = self.client
        data_dir = self.task['dir']
        # import ipdb;ipdb.set_trace()
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
                    # 新来的需要存下来                                     
                    self._opendb(os.path.join(cf.LOCAL_TASKS_DIR,
                                            'tasks.dat'),mode='c')
                    self.db[str(self.task['id'])] = self.task
                    self._closedb()
                    infoLogger.info('Task {} save info. (recover)'.format(self.task['id']))
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
                    # 注意这里，一定要取出来最新的状态之后再转移
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

            # 目前默认tar.gz
            datafile_name = self.task['data_file'].split('/')[-1]  
            compress_method = self.decompress_datafile(
                                    data_dir, 
                                    datafile_name)
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
            # 所有上传和下载 tenacity retry 后面可以改进一下写法

            self.run_script_in_container()

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
                    # async with self.co_lock:
                    self._opendb(os.path.join(cf.LOCAL_TASKS_DIR,
                                            'tasks.dat'),mode='c')
                    self.db[task_id] = self.task
                    # print(self.db[task_id])
                    self._closedb()
                elif TaskStatusZh2En[self.task['status']] == 'DT' or \
                    TaskStatusZh2En[self.task['status']] == 'RN':
                    # async with self.co_lock:
                    self._opendb(os.path.join(cf.LOCAL_TASKS_DIR,
                                            'tasks.dat'),mode='c')
                    self.task['gpu_id'] = self.db[task_id]['gpu_id']
                    self.task['dir'] = self.db[task_id]['dir']
                    self._closedb()
                elif TaskStatusZh2En[self.task['status']] == 'RC':
                    # async with self.co_lock:
                    self._opendb(os.path.join(cf.LOCAL_TASKS_DIR,
                                            'tasks.dat'),mode='c')
                    if str(self.task['id']) in self.db.keys():
                        self.task['gpu_id'] = self.db[task_id]['gpu_id']
                        self.task['dir'] = self.db[task_id]['dir']
                    self._closedb()
                else:
                    errorLogger.error('Error task status')
                    self.clear_latest_task()
                    continue
                
                infoLogger.info('Process task {task_id}. Use GPU {index}. Start.'
                                .format(task_id= self.task['id'],
                                        index=self.task['gpu_id']))
                pprint(self.task)
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
    