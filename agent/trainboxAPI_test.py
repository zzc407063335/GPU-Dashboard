import requests

action = "gpu_mem"
url = "http://train_box:5001/gpuinfo/"  + action
data = {"gpu_index":0}
r = requests.post(url,data=data)
print(r.text)

