
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 建立连接:
s.connect(('127.0.0.1', 9999))
# 接收欢迎消息:
print(s.recv(1024))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.f

# while True:
#     data = input()
#     if data == 'exit' or not data:
#         print("close")
#         break
#     if data == 'data':
#         s.send(data.encode())
#         file_size = int(s.recv(4096).decode())
#         print("data size:%d"%file_size)
#         s.send("start".encode())
#         recv_size = 0
#         with open('new_model.h5','wb') as f:
#             while True:
#                 if recv_size == file_size:
#                     break
#                 data = s.recv(1024)
#                 f.write(data)
#                 recv_size += len(data)
#         print("save over")
#         break
#     s.send(data.encode())
#     data = s.recv(1024).decode()
#     print(s.getpeername(),s.getsockname(),data)
#
# s.send('end'.encode())
# s.close()
#
