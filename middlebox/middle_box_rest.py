# -*- coding: utf-8 -*-

#  训练组件调用中间件的rest api
import os
from flask import Flask
from rest_fun import *
from middle_box_rest import *
from flask_restful import reqparse, abort, Api, Resource
from enum import Enum,unique
import json, threading

# 对接训练组件
@unique
class TBActions(Enum):
    task_over = 0 # 训练组件完成任务后，调用该接口

# 对接服务器连接组件
@unique
class ABActions(Enum):
    start_train = 0 # 收到训练开始指令，调用该接口

app = Flask(__name__)
api = Api(app)

# 为参数解析器增加key
parser = reqparse.RequestParser()
parser.add_argument('task_id')
parser.add_argument('model_name')
parser.add_argument('file_path')
parser.add_argument('task_name')
parser.add_argument('dataset_name')


# 拓展训练组件交互信息
TrainBoxActions = {
    'task_over': {'func_name': TBActions.task_over.name},
}

# 拓展服务器组件交互信息
AgentBoxActions = {
    'start_train' : {'func_name': ABActions.start_train.name},
}

# 拓展训练组件调用该接口的方法
def exe_fun_tba(tba_id, args):
    func_name = TrainBoxActions[tba_id]['func_name']
    if func_name == TBActions.task_over.name:
        fun = threading.Thread(target = send_model_2_server, args=(args['task_id'],args['model_name'],args['file_path'],))
        fun.start()
    else:
        print("error func")

# 拓展连接服务器组件调用该接口的方法
def exe_fun_aba(aba_id, args):
    print("args:", args)
    func_name = AgentBoxActions[aba_id]['func_name']
    if func_name == ABActions.start_train.name:
        fun = threading.Thread(target = send_task_2_trainbox, args=(args['task_name'], args['dataset_name'], args['file_path'],))
        fun.start()
    else:
        print("error func")


def abort_if_todo_doesnt_exist(id, action_list):
    if id not in action_list:
        msg = action_list
        msg = json.dumps(msg)
        abort(404, message=msg)

# TrainBox rest
# shows a single todo item and lets you delete a todo item
class TrainBox(Resource):
    def get(self, tba_id):
        abort_if_todo_doesnt_exist(tba_id, TrainBoxActions)
        return TrainBoxActions[tba_id]

    def post(self, tba_id):
        abort_if_todo_doesnt_exist(tba_id, TrainBoxActions)
        args = parser.parse_args()
        exe_fun_tba(tba_id, args) # 执行对应函数
        print("args:",args)
        return TrainBoxActions[tba_id], 200

# AgentBox rest
# aba : agentbox acitons
class AgentBox(Resource):
    def get(self, aba_id):
        abort_if_todo_doesnt_exist(aba_id, AgentBoxActions)
        return AgentBoxActions[aba_id]

    def post(self, aba_id):
        abort_if_todo_doesnt_exist(aba_id, AgentBoxActions)
        args = parser.parse_args()
        exe_fun_aba(aba_id, args) # 执行对应函数
        return AgentBoxActions[aba_id], 200

api.add_resource(TrainBox, '/trainbox2mid/<tba_id>') #
api.add_resource(AgentBox, '/agent2mid/<aba_id>') # agent 调用

if __name__ == '__main__':
    while True:
        print("Listen to 5001...")
        try:
            app.run(host="0.0.0.0",port=5001)
        except Exception as e:
                print("Listen Error:",e)

