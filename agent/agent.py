from __future__ import print_function

from conn_profile import *
import requests
import socket
from enum import Enum,unique
import json
import sys,time


@unique
class TaskType(Enum):
    train_model = 0


class ComputeNode(object):
    """docstring for ComputeNode."""
    def __init__(self, server_ip = '127.0.0.1', remote_port = 5678, machine_id = 'abc'):
        super(ComputeNode, self).__init__()
        self.server_ip = server_ip
        self.remote_port = remote_port
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.machine_id = machine_id
        self.exe_method = ""
    def set_node_machine_id(self,machine_id="abc"):
        self.machine_id = machine_id

    def receive_model(self,embed_data):
        file_size = embed_data['file_size']
        model_name = embed_data['model_name'] + '_' + self.machine_id + '.h5'
        print("data size:%d  model_name:%s" % (file_size, model_name))
        # self.soc.send("start".encode())
        print("start receive model")
        recv_size = 0
        with open(model_name, 'wb') as f:
            i = 0
            while True:
                if recv_size == file_size:
                    break
                data = self.soc.recv(1024)
                f.write(data)
                recv_size += len(data)
                i+=1
                if (i == 1000):
                    i = 0
                    print("%.2f%%"%(100.0*recv_size/file_size))
        print("100%")
        print("save over")

    def receive_data(self,embed_data):
        pass


    # 用这个函数先维护cookie？
    def connect(self):
        print("connect to server")
        self.soc.connect((self.server_ip,self.remote_port))
        print(self.soc.recv(1024).decode())
        # r = requests.post(url, data=msg)
        # cookies = r.cookies.get_dict()
    #
    def listen(self):# demo, directly use while true -----> should use events pool
        while True:
            data = self.soc.recv(1024)
            print(data)
            if data:
                data.decode('utf-8')
                data = json.loads(data)
                if data['msg_type'] == 1:
                    self.exe_method = self.receive_model
                elif data['msg_type'] == 2:
                    self.exe_method = self.receive_data
                # elif data['msg_type'] == 3:
                #     self.exe_method = self.train_model
                else:
                    print("unknown orders!")

                if self.exe_method:
                    self.exe_method(data['embed_data'])
            else:
                print("data is null")
                break

    # post ？
    def register(self):
        msg = {'msg_type': 0,'machine_id':self.machine_id}
        msg = json.dumps(msg)
        url = 'http://httpbin.org/post'
        r = requests.post(url, data=msg)
        print(r.text)
        cookies = r.cookies.get_dict()
        print (cookies)
        # self.send_msg(msg)

    # 暂时不用
    def send_msg(self,msg):
        print("send to %s:%d msg:%s"%(self.server_ip,self.remote_port, msg))
        self.soc.send(msg.encode())# tcp

    def send_order(self,order=0):
        if order == TaskType.train_model.value:
            url = TRAINING_CONTAINER_NAME + ":" + TRAINING_CONTAINER_PORT
            print(url)
            api = "/todos/train_model"
            model_name = 'torch_cnn.py'
            dataset_name = 'mnist'
            file_path = './'
            # 这里直接string就好
            msg = {'task_name': model_name,
                    'dataset_name': dataset_name,
                    'file_path':file_path
            }
            url = url + api
            r = requests.post(url, data=msg)
            print(r.status_code)
        # if
        else:
            print("waiting for extending")

    # 需要接口信息，获取训练数据及模型
    def get_model_data(self):
        pass

node = ComputeNode(server_ip=SERVER_IP,remote_port=REMOTE_PORT) # 注册方法，目前用machine_id标识不同机器，后面应该跟用户绑定

def start_rest_api():
    print("start client rest api")
    app.run(host="0.0.0.0", port=5001)


if __name__ == '__main__':
    try:
        name = sys.argv[1]
    except (ValueError, IndexError):
        sys.exit('what\'s your name? run python client.py yourname')

    try:
        node.set_node_machine_id(name)
        # node.connect()
        fun = threading.Thread(target=start_rest_api)
        fun.setDaemon(True)
        fun.start()
        while True:
            time.sleep(5)
            node.send_order(0)
    except KeyboardInterrupt:
        print('stopped by keyboard')


    # node.register()
    # node.listen()
