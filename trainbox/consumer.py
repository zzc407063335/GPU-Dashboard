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

class TaskConsumer(object):
    client: TaskClient
    q_tasks: asyncio.Queue # 任务队列
    co_loop: asyncio.unix_events._UnixSelectorEventLoop
    def __init__(self,cs_id):
        self.consumer_id = cs_id
        self.task = None
        self.time_out = cf.TIME_OUT
        self.task_timer: threading.Timer
        self.task_subproc = None

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
                print('undefined decompress method')
                pass
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

    def kill_time_out_task(self, subproc):
        try:
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
            pass
        self.task_timer = threading.Timer(self.time_out, self.kill_time_out_task, 
                                            [subproc])
        self.task_timer.start()
            
    def run_script(self, data_dir, script_name, gpu_index, task_id):
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
            infoLogger.info('Task {task_id}. Processes more than {count}. Waiting'
                            .format(task_id=task_id,count=cf.TASK_COUNTS_MAX))
            proc_counts = 0
            for index in range(cf.REGISTER_GPU_COUNT):
                proc_counts += ls.GpuGetDeviceProcessCounts(index)['proc_counts']

        try:
            debugLogger.debug("start train")
            # 创建
            stdout = open(log_file, 'w+')
            stderr = open(err_file, 'w+')
            subproc = subprocess.Popen(args=cmd, bufsize=0, shell=True, stdout=subprocess.PIPE,
                        stderr=stderr.fileno(), preexec_fn=os.setsid, cwd=data_dir)
            infoLogger.info('Start train. Subprocess ID:{pid}'
                            .format(pid=subproc.pid))
            self.task_subproc = subproc
            self.set_task_timer(self.time_out, subproc)
            
            line = ''
            while len(line) >= 1 or subproc.poll() == None:
                # 每次读取512个字符
                line = subproc.stdout.read(512).decode('utf-8')
                stdout.write(line)
                stdout.flush()
                print(line)
                time.sleep(0.2)
                # client.post_line() 实时输出反馈给服务器
            res = subproc.returncode
            # subproc.communicate()
        except BaseException:
            self.task_timer.cancel()
            # 执行过程中出现了错误,例如ctl+c
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            os.killpg(subproc.pid,9)
            subproc.kill()
            subproc.communicate()

        else:
            self.task_timer.cancel()
            debugLogger.debug(res)
            if res == 0:
                debugLogger.debug("success")
                infoLogger.info('Finish task. Subprocess ID:{pid}'.format(
                                    pid=subproc.pid))
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
                                .format(task_id=task_id,pid=subproc.pid,returncode=res))
                    os.killpg(subproc.pid,9)
                except BaseException:
                    errorLogger.error('\n'+str(traceback.format_exc())+'\n')
            stdout.flush()
            stderr.flush()
            stdout.close()
            stderr.close()
        finally:
            self.task_subproc = None
            return res
    
    def train_model(self):
        client = self.client
        data_dir = self.task['dir']
        try:
            # 训练过程出错，不需要再重新下载数据集
            # 注意:目前没有增加数据集下载过程出错的差错控制
            # 正在运行状态,注意gpu_id 对应于服务器端的user_server_no
            if(self.task['status'] != 'RN'):
                client.confirm_request(self.task['id'],self.task['gpu_id'])
                client.get_task_data(task=self.task, 
                                    data_dir=data_dir, 
                                    user_server_no=self.task['gpu_id'])
            # 默认python文件
            script_name = self.task['script_file'].split('/')[-1]  
            # 目前默认tar.gz
            datafile_name = self.task['data_file'].split('/')[-1]  
            compress_method = self.decompress_datafile(data_dir, datafile_name)
            '''
            fix this place
            '''
            # run_script(data_dir, script_name, task['gpu_id'])
            res = -1
            try_time = 0
            script_res = False
            while res != 0:
                try_time += 1
                client.start_running_task(self.task['id'],self.task['gpu_id'])
                res = self.run_script(data_dir, script_name, 
                                        self.task['gpu_id'], self.task['id'])
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
                                    .format(id=self.task['id'],time=sleep_time))
                    time.sleep(sleep_time)
                    
            uploadfile_name = self.compress_model_result(data_dir, compress_method)
            infoLogger.info('Post result to server. Task {task_id}'
                            .format(task_id=self.task['id']))
            client.post_task_result(self.task['id'], self.task['gpu_id'], 
                                    output_string='task finished',
                                    valid_or_not=script_res,
                                    output_file=os.path.join(
                                        data_dir, uploadfile_name)
                                    )
        except Exception:
            errorLogger.error('\n'+str(traceback.format_exc())+'\n')
        else:
            return data_dir

    async def process_tasks(self):
        q_tasks = self.q_tasks
        while True:
            self.task = await q_tasks.get()
            print('consumer{} process task in {}'.format(self.consumer_id,
                                                self.task['dir']))
            try:
                infoLogger.info('Process task {task_id}. \
                                Use GPU {gpu_id}'
                                .format(task_id= self.task['id'],
                                        gpu_id= self.task['gpu_id']))
                res = await self.co_loop.run_in_executor(
                                    None, self.train_model,)
            except Exception:
                errorLogger.error('\n'+str(traceback.format_exc())+'\n')
                break
    