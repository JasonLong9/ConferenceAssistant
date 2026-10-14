#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的音频处理和问答流程
"""

import requests
import time
import json

def test_complete_flow():
    """测试完整的处理和问答流程"""
    
    base_url = "http://127.0.0.1:8080"
    
    # 1. 首先检查服务状态
    print("1. 检查服务状态...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ 服务运行正常: {response.json()}")
    except Exception as e:
        print(f"❌ 服务检查失败: {e}")
        return
    
    # 2. 模拟上传音频文件（这里我们创建一个假的任务来测试）
    print("\n2. 模拟已处理的任务...")
    
    # 手动添加一个测试任务到系统中
    test_task_id = "test-task-12345"
    
    # 创建测试数据
    test_data = {
        "transcript": "这是一个测试会议的转录内容。张三说：大家好，我是张三。李四回答：你好张三，我是李四。",
        "cleaned": "张三: 大家好，我是张三。\n李四: 你好张三，我是李四。", 
        "minutes": "会议纪要：张三和李四进行了简单的问候交流。",
        "speaker_count": 2,
        "meeting_name": "测试会议",
        "chat_available": True
    }
    
    # 通过直接调用API来创建测试任务状态
    create_task_url = f"{base_url}/create_test_task"  # 我们需要添加这个临时接口
    
    # 3. 测试问答接口
    print("\n3. 测试问答接口 (GET参数)...")
    
    question = "会议中有几个人发言？"
    params = {
        "task_id": test_task_id,
        "question": question
    }
    
    try:
        response = requests.get(f"{base_url}/meeting/ask", params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 200:
            print("✅ GET参数接口测试成功!")
        else:
            print(f"❌ 接口返回错误: {response.json()}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 4. 测试URL编码
    print("\n4. 测试中文问题的URL编码...")
    import urllib.parse
    encoded_question = urllib.parse.quote("这次会议的主要内容是什么？")
    manual_url = f"{base_url}/meeting/ask?task_id={test_task_id}&question={encoded_question}"
    
    try:
        response = requests.get(manual_url)
        print(f"手动编码URL测试 - 状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 中文URL编码测试成功!")
        else:
            print(f"返回信息: {response.json()}")
    except Exception as e:
        print(f"❌ 手动URL测试失败: {e}")

if __name__ == "__main__":
    print("🧪 测试完整的音频处理和问答流程")
    print("=" * 60)
    test_complete_flow()