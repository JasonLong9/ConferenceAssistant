#!/usr/bin/env python3
"""
查找已完成任务并测试问答功能
"""

import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:8080"

def find_completed_tasks():
    """尝试找到一些已完成的任务ID"""
    # 检查输出目录，看有没有最近的处理结果
    output_dir = "temp_output"
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        meeting_files = [f for f in files if f.startswith("会议纪要_")]
        if meeting_files:
            print(f"发现 {len(meeting_files)} 个会议纪要文件")
            return meeting_files[:3]  # 返回前3个
    return []

def test_with_mock_task():
    """用一个模拟的已完成任务测试"""
    # 创建一个简单的测试任务
    mock_task_id = "test-completed-task-123"
    
    print("测试模拟已完成任务的问答功能...")
    
    # 测试问答接口
    question_data = {
        "task_id": mock_task_id,
        "question": "这是一个测试问题"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/meeting/ask", json=question_data, timeout=10)
        print(f"问答接口响应状态: {response.status_code}")
        print(f"问答接口响应内容: {response.text}")
    except Exception as e:
        print(f"问答接口测试错误: {e}")
    
    # 测试问答状态接口
    try:
        response = requests.get(f"{BASE_URL}/meeting/chat/status", 
                              params={'task_id': mock_task_id}, timeout=10)
        print(f"问答状态接口响应状态: {response.status_code}")
        print(f"问答状态接口响应内容: {response.text}")
    except Exception as e:
        print(f"问答状态接口测试错误: {e}")
    
    # 测试对话历史接口
    try:
        response = requests.get(f"{BASE_URL}/meeting/chat/history", 
                              params={'task_id': mock_task_id}, timeout=10)
        print(f"对话历史接口响应状态: {response.status_code}")
        print(f"对话历史接口响应内容: {response.text}")
    except Exception as e:
        print(f"对话历史接口测试错误: {e}")

def test_interface_edge_cases():
    """测试接口的边缘情况"""
    print("测试接口边缘情况...")
    
    # 测试空参数
    test_cases = [
        {
            'name': '问答接口-空任务ID',
            'url': f"{BASE_URL}/meeting/ask",
            'method': 'POST',
            'data': {"task_id": "", "question": "test"}
        },
        {
            'name': '问答接口-空问题',
            'url': f"{BASE_URL}/meeting/ask", 
            'method': 'POST',
            'data': {"task_id": "test-id", "question": ""}
        },
        {
            'name': '问答接口-缺少参数',
            'url': f"{BASE_URL}/meeting/ask",
            'method': 'POST', 
            'data': {"task_id": "test-id"}
        },
        {
            'name': '任务状态-空任务ID',
            'url': f"{BASE_URL}/task_status",
            'method': 'GET',
            'params': {"task_id": ""}
        },
        {
            'name': '任务状态-缺少参数',
            'url': f"{BASE_URL}/task_status",
            'method': 'GET',
            'params': {}
        }
    ]
    
    for case in test_cases:
        try:
            if case['method'] == 'POST':
                response = requests.post(case['url'], json=case.get('data', {}), timeout=5)
            else:
                response = requests.get(case['url'], params=case.get('params', {}), timeout=5)
            
            print(f"[{case['name']}] 状态: {response.status_code}")
            print(f"  响应: {response.text[:100]}...")
            
        except Exception as e:
            print(f"[{case['name']}] 错误: {e}")
        print()

if __name__ == "__main__":
    print("开始测试已完成任务和接口边缘情况")
    print("=" * 50)
    
    # 查找已完成任务
    completed = find_completed_tasks()
    if completed:
        print(f"发现已完成任务: {completed}")
    else:
        print("未发现已完成任务文件")
    
    print()
    
    # 测试模拟任务
    test_with_mock_task()
    print()
    
    # 测试边缘情况
    test_interface_edge_cases()