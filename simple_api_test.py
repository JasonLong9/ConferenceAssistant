#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import os

def test_basic_apis():
    """测试基础API接口"""
    base_url = "http://localhost:8080"
    
    print("=== 测试基础接口 ===")
    
    # 1. 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        print(f"根路径: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  服务状态: {data.get('status')}")
            print(f"  可用接口: {list(data.get('endpoints', {}).keys())}")
    except Exception as e:
        print(f"根路径测试失败: {e}")
    
    # 2. 测试健康检查
    try:
        response = requests.get(f"{base_url}/health")
        print(f"健康检查: {response.status_code}")
        if response.status_code == 200:
            print(f"  健康状态: {response.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}")
    
    # 3. 测试文档接口
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"API文档: {response.status_code}")
    except Exception as e:
        print(f"API文档测试失败: {e}")

def test_simple_upload():
    """测试简单上传但不等待完成"""
    base_url = "http://localhost:8080"
    audio_file = "test_file/admin.MP3"
    
    print("\n=== 测试音频上传 ===")
    
    if not os.path.exists(audio_file):
        print(f"测试文件不存在: {audio_file}")
        return None
        
    file_size = os.path.getsize(audio_file)
    print(f"文件大小: {file_size / 1024:.2f} KB")
    
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': (os.path.basename(audio_file), f, 'audio/mpeg')}
            response = requests.post(f"{base_url}/audio2summary_async", files=files, timeout=10)
            
        print(f"上传响应: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"任务ID: {task_id}")
            return task_id
        else:
            print(f"上传失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"上传异常: {e}")
        return None

def check_task_status_once(task_id):
    """检查任务状态一次"""
    if not task_id:
        return
        
    base_url = "http://localhost:8080"
    
    print(f"\n=== 检查任务状态 ===")
    
    try:
        response = requests.get(f"{base_url}/task_status", params={"task_id": task_id})
        print(f"状态查询: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"任务状态: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"状态查询失败: {response.text}")
            
    except Exception as e:
        print(f"状态查询异常: {e}")

def test_existing_interfaces():
    """测试已有的其他接口"""
    base_url = "http://localhost:8080"
    
    print(f"\n=== 测试其他接口 ===")
    
    # 测试会话状态接口（用假的task_id）
    fake_task_id = "test-task-123"
    
    try:
        response = requests.get(f"{base_url}/meeting/chat/status", params={"task_id": fake_task_id})
        print(f"会话状态接口: {response.status_code}")
        if response.status_code in [200, 404]:
            print(f"  响应: {response.json()}")
    except Exception as e:
        print(f"会话状态接口异常: {e}")
    
    # 测试问答接口（用假数据）
    try:
        payload = {"task_id": fake_task_id, "question": "测试问题"}
        response = requests.post(f"{base_url}/meeting/ask", json=payload, timeout=5)
        print(f"问答接口: {response.status_code}")
        if response.status_code in [200, 400, 404]:
            print(f"  响应: {response.json()}")
    except Exception as e:
        print(f"问答接口异常: {e}")

if __name__ == "__main__":
    print("🔍 ConferenceAssistant API 简单测试")
    
    # 基础接口测试
    test_basic_apis()
    
    # 上传测试
    task_id = test_simple_upload()
    
    # 状态检查
    check_task_status_once(task_id)
    
    # 其他接口测试
    test_existing_interfaces()
    
    print("\n✅ 简单测试完成")