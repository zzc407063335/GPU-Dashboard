# -*- coding: utf-8 -*-

import requests
import time
import os, sys, traceback, random, fcntl
import subprocess, threading
import json
import asyncio, ctypes, inspect
import conn_file_t as cf
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

class TaskTrainer(object):
    
    def __init__(self):
        self.trainer_id = cf.CS_ID
        self.time_out = cf.TIME_OUT
        self.task_timer: threading.Timer
        self.task_subproc = None
        self.db=None
        self.task=None
        self.task_status = TaskStatus.UnKownError
        self.task_desc = StatusDesc[self.task_status.value]
        self.client = TaskClient(cf.USER_NAME, cf.USER_PASS)
    def init_task(self):
        self._opendb(os.path.join(cf.LOCAL_TASKS_DIR,
                                'tasks.dat'),mode='c')
        self.task = self.db[str(cf.TASK_ID)]
        self._closedb()
    
    def _opendb(self, filename, mode='c'):       
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

    def set_status_transfer(self, new_status, last_status):
        self.store_data_in_local(str(self.task['id']),
                                        'status', new_status)
        self.store_data_in_local(str(self.task['id']),
                                        'last_status', last_status)

    def store_data_in_local(self, task_id, task_key, task_value):
        self._opendb(filename=os.path.join(cf.LOCAL_TASKS_DIR,
                                'tasks.dat'),mode='c')
        self.db[str(task_id)][task_key] = task_value
        self._closedb()

    def read_data_in_local(self, task_id, task_key):
        self._opendb(filename=os.path.join(cf.LOCAL_TASKS_DIR,
                                'tasks.dat'),mode='c')
        res = None
        if str(task_id) in self.db.keys():
            res = self.db[str(task_id)][task_key]
        else:
            res = None
        self._closedb()
        return res
    
    # 设置超时时长
    def set_time_out(self, time):
        self.time_out = time
    
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

    # run_scriptin docker
    def run_script(self, data_dir, script_name, gpu_index, task_id):
        # 目前支持python训练文件
        # tf keras pytorch 应该分开？

        # PYTHONUNBUFFERED=1 默认不使用缓存，实时获取STDOUT输出 
        cmd = 'CUDA_VISIBLE_DEVICES={index} PYTHONUNBUFFERED=1 \
                 python {script}'\
            .format(index=gpu_index, script=script_name)

        # 0xxxxxxxxxx/result
        # 创建result 文件夹
        if not os.path.exists(os.path.join(data_dir, cf.LOCAL_RESULT_DIR)):
            os.makedirs(os.path.join(data_dir, cf.LOCAL_RESULT_DIR))

        log_file = os.path.join(data_dir, 
                                cf.LOCAL_RESULT_DIR, 
                                cf.LOG_INFO_NAME)
        # err_file = os.path.join(data_dir, 
        #                         cf.LOCAL_RESULT_DIR, 
        #                         cf.LOG_ERROR_NAME)
        try:
            debugLogger.debug("start train")
            # 创建
            stdout = open(log_file, 'w+')
            subproc = subprocess.Popen(args=cmd, bufsize=0, shell=True, 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.STDOUT, 
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
                # 反馈输出
                resp = False
                while not resp:
                    try:
                        # 网络原因可能出错，这里缺乏重传机制，写死一直请求
                        resp = self.client.post_task_output_str(
                                            task_id=self.task['id'],
                                            user_server_no=self.task['gpu_id'], 
                                            output_string=line)
                    except Exception:
                        resp = False
                        time.sleep(random.randint(1,2))
                        infoLogger.info('Task {id} post string error. Network error.'\
                                        .format(id=self.task['id']))
                        errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                if TaskStatusZh2En[resp] == 'ST': 
                    self.stop_task(self.task_subproc)
                    self.set_status_transfer('ST','RN')
                    upload_str = '\n'+': '.join([self.task_status.name,self.task_desc])+'\n'
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
                                .format(task_id=task_id,
                                        pid=subproc.pid,
                                        returncode=res))
                    os.killpg(subproc.pid,9)
                except BaseException:
                    errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            stdout.flush()
            stdout.close()
        finally:
            res = subproc.returncode
            return res
    
if __name__ == '__main__':
    trainer = TaskTrainer()
    trainer.init_task()
    script_name = trainer.task['script_file'].split('/')[-1]
    datafile_name = trainer.task['data_file'].split('/')[-1]
    suffix_name = datafile_name.split('.')[-1]
    if suffix_name == 'gz':
        suffix_name = 'tar.gz' if \
                        datafile_name.split('.')[-2] == 'tar' else 'gz'
    data_dir = os.path.join('/home/fq-user'
                            , trainer.task['dir'].split('/')[-1])
    res = -1
    try_time = 0
    script_res = False
    while res != 0:
        try_time += 1
        res = trainer.run_script(data_dir, script_name, 
                            trainer.task['gpu_id'], trainer.task['id'])
        # 没有正常结束,retry
        if res == 0:
            script_res = True
            trainer.set_task_desc(TaskStatus.TaskFinished)
                # 运行出错
        elif res == 1:
            script_res = False
            trainer.set_task_desc(TaskStatus.ScriptError)
        else:
            script_res = False
            # 看一下是否是超时或者服务器要求退出
             # 如果是，则马上结束训练
            if trainer.task_status == TaskStatus.TaskStopped or \
                trainer.task_status == TaskStatus.TaskTimeOut:             
                os._exit(res)
                    
        if try_time >= 1:
            infoLogger.info('Retry {times} times. Post latest retry log.'
                                    .format(times=try_time))
            trainer.task_desc += ' Upload after {} retries.'.format(try_time)
            break
        if res != 0:
            sleep_time = random.randint(30,90)
            infoLogger.info('Task {id} return no-zero code.\
                            Sleep {time}s and re-run the script.'
                            .format(id=trainer.task['id'],time=sleep_time))
            time.sleep(sleep_time)
    uploadfile_name = trainer.compress_model_result(data_dir, suffix_name)
    infoLogger.info('Post result to server. Task {task_id}'
                            .format(task_id=trainer.task['id']))

    # 上传结果不能停止
    upload_str = ': '.join([trainer.task_status.name,trainer.task_desc])
    
    resp = False
    while not resp:
        try:
            trainer.client.post_task_result(trainer.task['id'], 
                                trainer.task['gpu_id'], 
                                output_string=upload_str,
                                valid_or_not=script_res,
                                output_file=os.path.join(
                                    data_dir, uploadfile_name)
                            )
        except Exception:
            resp = False
            time.sleep(random.randint(1,2))
            infoLogger.info('Task {id} post result error. Network error.'\
                                .format(id=trainer.task['id']))
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        else:
            # 上传成功就退出呗
            resp = True
            
    if script_res:
        trainer.set_status_transfer('CP', 'RN')
    else:
        trainer.set_status_transfer('IV', 'RN')
    trainer.task_timer.cancel()
    