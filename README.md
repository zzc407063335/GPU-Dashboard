## 使用规则
#### 支持pytorch、keras, tensorflow目前待测试
假设需要训练模型model.py<br>
数据集的名称为dataset_name.tar.gz(或者 dataset\_name.zip)，数据集中包含a.txt与b.txt的两个文件,并且包含一个子文件夹subfolder，里面包含c.txt文件
#### 虚拟的文件结构如下：
```
│   model.py   
│	dataset_name.tar.gz 
└── dataset_name (自动生成)
│   │   a.txt
│   │   b.txt
│   └───subfolder
│       │   c.txt
│ 
└── result (自动生成)
│       │  pytorch.pt
│       │  keras.h5
│       │  error.log
│       │  info.log
│
-----------------------
```
### 数据集导入
用户需要上传需要运行的模型文件 **model.py**，以及压缩后的数据集**dataset_name.tar.gz(.zip)**<br>
其中用户在编写model.py里引入数据集数据时，按照上述文件结构进行编写,**dataset_name**以及数据集文件中的子文件夹名**subfolder**，用户自己指定和命名<br>
例如：<br>

```python
# model.py 文件中按照如下规则读入数据

# 如下即可读入主文件夹中的a.txt
file_path = './dataset_name/a.txt'
f = open(file_path,'r')
f.close()

# 如下即可读入子文件夹中的c.txt
file_path = './dataset_name/subfolder/c.txt'
f = open(file_path,'r')
f.close()
```
#### 注意，dataset\_name 与 subfolder 的名称用户可以自己指定，上传压缩包和model.py文件即可，系统会自动在model.py的同一目录下解压出与压缩包同名的dataset\_name目录，用户直接读入即可。
### 模型保存及日志结果

系统自动在model.py同一目录下创建result目录，用户在代码中保存模型时，直接指定path为'result'，即可。

```python
# model.py中按如下路径保存模型

# pytorch模型保存
save_dir = './result'
model_result = 'pytorch.pt'
torch.save(model.state_dict(), os.path.join(save_dir, model_result))

# keras模型保存
save_dir = './result'
model_result = 'keras.h5'
model_path = os.path.join(save_dir, model_name)
model.save(model_path)
```
用户只需在model.py中指定path指向'./result'即可，error.log 与 info.log自动为用户生成，其中error.log保存了model.py在模型加载中的错误与配置日志，info.log为用户在model.py中打印的一些日志，例如print()的结果等。<br>
最后result文件中的结果压缩后反馈给用户
