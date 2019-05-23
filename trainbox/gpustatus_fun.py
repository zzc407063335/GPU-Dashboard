'''
获取GPU设备信息的api函数，可用于监控程序
'''

from pynvml import *
import json
# 系列名称
brandNames = {
    NVML_BRAND_UNKNOWN: "Unknown",
    NVML_BRAND_QUADRO: "Quadro",
    NVML_BRAND_TESLA: "Tesla",
    NVML_BRAND_NVS: "NVS",
    NVML_BRAND_GRID: "Grid",
    NVML_BRAND_GEFORCE: "GeForce",
}

# 首先应该初始化nvmlInit()

# 返回错误类型
def handleError(err):
    info = {'error_info':err.__str__()}
    return json.dumps(info)

# 获取GPU的数量
def GpuGetCounts():
    info = {'counts':nvmlDeviceGetCount()}
    return json.dumps(info)

def ValidIndex(index):
    if index >= nvmlDeviceGetCount() or index < 0:
        return False
    else:
        return True

# 获取设备名称
def GpuGetDeviceName(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info':'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        device_name = nvmlDeviceGetName(handle)
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'device_name':device_name}
        return json.dumps(info)

# 获取设备系列
def GpuGetDeviceBrand(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        brand_name = brandNames[nvmlDeviceGetBrand(handle)]
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'brand_name':brand_name}
        return json.dumps(info)

# 获取persistence_mode
def GpuGetDevicePersistenceModel(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        mode = 'Enabled' if (nvmlDeviceGetPersistenceMode(handle) != 0) else 'Disabled'
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'mode':mode}
        return json.dumps(info)

# 获取设备的UUID
def GpuGetDeviceUUID(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        uuid = nvmlDeviceGetUUID(handle)
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'uuid':uuid}
        return json.dumps(info)

# 获取风扇转速
def GpuGetDeviceFanSpeed(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        fan = str(nvmlDeviceGetFanSpeed(handle)) + " %"
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'fan':fan}
        return json.dumps(info)

# 获取工作状态,功耗状态
def GpuGetDevicePerformanceState(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        perfState = nvmlDeviceGetPowerState(handle)
        state = 'P%s' % perfState
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'power_state':state}
        return json.dumps(info)

# 获取Gpu内存使用情况,json
def GpuGetDeviceMemory(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        mem_info = nvmlDeviceGetMemoryInfo(handle)
        mem_total = str(mem_info.total / 1024 / 1024) + ' MiB'
        mem_used = str(mem_info.used / 1024 / 1024) + ' MiB'
        mem_free = str(mem_info.total / 1024 / 1024 - mem_info.used / 1024 / 1024) + ' MiB'
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'mem_total':mem_total,'mem_used':mem_used,'mem_free':mem_free}
        info = json.dumps(info)
        return info

# Bar1 内存使用 尚未明确这个数据在GPU架构中的角色
def GpuGetDeviceBar1Memory(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        memInfo = nvmlDeviceGetBAR1MemoryInfo(handle)
        mem_total = str(memInfo.bar1Total / 1024 / 1024) + ' MiB'
        mem_used = str(memInfo.bar1Used / 1024 / 1024) + ' MiB'
        mem_free = str(memInfo.bar1Total / 1024 / 1024 - memInfo.bar1Used / 1024 / 1024) + ' MiB'
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'mem_total': mem_total, 'mem_used': mem_used, 'mem_free': mem_free}
        info = json.dumps(info)
        return info

# 获取温度
def GpuGetDeviceTemperature(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        temp = str(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)) + ' C'
        temp_shutdown =  str(nvmlDeviceGetTemperatureThreshold(handle, NVML_TEMPERATURE_THRESHOLD_SHUTDOWN)) + ' C'
        temp_slowdown =  str(nvmlDeviceGetTemperatureThreshold(handle, NVML_TEMPERATURE_THRESHOLD_SLOWDOWN)) + ' C'
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {"cur_temp":temp,"temp_shutdown":temp_shutdown,"temp_slowdown":temp_slowdown}
        return json.dumps(info)

# 获取设备利用率
def GpuGetDeviceUtilization(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        util = nvmlDeviceGetUtilizationRates(handle)
        (util_int, ssize) = nvmlDeviceGetEncoderUtilization(handle)
        encoder_util = str(util_int) + ' %'
        (util_int, ssize) = nvmlDeviceGetDecoderUtilization(handle)
        decoder_util = str(util_int) + ' %'
        gpu_util = str(util.gpu) + " %"
        mem_util = str(util.memory) + " %"
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'gpu_util': gpu_util, 'mem_util': mem_util, 'encoder_util': encoder_util, 'decoder_util':decoder_util}
        return json.dumps(info)

def GpuGetDevicePowerUsage(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        powDraw = (nvmlDeviceGetPowerUsage(handle) / 1000.0)  # 功率消耗
        powDrawStr = '%.2f W' % powDraw
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {'power_usage':powDrawStr}
        return json.dumps(info)

# 返回gpu的功率信息
def GpuGetDevicePowerInfo(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        powMan = nvmlDeviceGetPowerManagementMode(handle)
        powManStr = 'Supported' if powMan != 0 else 'N/A'

        powLimit = (nvmlDeviceGetPowerManagementLimit(handle) / 1000.0) # 设定的功率上限
        setting_powLimit = '%.2f W' % powLimit
        powLimit = (nvmlDeviceGetPowerManagementDefaultLimit(handle) / 1000.0)
        default_powLimit = '%.2f W' % powLimit
        powLimit = nvmlDeviceGetPowerManagementLimitConstraints(handle) #强制的功率上下限
        powLimitStrMin = '%.2f W' % (powLimit[0] / 1000.0)
        powLimitStrMax = '%.2f W' % (powLimit[1] / 1000.0)
        powLimit = (nvmlDeviceGetEnforcedPowerLimit(handle) / 1000.0) # 强制的功率限制，与设定的功率上限类似？
        enforcedPowLimitStr = '%.2f W' % powLimit
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        info = {}
        info['bool_managementmode'] = powManStr
        info['setting_powLimit'] = setting_powLimit
        info['default_powLimit'] = default_powLimit
        info['enforcedPowLimitStr'] = enforcedPowLimitStr # 与设定的限制有差别？待定
        info['powLimitStrMin'] = powLimitStrMin
        info['powLimitStrMax'] = powLimitStrMax
        return json.dumps(info)

# 返回gpu的进程占用情况
def GpuGetDeviceProcess(gpu_index):
    if not ValidIndex(gpu_index):
        error_info = {'error_info': 'error gpu index'}
        return json.dumps(error_info)
    # 确保程序能够正确执行，异常不能这样写，待改进
    try:
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        proc = nvmlDeviceGetComputeRunningProcesses(handle)
        info = {}
        proc_counts = len(proc)
        info['proc_counts'] = proc_counts
        info['processes'] = {}
        for i in range(0, proc_counts):
            key = 'proc%d' % (i + 1)
            p = proc[i]
            content = {}
            try:
                name = nvmlSystemGetProcessName(p.pid).decode('utf-8')
                if (p.usedGpuMemory == None):
                    mem = 'N\A'
                else:
                    mem = '%d MiB' % (p.usedGpuMemory / 1024 / 1024)
            except NVMLError as err:
                if err.__str__() == "Not Found":
                    #查询的时候这个进程刚好消失
                    continue
                else:
                    error_info = handleError(err)
                    return error_info
            else:
                content['pid'] = p.pid
                content['name'] = name
                content['mem_usage'] = mem
                info['processes'][key] = content
    except NVMLError as err:
        error_info = handleError(err)
        return error_info
    else:
        return json.dumps(info)

# this is not exectued when module is imported
if __name__ == "__main__":
    nvmlInit()
    print(GpuGetDeviceProcess(0))
