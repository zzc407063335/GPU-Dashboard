import requests
import time,json
from conn_profile import *
'''
调用训练组件接口api
api = /todos/<id>
@unique
class TaskType(Enum):
    train_model = 0
    json format: 'task_name' : 任务名称 
                 'dataset_name' ： 数据集名称
                 'file_path' ： 指向数据集的路径
'''

def send_rest_api(url,msg):
    try:
        r = requests.post(url,data = msg)
        return r
    except Exception as e:
        print("Request Error:", e)


def send_model_2_server(task_id, model_name, file_path):
    print("send to server:", task_id, model_name, file_path)
    msg = {'msg_type': 0, 'machine_id': "zzc"}
    msg = json.dumps(msg)
    url = 'http://httpbin.org/post'
    r = requests.post(url, data=msg)
    print(r.text)
    cookies = r.cookies.get_dict()
    print(cookies)
    # 实现发送模型给服务器


def send_task_2_trainbox(task_name="default", dataset_name="default",file_path="default"):
    url = TRAINING_CONTAINER_NAME + ":" + TRAINING_CONTAINER_PORT
    print(url)
    api = "/todos/train_model"
    # 这里直接string就好
    msg = {'task_name': task_name,
           'dataset_name': dataset_name,
           'file_path': file_path
    }
    url = url + api
    r = send_rest_api(url, msg)
    # if
    print("start_train")
    pass

