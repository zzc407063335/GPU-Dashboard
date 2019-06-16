import sys
import time
import socket
from enum import Enum,unique
import json
import threading
import os

@unique
class MessageType(Enum):
    Register = 0 # Sun的value被设定为0
    SendModel = 1
    SendData = 2
    SendTrainOrder = 3
    SendMidRes = 4
    DjangoOrder = 5

machines_socks = {}


def tcplink(sock, addr):
    print('Accept new connection from %s:%s...' % addr)
    sock.send('Welcome!'.encode())
    machine_id = ""
    while True:
        data = sock.recv(1024)
        print(data)
        if data:
            data.decode('utf-8')
            data = json.loads(data)
            if data['msg_type'] == 0:
                # register
                # if addr[0] != '127.0.0.1': # modify this when deploy in the cloud
                machine_id = data['machine_id']
                print(machine_id)
                machines_socks[data['machine_id']] = sock  # this step must stored in database,here is showing a demo
                print(data['machine_id'], machines_socks[data['machine_id']])
            elif data['msg_type'] == 1: # send model
                embed_data = data['embed_data']
                model_path = embed_data['model_path']
                machine_id = embed_data['machine_id']
                if machine_id not in machines_socks:
                    print("error machine")
                    continue
                else:
                    if machines_socks[machine_id] == "":
                        print("machine offline")
                        continue

                sock_machines = machines_socks[machine_id]
                if sock_machines == "":
                    print("link is closed")
                    continue
                file_size = os.stat(model_path).st_size
                msg = {'msg_type':MessageType.SendModel.value,'embed_data':{'file_size':file_size, 'model_name':'mnist_model'}}
                msg = json.dumps(msg)
                print(msg)
                sock_machines.sendall(msg.encode())
                time.sleep(3) # block to avoid packet sticking, needs more complicated design
                sent_size = 0
                with open(model_path, 'rb') as f:
                    while (sent_size < file_size):
                        if (sent_size + 1024 > file_size):
                            line = f.read(file_size - sent_size)
                        else:
                            line = f.read(1024)
                        sock_machines.sendall(line)
                        sent_size += len(line)
                print("send over!")

            elif data['msg_type'] == 2:
                pass  # send data
            elif data['msg_type'] == 3:
                pass  # send train order
            elif data['msg_type'] == 4:
                print("Receive middle result. loss:%s, accuracy:%s" % (data['loss'], data['accuracy']))
            elif data['msg_type'] == 5:  # from django
                # first send model, use order 1
                # next send data, use order 2
                # then send training order
                for k, v in data.items():
                    print(k, v)

                msg = {'msg_type': 3, 'embed_data': {'model_name':'mnist_model','epochs': 1, 'batch_size': 128, 'img_rows': 28, 'img_cols': 28,
                                                     'num_classes': 10}}
                msg = json.dumps(msg)
                machine_id = data['machine_id']
                if machine_id not in machines_socks:
                    print("error machine")
                    continue
                else:
                    if machines_socks[machine_id] == "":
                        print("machine offline")
                        continue
                sock_machines = machines_socks[machine_id]
                sock_machines.sendall(msg.encode())
                print("send trianing order!")
            else:
                print("unknown orders!")

        else:
            print("data is null")
            break
    sock.close()
    machines_socks[machine_id] = ""
    print('Connection from %s:%s closed.' % addr)


def main(port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('', port))
  s.listen(10)
  while True:
      # receive a link:
      print("listen")
      sock, addr = s.accept()
      # new thread to process the request:
      t = threading.Thread(target=tcplink, args=(sock, addr))
      t.start()


if __name__ == '__main__':
  try:
    port = int(sys.argv[1])
  except (ValueError, IndexError):
    sys.exit('which port to listen?')
  main(port)
