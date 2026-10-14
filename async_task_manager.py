import threading
import uuid
import time

# 全局任务状态字典
TASKS = {}

def generate_task_id():
    return str(uuid.uuid4())

def set_task_status(task_id, status, progress=0, result=None, error=None, stage=None):
    now = time.time()
    # 初始化任务时记录开始时间
    if task_id not in TASKS or TASKS[task_id].get('start_time') is None:
        start_time = now
    else:
        start_time = TASKS[task_id]['start_time']
    # 计算预计剩余时间
    elapsed = now - start_time
    if progress > 0 and progress < 100:
        estimated_total = elapsed / (progress / 100)
        eta = max(0, estimated_total - elapsed)
    else:
        eta = 0 if progress == 100 else None
    TASKS[task_id] = {
        "status": status,      # "pending", "processing", "done", "error"
        "progress": progress,  # 0-100
        "result": result,      # 处理结果
        "error": error,        # 错误信息
        "start_time": start_time,
        "eta": eta,           # 预计剩余秒数
        "stage": stage,       # 当前处理阶段描述
        "last_update": now    # 最后更新时间
    } 