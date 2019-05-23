import os
# -*- coding: utf-8 -*-
from rest_fun import *
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from enum import Enum,unique
import json, threading

# 中间件调用训练组件的rest api

@unique
class TaskType(Enum):
    train_model = 0

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('task_name')
parser.add_argument('dataset_name')
parser.add_argument('file_path')


TODOS = {
    'train_model': {'func_name': TaskType.train_model.name},
}

QUERYS = {
    'train_model': {'func_name': TaskType.train_model.name},
}


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        msg = TODOS
        msg = json.dumps(msg)
        abort(404, message=msg)

def exe_fun(todo_id, args):
    func_name = TODOS[todo_id]['func_name']
    if func_name == TaskType.train_model.name:
        fun = threading.Thread(target=train_model,args=(args['file_path'],args['task_name'],args['dataset_name'],))
        fun.start()
    else:
        print("error func")


# Todo
# shows a single todo item and lets you delete a todo item
class Todo(Resource):
    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]


    def post(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        args = parser.parse_args()
        exe_fun(todo_id, args)
        print(args)
        # train(args['file_path'], args['task_name'], args['dataset_name'])
        return TODOS[todo_id], 200
# GPU Query
class GPUQuery(Resource):

    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]


    def post(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        args = parser.parse_args()
        exe_fun(todo_id, args)
        print(args)
        # train(args['file_path'], args['task_name'], args['dataset_name'])
        return TODOS[todo_id], 200

api.add_resource(Todo, '/todos/<todo_id>')
api.add_resource(GPUQuery, '/gpuinfo/<query_id>')

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5001)
