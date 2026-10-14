#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查任务状态的简单脚本
"""

import requests
import sys

def check_task_status(task_id):
    """检查指定任务的状态"""
    base_url = "http://localhost:8080"
    
    try:
        response = requests.get(f"{base_url}/task_status", params={'task_id': task_id})
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'unknown')
            progress = result.get('progress', 0)
            eta = result.get('eta', 0)
            
            print(f"任务ID: {task_id}")
            print(f"状态: {status}")
            print(f"进度: {progress}%")
            if eta > 0:
                print(f"预计剩余时间: {eta}秒")
            
            return status
        else:
            print(f"查询失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"查询异常: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
    else:
        task_id = "bc35656c-725a-4449-aa31-aea80a826ca4"  # 从日志中看到的任务ID
    
    check_task_status(task_id)