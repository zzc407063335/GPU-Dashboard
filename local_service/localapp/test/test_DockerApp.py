import unittest
import os
import sys
import time
sys.path.append('..')

from threading import Thread
import asyncio, inspect, ctypes
from DockerApp.local_app import app 
from DockerApp.recv_producer import TaskProducer
from DockerApp.recv_consumer import TaskConsumer
import DockerApp.local_service
from mock import MagicMock, create_autospec, patch
from firstquadrants import TaskClient

# producer测试
task_sub = [{'id': 262,
  'name': 'sssssss',
  'task_desc': 'sssss',
  'script_file': '/media/tasks/2/code/483efef5871a8ce7/cifar10_cnn_keras_docker_test.py',
  'data_file': '/media/tasks/2/data/5babc800b3348833/cifar-10-batches-py.tar.gz',
  'add_time': '2019-06-20T04:53:36.240Z',
  'min_memory_size': 8.0,
  'min_hdisk_size': 5.0,
  'min_gpu_memory_size': 4.0,
  'status': '已提交',
  'flag':'测试',
  'script_last_update': '2019-06-23T13:29:00Z',
  'data_last_update': '2019-06-21T14:53:00Z'
  },
  {'id': 1,
  'name': 'zzzz',
  'task_desc': 'zzzz',
  'script_file': '/media/tasks/2/code/483efef51a8ce227/cifar10_cnn_keras_docker_test.py',
  'data_file': '/media/tasks/2/data/5babc800b3343223/cifar-10-batches-py.tar.gz',
  'add_time': '2019-06-20T04:53:36.250Z',
  'min_memory_size': 8.0,
  'min_hdisk_size': 5.0,
  'min_gpu_memory_size': 4.0,
  'status': '已恢复',
  'flag':'测试',
  'script_last_update': '2019-06-23T13:29:00Z',
  'data_last_update': '2019-06-21T14:53:00Z'
  },
   {'id': 1111,
  'name': 'zzzz',
  'task_desc': 'zzzz',
  'script_file': '/media/tasks/2/code/483efef51a8ce227/cifar10_cnn_keras_docker_test.py',
  'data_file': '/media/tasks/2/data/5babc800b3343223/cifar-10-batches-py.tar.gz',
  'add_time': '2019-06-20T04:53:36.250Z',
  'min_memory_size': 8.0,
  'min_hdisk_size': 5.0,
  'min_gpu_memory_size': 4.0,
  'status': '已恢复',
  'flag':'测试',
  'script_last_update': '2019-06-23T13:29:00Z',
  'data_last_update': '2019-06-21T14:53:00Z'
  }]

task_rn = [{'id': 263,
  'name': 'keras5epochs',
  'task_desc': '实时',
  'script_file': '/media/tasks/2/code/327d3f0ed864e0cf/cifar10_cnn_keras_docker_test.py',
  'data_file': '/media/tasks/2/data/49cd00f12e695c1f/cifar-10-batches-py.tar.gz',
  'add_time': '2019-06-19T09:13:17.714Z',
  'min_memory_size': 8.0,
  'min_hdisk_size': 5.0,
  'min_gpu_memory_size': 4.0,
  'status': '正在运行',
  'flag':'测试',
  'script_last_update': '2019-07-08T05:10:00Z',
  'data_last_update': '2019-06-21T14:53:00Z'
  }]

devices = [{'device_name': 'GeForce RTX 2080 Ti',
  'device_series': 'GeForce',
  'gpu_util': 0.0,
  'user_server_no': 0,
  'memory_size': 15.0,
  'memory_remain': 15.0,
  'hdisk_size': 50.0,
  'hdisk_remain': 50.0,
  'support_gpu': True,
  'gpu_memory_size': 10.73187255859375,
  'gpu_memory_remain': 10.73187255859375},
 {'device_name': 'GeForce RTX 2080 Ti',
  'device_series': 'GeForce',
  'gpu_util': 0.0,
  'user_server_no': 1,
  'memory_size': 15.0,
  'memory_remain': 15.0,
  'hdisk_size': 50.0,
  'hdisk_remain': 50.0,
  'support_gpu': True,
  'gpu_memory_size': 10.73187255859375,
  'gpu_memory_remain': 10.73187255859375}]

# consumer测试
cs_task_sub = [
{'add_time': '2019-06-30T13:55:38.794Z',
 'data_file': '/media/tasks/2/data/2a5b9853a1b0dd4d/ywb_MNIST.tar.gz',
 'data_last_update': '2019-06-30T13:55:00Z',
 'dir': '/home/fq-user/data/0x950xbd0x00x660x70xa90x350xd00xd00xb',
 'gpu_id': 1,
 'id': 222,
 'last_status': 'DT',
 'min_gpu_memory_size': 4.0,
 'min_hdisk_size': 5.0,
 'min_memory_size': 8.0,
 'name': '并发测试15',
 'script_file': '/media/tasks/2/code/11921e13f74c897d/pytorch.py',
 'script_last_update': '2019-07-07T11:30:33.426Z',
 'status': '已提交',
 'task_desc': '并发测试'
},
{'add_time': '2019-06-30T13:55:38.794Z',
 'data_file': '/media/tasks/2/data/2a5b9853a1b0dd4d/ywb_MNIST.tar.gz',
 'data_last_update': '2019-06-30T13:55:00Z',
 'dir': '/home/fq-user/data/0x950xbd0x00x660x70xa90x350xd00xd00xb',
 'gpu_id': 1,
 'id': 222,
 'last_status': 'DT',
 'min_gpu_memory_size': 4.0,
 'min_hdisk_size': 5.0,
 'min_memory_size': 8.0,
 'name': '并发测试15',
 'script_file': '/media/tasks/2/code/11921e13f74c897d/pytorch.py',
 'script_last_update': '2019-07-07T11:30:33.426Z',
 'status': '正在运行',
 'task_desc': '并发测试'
 },
{'add_time': '2019-06-30T13:55:38.794Z',
 'data_file': '/media/tasks/2/data/2a5b9853a1b0dd4d/ywb_MNIST.tar.gz',
 'data_last_update': '2019-06-30T13:55:00Z',
 'dir': '/home/fq-user/data/0x950xbd0x00x660x70xa90x350xd00xd00xb',
 'gpu_id': 1,
 'id': 222,
 'last_status': 'DT',
 'min_gpu_memory_size': 4.0,
 'min_hdisk_size': 5.0,
 'min_memory_size': 8.0,
 'name': '并发测试15',
 'script_file': '/media/tasks/2/code/11921e13f74c897d/pytorch.py',
 'script_last_update': '2019-07-07T11:30:33.426Z',
 'status': '已恢复',
 'task_desc': '并发测试'
 },
 {'add_time': '2019-06-30T13:55:38.794Z',
 'data_file': '/media/tasks/2/data/2a5b9853a1b0dd4d/ywb_MNIST.tar.gz',
 'data_last_update': '2019-06-30T13:55:00Z',
 'dir': '/home/fq-user/data/0x950xbd0x00x660x70xa90x350xd00xd00xb',
 'gpu_id': 1,
 'id': 222,
 'last_status': 'DT',
 'min_gpu_memory_size': 4.0,
 'min_hdisk_size': 5.0,
 'min_memory_size': 8.0,
 'name': '并发测试15',
 'script_file': '/media/tasks/2/code/11921e13f74c897d/pytorch.py',
 'script_last_update': '2019-07-07T11:30:33.426Z',
 'status': '已分配',
 'task_desc': '并发测试'
},
 {'add_time': '2019-06-30T13:55:38.794Z',
 'data_file': '/media/tasks/2/data/2a5b9853a1b0dd4d/ywb_MNIST.tar.gz',
 'data_last_update': '2019-06-30T13:55:00Z',
 'dir': '/home/fq-user/data/0x950xbd0x00x660x70xa90x350xd00xd00xb',
 'gpu_id': 1,
 'id': 222,
 'last_status': 'DT',
 'min_gpu_memory_size': 4.0,
 'min_hdisk_size': 5.0,
 'min_memory_size': 8.0,
 'name': '并发测试15',
 'script_file': '/media/tasks/2/code/11921e13f74c897d/pytorch.py',
 'script_last_update': '2019-07-07T11:30:33.426Z',
 'status': '错误状态',
 'task_desc': '并发测试'
 },
  {'add_time': '2019-06-30T13:55:38.794Z',
 'data_file': '/media/tasks/2/data/2a5b9853a1b0dd4d/ywb_MNIST.tar.gz',
 'data_last_update': '2019-06-30T13:55:00Z',
 'dir': '/home/fq-user/data/0x950xbd0x00x660x70xa90x350xd00xd00xb',
 'gpu_id': 1,
 'id': 222,
 'last_status': 'DT',
 'min_gpu_memory_size': 4.0,
 'min_hdisk_size': 5.0,
 'min_memory_size': 8.0,
 'name': '并发测试15',
 'script_file': '/media/tasks/2/code/11921e13f74c897d/pytorch.py',
 'script_last_update': '2019-07-07T11:30:33.426Z',
 'status': '已停止',
 'task_desc': '并发测试'
 }
]


# 模拟下载11s
def mock_download(task,data_dir,gpu_id,need_data,need_code):
    time.sleep(11)


class TestLocalService(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.debug = True

    def tearDown(self):
        pass
    
    def test_abort_if_todo_doesnt_exist(self):
        res = self.app.post('/gpuinfo/error_id', 
                                data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('error api call',
                                    json_data['message'])

    def test_get(self):
        res = self.app.get('/gpuinfo/error_id')
        json_data = res.get_json()
        self.assertEqual('error api call',
                                    json_data['message'])
        res = self.app.get('/gpuinfo/gpu_counts')
        json_data = res.get_json()
        self.assertEqual('GpuGetCounts',json_data)

    @patch('DockerApp.local_service.GpuGetCounts',
                        MagicMock(side_effect = Exception))
    def test_no_para_err(self):
        res = self.app.post('/gpuinfo/gpu_counts',data={})
        print(res)
        json_data = res.get_json()
        self.assertEqual('error when enroll nvidia library'
                                    ,json_data['message'])

    @patch('DockerApp.local_service.GpuGetDeviceName',
                        MagicMock(side_effect = Exception))
    def test_para_err(self):
        res = self.app.post('/gpuinfo/gpu_name',
                                data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('error when enroll nvidia library'
                                ,json_data['message'])

    @patch('DockerApp.local_service.GpuGetCounts',
                    MagicMock(return_value = {'counts':'2'}))
    def test_GpuGetCounts(self):
        res = self.app.post('/gpuinfo/gpu_counts',data={})
        print(res)
        json_data = res.get_json()
        self.assertEqual('2',json_data['counts'])
    
    @patch('DockerApp.local_service.GpuGetDeviceName',
            MagicMock(return_value = {'device_name':'NVIDIA'}))
    def test_GpuGetDeviceName(self):
        res = self.app.post('/gpuinfo/gpu_name',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('NVIDIA',json_data['device_name'])
    
    @patch('DockerApp.local_service.GpuGetDeviceBrand',
            MagicMock(return_value = {'brand_name':'Geforce'}))
    def test_GpuGetDeviceBrand(self):
        res = self.app.post('/gpuinfo/gpu_brand',data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('Geforce',json_data['brand_name'])
    
    @patch('DockerApp.local_service.GpuGetDevicePersistenceModel',
                MagicMock(return_value = {'mode':'Enabled'}))
    def test_GpuGetDevicePersistenceModel(self):
        res = self.app.post('/gpuinfo/gpu_pmode',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('Enabled',json_data['mode'])
    
    @patch('DockerApp.local_service.GpuGetDeviceUUID',
                MagicMock(return_value = {'uuid':'1234'}))
    def test_GpuGetDeviceUUID(self):
        res = self.app.post('/gpuinfo/gpu_uuid',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('1234',json_data['uuid'])
    
    @patch('DockerApp.local_service.GpuGetDeviceFanSpeed',
                MagicMock(return_value = {'fan':'27'}))
    def test_GpuGetDeviceFanSpeed(self):
        res = self.app.post('/gpuinfo/gpu_fan',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('27',json_data['fan'])
    
    @patch('DockerApp.local_service.GpuGetDevicePerformanceState',
                MagicMock(return_value = {'power_state':'P0'}))
    def test_GpuGetDevicePerformanceState(self):
        res = self.app.post('/gpuinfo/gpu_perfstate',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('P0',json_data['power_state'])
    
    @patch('DockerApp.local_service.GpuGetDeviceMemory',
                MagicMock(return_value = {'mem_total':'100'}))
    def test_GpuGetDeviceMemory(self):
        res = self.app.post('/gpuinfo/gpu_mem',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('100',json_data['mem_total'])
    
    @patch('DockerApp.local_service.GpuGetDeviceBar1Memory',MagicMock(
                            return_value = {'mem_used':'222'}))
    def test_GpuGetDeviceBar1Memory(self):
        res = self.app.post('/gpuinfo/gpu_bar1mem',data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('222',json_data['mem_used'])
    
    @patch('DockerApp.local_service.GpuGetDeviceTemperature',MagicMock(
                            return_value = {'cur_temp':'82'}))
    def test_GpuGetDeviceTemperature(self):
        res = self.app.post('/gpuinfo/gpu_temp',data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('82',json_data['cur_temp'])
    
    @patch('DockerApp.local_service.GpuGetDeviceUtilization',
                MagicMock(return_value = {'gpu_util':'45'}))
    def test_GpuGetDeviceUtilization(self):
        res = self.app.post('/gpuinfo/gpu_util',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('45',json_data['gpu_util'])
    
    @patch('DockerApp.local_service.GpuGetDevicePowerUsage',
        MagicMock(return_value = {'power_usage':'204.01'}))
    def test_GpuGetDevicePowerUsage(self):
        res = self.app.post('/gpuinfo/gpu_power',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('204.01',json_data['power_usage'])
    
    @patch('DockerApp.local_service.GpuGetDevicePowerInfo',
        MagicMock(return_value = {'powLimitStrMax':'250 W'}))
    def test_GpuGetDevicePowerInfo(self):
        res = self.app.post('/gpuinfo/gpu_powerinfo',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('250 W',json_data['powLimitStrMax'])
    
    @patch('DockerApp.local_service.GpuGetDeviceProcessCounts',
                MagicMock(return_value = {'proc_counts':'2'}))
    def test_GpuGetDeviceProcessCounts(self):
        res = self.app.post('/gpuinfo/gpu_procounts',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('2',json_data['proc_counts'])
    
    @patch('DockerApp.local_service.GpuGetDeviceProcessDetails',
                    MagicMock(return_value = {'proc_counts':'2',
                                    'processes':{'pid':'111'}}))
    def test_GpuGetDeviceProcessDetails(self):
        res = self.app.post('/gpuinfo/gpu_proc',
                                    data={'gpu_index':0})
        json_data = res.get_json()
        self.assertEqual('2',json_data['proc_counts'])
        self.assertEqual('111',json_data['processes']['pid'])

class TestTaskProducer(unittest.TestCase):

    def setUp(self):
        # main_loop = asyncio.get_event_loop()
        TaskProducer.proc_tasks = []
        self.producer = TaskProducer()
        self.client = MagicMock(TaskClient('username','password'))
        TaskProducer.client = self.client
        
        # 这里可能打破了nose本身的事件体系
        # 所以重新建立线程事件循环进行测试
        self.loop = asyncio.new_event_loop()
        TaskProducer.q_tasks = asyncio.Queue(
                loop=self.loop, maxsize=5)
        self.t = Thread(target=self.start_loop,args=(self.loop,))
        self.t.start()

    def start_loop(self,loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

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
    
    def tearDown(self):
        self.loop.stop()
        print('stop loop')
        self.stop_thread_tasks(self.t)
        print('stop thread')

    def test_append_proc_task(self):
        self.producer.append_proc_task(1)
        self.assertEqual(1,self.producer.proc_tasks[-1])
    
    def test_request_new_tasks(self):
        self.client.request_tasks = create_autospec(
                            self.client.request_tasks,
                            return_value = task_sub)
        new_tasks = self.producer.request_new_tasks(devices)
        self.assertEqual(new_tasks, task_sub)
    
    def test_request_unfin_tasks(self):
        self.client.request_running_tasks = create_autospec(
                            self.client.request_running_tasks,
                            return_value = task_rn)
        unfin_tasks = self.producer.request_unfin_tasks(devices)
        self.assertEqual(unfin_tasks,task_rn)

    # 测试 请求设备抛出异常
    def test_device_error(self):
        self.client.get_server_list = create_autospec(
                            self.client.get_server_list,
                            side_effect = Exception)
        asyncio.run_coroutine_threadsafe(
                                self.producer.request_for_tasks(),
                                self.loop)
        from DockerApp.conn_file_r import QUERY_INTERVAL
        time.sleep(QUERY_INTERVAL + 1)
        self.assertEqual(True,self.producer._err)
        
    # 测试 正常请求
    def test_request_for_tasks(self):
        self.client.get_server_list = create_autospec(
                            self.client.get_server_list,
                            return_value = devices)
        self.client.request_tasks = create_autospec(
                            self.client.request_tasks,
                            return_value = task_sub)
        self.client.request_running_tasks = create_autospec(
                            self.client.request_running_tasks,
                            return_value = task_rn)
        
        asyncio.run_coroutine_threadsafe(
                                self.producer.request_for_tasks(),
                                self.loop)
        # 模拟阻塞请求任务
        from DockerApp.conn_file_r import QUERY_INTERVAL
        time.sleep(2 * QUERY_INTERVAL + 1)

        async def get_data():
            tasks = []
            while not self.producer.q_tasks.empty():
                task = await self.producer.q_tasks.get()
                tasks.append(task)
            return tasks
        t_tasks = []
        t_tasks.extend(task_sub)
        t_tasks.extend(task_rn)
        future = asyncio.run_coroutine_threadsafe(get_data(),
                                                self.loop)
        # 等待处理完get_data
        time.sleep(1)
        r_tasks = future.result()
        for task in t_tasks:
            self.assertTrue(task in r_tasks)

class TestTaskConsumer(unittest.TestCase):

    def setUp(self):
        main_loop = asyncio.get_event_loop()
        TaskConsumer.q_tasks = asyncio.Queue(
                loop=main_loop, maxsize=10)
        TaskConsumer.proc_tasks = []
        self.consumer = TaskConsumer(1)
        self.client = MagicMock(TaskClient('username','password'))
        TaskConsumer.client = self.client
        # 这里可能打破了nose本身的事件体系
        # 所以重新建立线程事件循环进行测试
        self.loop = asyncio.new_event_loop()
        self.t = Thread(target=self.start_loop,args=(self.loop,))
        self.t.start()
        TaskConsumer.co_loop = self.loop

    def start_loop(self,loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

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
    
    def tearDown(self):
        self.loop.stop()
        print('stop loop')
        self.stop_thread_tasks(self.t)
        print('stop thread')
    
    # 优先测试
    def test_a_process_tasks(self):
        self.maxDiff=None
        self.consumer.train_model = create_autospec(
                                    self.consumer.train_model,
                                    return_value = '/sss')
        # 先把清理方法给屏蔽掉
        self.consumer.clear_latest_task = create_autospec(
                                    self.consumer.clear_latest_task,
                                    return_value = True
                                    )
        asyncio.run_coroutine_threadsafe(self.consumer.process_tasks(),
                                        self.loop)
        # 测试错误状态
        self.consumer.proc_tasks.append(cs_task_sub[4]['id'])
        self.consumer.q_tasks.put_nowait(cs_task_sub[4])
        # 等待consumer处理
        
        # 测试不关心的状态
        self.consumer.proc_tasks.append(cs_task_sub[5]['id'])
        self.consumer.q_tasks.put_nowait(cs_task_sub[5])
        # 等待consumer处理
        
        # 测试已提交任务
        self.consumer.proc_tasks.append(cs_task_sub[0]['id'])
        self.consumer.q_tasks.put_nowait(cs_task_sub[0])
        # 等待consumer处理
        time.sleep(2)
        import shelve
        db = shelve.open(os.path.join(os.getcwd(),'tasks/tasks.dat'))
        self.assertEqual(cs_task_sub[0],db[str(cs_task_sub[0]['id'])])
        db.close()

        # 测试正在运行任务
        self.consumer.proc_tasks.append(cs_task_sub[1]['id'])
        self.consumer.q_tasks.put_nowait(cs_task_sub[1])
        # 等待consumer处理
        time.sleep(2)
        import shelve
        db = shelve.open(os.path.join(os.getcwd(),'tasks/tasks.dat'))
        self.assertEqual(db[str(cs_task_sub[1]['id'])]['dir'],
                                self.consumer.task['dir'])
        db.close()

        # 测试已恢复
        self.consumer.proc_tasks.append(cs_task_sub[2]['id'])
        self.consumer.q_tasks.put_nowait(cs_task_sub[2])
        # 等待consumer处理
        time.sleep(2)
        import shelve
        db = shelve.open(os.path.join(os.getcwd(),'tasks/tasks.dat'))
        self.assertEqual(db[str(cs_task_sub[2]['id'])]['dir'],
                                self.consumer.task['dir'])
        db.close()

        # 测试已分配
        self.consumer.proc_tasks.append(cs_task_sub[3]['id'])
        self.consumer.q_tasks.put_nowait(cs_task_sub[3])
        # 等待consumer处理
        time.sleep(2)
        import shelve
        db = shelve.open(os.path.join(os.getcwd(),'tasks/tasks.dat'))
        self.assertEqual(db[str(cs_task_sub[3]['id'])]['dir'],
                                self.consumer.task['dir'])
        db.close()
    
    def test_clear_latest_task(self):
        self.consumer.proc_tasks.append(cs_task_sub[0]['id'])
        self.consumer.task = cs_task_sub[0]
        self.consumer.clear_latest_task()
        self.assertEqual(None,self.consumer.task)

    def test_set_status_transfer(self):
        self.consumer.task = cs_task_sub[0]
        self.consumer.set_status_transfer('DT','SB')
        status = self.consumer.read_data_in_local(self.consumer.task['id'],
                                            'status')
        last_status = self.consumer.read_data_in_local(self.consumer.task['id'],
                                            'last_status')
        self.assertEqual(status,'DT')
        self.assertEqual(last_status,'SB')

    def test_download_files(self):
        self.consumer.task = cs_task_sub[0]
        self.client.get_task_data = create_autospec(
                            self.client.get_task_data, 
                            side_effect = mock_download)
        # 测试下载停止
        self.client.get_task_info = create_autospec(
                            self.client.get_task_info,
                            side_effect = [None,{'status':'已停止'}])
        self.client.post_task_output_str = create_autospec(
                            self.client.post_task_output_str,
                            return_value = True)
        res = self.consumer.download_files('/mock/path')
        self.assertFalse(res)
        # 测试正常下载
        self.client.get_task_info = create_autospec(
                            self.client.get_task_info,
                            return_value={'status':'已分配'})

        res = self.consumer.download_files('/mock/path')
        self.assertTrue(res)
        # 测试网络出错，没有及时拿到停止指令
        # 不过这个情况实际应该很难出现
        self.client.get_task_info = create_autospec(
                            self.client.get_task_info,
                            side_effect=[{'status':'已分配'},Exception])
        res = self.consumer.download_files('/mock/path')
        self.assertTrue(res)
    # 注意这个测试时间的sleep
    # 并发的测试比较蛋疼，这里也会出现无法退出测试的情况，不过不影响覆盖率
    
    # 这个测试需要人为配合一下
    # 启动容器后需要测试人员stop模拟训练结束
    def test_train_model(self):
        self.consumer.consumer_id = 1
        self.client.get_task_data = create_autospec(
                            self.client.get_task_data, 
                            side_effect = mock_download)
        # 测试正常下载
        self.client.get_task_info = create_autospec(
                            self.client.get_task_info,
                            return_value={'status':'已分配'})
        # 不测试真实的文件解压缩
        self.consumer.decompress_datafile = create_autospec(
                            self.consumer.decompress_datafile,
                            return_value='zip')
        cmd = 'docker run -itd --name trainbox1 ubuntu:16.04 /bin/bash'
        # 先模拟一个没有退出的容器
        os.popen(cmd)
        time.sleep(2) #等容器启动
        self.consumer.get_docker_start_cmd = create_autospec(
                                self.consumer.get_docker_start_cmd,
                                return_value = cmd)
        # 已提交
        self.consumer.task = cs_task_sub[0]
        self.consumer.train_model()
        self.assertTrue(self.consumer._docker_over)
        
        # 正在运行
        self.consumer._docker_over = False
        self.consumer.task = cs_task_sub[1]
        self.consumer.train_model()
        self.assertTrue(self.consumer._docker_over)

        # 已恢复
        self.consumer._docker_over = False
        self.consumer.task = cs_task_sub[2]
        self.consumer.train_model()
        self.assertTrue(self.consumer._docker_over)
        # 已恢复
        self.consumer._docker_over = False
        self.consumer.task = cs_task_sub[2]
        # 这里测试来到一个本地没有的恢复任务
        import random
        self.consumer.task['id'] += random.randint(1,10000)
        self.consumer.train_model()
        self.assertTrue(self.consumer._docker_over)
        # 已分配
        self.consumer._docker_over = False
        self.consumer.task = cs_task_sub[3]
        self.consumer.train_model()
        self.assertTrue(self.consumer._docker_over)

if __name__=='__main__':
    unittest.main()
