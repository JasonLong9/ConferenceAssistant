#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试优化后的API接口
"""

import requests
import json
import time

def test_meeting_ask_api():
    """测试meeting/ask接口"""
    base_url = "http://127.0.0.1:8080"
    
    print("=== 测试 /meeting/ask 接口 ===")
    
    # 测试1: 缺少请求体
    print("\\n1. 测试缺少请求体...")
    try:
        response = requests.post(f"{base_url}/meeting/ask")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试2: 错误的请求格式
    print("\\n2. 测试错误的请求格式...")
    try:
        response = requests.post(
            f"{base_url}/meeting/ask",
            data="invalid_data"
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试3: 正确格式但缺少参数
    print("\\n3. 测试缺少task_id...")
    try:
        response = requests.post(
            f"{base_url}/meeting/ask",
            json={"question": "测试问题"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试4: 正确格式但缺少question
    print("\\n4. 测试缺少question...")
    try:
        response = requests.post(
            f"{base_url}/meeting/ask",
            json={"task_id": "test-task-id"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试5: 空的task_id和question
    print("\\n5. 测试空的task_id和question...")
    try:
        response = requests.post(
            f"{base_url}/meeting/ask",
            json={"task_id": "", "question": ""}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试6: 不存在的task_id
    print("\\n6. 测试不存在的task_id...")
    try:
        response = requests.post(
            f"{base_url}/meeting/ask",
            json={"task_id": "non-existent-task", "question": "测试问题"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\\n=== 接口测试完成 ===")

def test_root_endpoint():
    """测试根端点"""
    print("\\n=== 测试根端点 ===")
    try:
        response = requests.get("http://127.0.0.1:8080/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"根端点测试失败: {e}")

def test_docs_endpoint():
    """测试文档端点"""
    print("\\n=== 测试API文档 ===")
    try:
        response = requests.get("http://127.0.0.1:8080/docs")
        print(f"文档页面状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ API文档可访问")
        else:
            print("❌ API文档不可访问")
    except Exception as e:
        print(f"文档端点测试失败: {e}")

def main():
    """主测试函数"""
    print("🧪 ConferenceAssistant API 接口测试")
    print("请确保服务已启动: uvicorn web_service:app --reload")
    
    # 等待用户确认
    input("\\n按回车键开始测试...")
    
    # 测试根端点
    test_root_endpoint()
    
    # 测试文档端点
    test_docs_endpoint()
    
    # 测试问答接口
    test_meeting_ask_api()
    
    print("\\n🎯 测试建议:")
    print("1. 确保请求Content-Type为application/json")
    print("2. 请求体必须包含task_id和question字段")
    print("3. task_id必须是已完成的任务ID")
    print("4. 示例正确请求:")
    print('   curl -X POST http://127.0.0.1:8080/meeting/ask \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"task_id": "your-task-id", "question": "会议讨论了什么?"}\'')

if __name__ == "__main__":
    main()