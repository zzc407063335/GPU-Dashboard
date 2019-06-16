import socket
# orders from django
from enum import Enum,unique
import json
address = ('127.0.0.1', 5678)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(address)
print(s.recv(1024))

@unique
class MessageType(Enum):
    Register = 0 # Sun的value被设定为0
    SendModel = 1
    SendData = 2
    SendTrainOrder = 3
    SendMidRes = 4
    DjangoOrder = 5


while True:
    msg = input()
    if not msg:
        break
    if msg == '1':
        print("machine id:")
        name = input()
        if not name:
            print("error name")
            continue
        msg = {'msg_type': MessageType(int(msg)).value, 'embed_data':{'model_path':'./mnist_model.h5','machine_id':name}} # 后两项表明要传输的模型和数据集
        msg = json.dumps(msg)
        s.send(msg.encode())
    elif msg == '5':
        print("machine id:")
        name = input()
        msg = {'msg_type': MessageType(int(msg)).value, 'machine_id':name, 'task_id':1, 'model':1, 'dataset':1} # 后两项表明要传输的模型和数据集
        msg = json.dumps(msg)
        s.send(msg.encode())
    else:
        print("msg = 1 or msg = 5")
        continue

s.close()