import requests
import time,subprocess,os
from conn_profile import *
'''

api = '/trainbox2mid/<id>'
@unique
class TBActions(Enum):
    task_over = 0 # 训练组件完成任务后，调用该接口
    json format: 'task_id' 完成的任务名称
                 'model_name' 存下来的模型名称
                 'file_path' 指定到对应的存储
'''
def send_rest_api(url,msg):
    try:
        r = requests.post(url,data = msg)
        return r
    except Exception as e:
        print("Request Error:", e)

def send_task_over_2_server(task_id, model_name, file_path):
    print("send_task_over_2_server")
    # api = "/trainbox2mid/task_over"
    # url = MIDDLE_BOX_CONTAINER_NAME + ":" + MIDDLE_BOX_CONTAINER_PORT
    # url += api
    # # 这里直接string就好
    # msg = { 'task_id': task_id,
    #         'model_name': model_name,
    #         'file_path': file_path
    # }
    # r = send_rest_api(url,msg)
    # print(r.status_code)
    # if


def train_model(path="./",task_name = "",dataset_name = ""):
    print(path,task_name,dataset_name)
    order = "python "
    order = order + path + task_name # + " " + dataset_name
    print(order)

    # 执行前应该检查GPU设备是否在应用内被占用

    try:
        res = os.system(order)# 执行shell命令
        print("res:",res)
        if res == 0:
            print("success")
        else:
            print("error")
            # 成功执行
    except Exception as e:
        print("error:",e)
    # 待解决：如何确定模型训练完之后的文件？


    # 需要制定训练完之后模型路径、名称等,这里为测试
    # 这里需要添加差错控制，反馈给用户
    # notify middle_box
    # time.sleep(5)
    send_task_over_2_server(task_id=task_name, model_name="cnn", file_path=path)

