import os
# -*- coding: utf-8 -*-
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from enum import Enum,unique
import json

@unique
class TaskType(Enum):
    train_model = 0

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('model_name')
parser.add_argument('dataset_name')
parser.add_argument('file_path')


TODOS = {
    'train_model': {'func': TaskType.train_model.value},
}


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        msg = TODOS
        msg = json.dumps(msg)
        abort(404, message=msg)


# Todo
# shows a single todo item and lets you delete a todo item
class Todo(Resource):
    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]


    def post(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        args = parser.parse_args()
        print(args)
        return TODOS[todo_id], 200

api.add_resource(Todo, '/todos/<todo_id>')

if __name__ == '__main__':
    app.run(debug=True)


# def train(path="./",name=""):
#     order = "python "
#     file_name = name
#     order = order + path + file_name
#     print(order)
#     os.system(order)
#
# train("./","torch_cnn.py")