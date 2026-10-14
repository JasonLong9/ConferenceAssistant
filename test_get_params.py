#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修改后的GET参数接口
"""

import requests
import urllib.parse

def test_get_params_api():
    """测试使用GET参数的问答接口"""
    
    # API基础URL
    base_url = "http://127.0.0.1:8080"
    
    # 测试参数
    task_id = "be486adf-37af-4995-8222-0ad34016f1e8"
    question = "会议中有多少人发言？"
    
    # 构建GET请求URL
    params = {
        "task_id": task_id,
        "question": question
    }
    
    # URL编码参数
    url = f"{base_url}/meeting/ask"
    
    print(f"测试URL: {url}")
    print(f"参数: {params}")
    print("-" * 50)
    
    try:
        # 发送GET请求
        response = requests.get(url, params=params)
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"响应数据: {result}")
        else:
            print("❌ 请求失败!")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保服务器在 8080 端口运行")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_with_encoded_url():
    """测试手动编码的URL"""
    
    task_id = "be486adf-37af-4995-8222-0ad34016f1e8"
    question = "会议中有多少人发言？"
    
    # 手动构建URL
    encoded_question = urllib.parse.quote(question)
    url = f"http://127.0.0.1:8080/meeting/ask?task_id={task_id}&question={encoded_question}"
    
    print(f"\n手动编码的URL: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    print("🧪 测试修改后的GET参数接口")
    print("=" * 50)
    
    test_get_params_api()
    test_with_encoded_url()