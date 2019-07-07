# -*- coding: utf-8 -*-
from flask import Flask
from flask_cors import CORS
from flask_restful import reqparse, abort, Api, Resource
from enum import Enum, unique
import local_service

# 中间件调用训练组件的rest api

app = Flask(__name__)
api = Api(app)
CORS(app)

@unique
class GpuInfoType(Enum):
    GpuGetCounts = 0
    GpuGetDeviceName = 1
    GpuGetDeviceBrand = 2
    GpuGetDevicePersistenceModel = 3
    GpuGetDeviceUUID = 4
    GpuGetDeviceFanSpeed = 5
    GpuGetDevicePerformanceState = 6
    GpuGetDeviceMemory = 7
    GpuGetDeviceBar1Memory = 8
    GpuGetDeviceTemperature = 9
    GpuGetDeviceUtilization = 10
    GpuGetDevicePowerUsage = 11
    GpuGetDevicePowerInfo = 12
    GpuGetDeviceProcessDetails = 13
    GpuGetDeviceProcessCounts = 14
# parser = reqparse.RequestParser()

QUERYS = {
    'gpu_counts': GpuInfoType.GpuGetCounts.name,
    'gpu_name': GpuInfoType.GpuGetDeviceName.name,
    'gpu_brand': GpuInfoType.GpuGetDeviceBrand.name,
    'gpu_pmode': GpuInfoType.GpuGetDevicePersistenceModel.name,  # persistence mode
    'gpu_uuid': GpuInfoType.GpuGetDeviceUUID.name,
    'gpu_fan': GpuInfoType.GpuGetDeviceFanSpeed.name,
    'gpu_perfstate': GpuInfoType.GpuGetDevicePerformanceState.name,
    'gpu_mem': GpuInfoType.GpuGetDeviceMemory.name,
    'gpu_bar1mem': GpuInfoType.GpuGetDeviceBar1Memory.name,
    'gpu_temp': GpuInfoType.GpuGetDeviceTemperature.name,
    'gpu_util': GpuInfoType.GpuGetDeviceUtilization.name,
    'gpu_power': GpuInfoType.GpuGetDevicePowerUsage.name,
    'gpu_powerinfo': GpuInfoType.GpuGetDevicePowerInfo.name,
    'gpu_proc': GpuInfoType.GpuGetDeviceProcessDetails.name,
    'gpu_procounts':GpuInfoType.GpuGetDeviceProcessCounts.name
}


def abort_if_todo_doesnt_exist(id):
    if id not in QUERYS:
        msg = "error api call"
        abort(404, message=msg)

# 根据函数名字调用函数


def gpuinfo_exe_fun(query_id, args):
    # 不带参数，获取GPU数量
    if QUERYS[query_id] == GpuInfoType.GpuGetCounts.name:
        exe_fun = getattr(local_service, GpuInfoType.GpuGetCounts.name)
        res = exe_fun()
        return res

    else:
        exe_fun = getattr(local_service, QUERYS[query_id])
        try:
            res = exe_fun(int(args['gpu_index']))
        # 调用错误异常
        except Exception as err:
            info = {'error_info': err.__str__()}
            return info
        else:
            return res

# GPU Query
class GPUQuery(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('gpu_index')

    def get(self, query_id):
        abort_if_todo_doesnt_exist(query_id)
        return QUERYS[query_id]

    def post(self, query_id):
        abort_if_todo_doesnt_exist(query_id)
        args = self.parser.parse_args()
        res = gpuinfo_exe_fun(query_id, args)
        return res, 200


api.add_resource(GPUQuery, '/gpuinfo/<query_id>')