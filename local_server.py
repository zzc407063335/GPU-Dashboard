# 导入socket库:
import socket
import threading
import time
import os
# 创建一个socket:
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 建立连接:
s.bind(('127.0.0.1', 9999))
s.listen()
print('Waiting for connection...')

def tcplink(sock, addr):
    print('Accept new connection from %s:%s...' % addr)
    sock.send('Welcome!'.encode())
    while True:
        data = sock.recv(1024).decode()
        time.sleep(1)
        if data == 'exit' or not data:
            break
        if data == 'data':
            print("send data!")
            file_size = os.stat('./mnist_model.h5').st_size
            sock.sendall(str(file_size).encode())
            print(sock.recv(1024)) # wait for start
            time.sleep(1)
            sent_size = 0
            with open('./mnist_model.h5','rb') as f:
                while (sent_size < file_size):
                    if (sent_size + 1024 > file_size):
                        line = f.read(file_size - sent_size)
                    else:
                        line = f.read(1024)
                    sock.sendall(line)
                    sent_size += len(line)
            print("send over!")
        else:
            msg = 'Hello, %s!' % data
            sock.send(msg.encode())
    sock.close()
    print('Connection from %s:%s closed.' % addr)

while True:
    # 接受一个新连接:
    sock, addr = s.accept()
    # 创建新线程来处理TCP连接:
    t = threading.Thread(target=tcplink, args=(sock, addr))
    t.start()
