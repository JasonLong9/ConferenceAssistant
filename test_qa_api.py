#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试问答API接口
验证JSON请求体格式的修复效果
"""

import requests
import json

# 配置
BASE_URL = "http://127.0.0.1:8080"

# 从日志中可以看到已完成的任务ID
TEST_TASK_ID = "9c471a83-c8fc-41e4-9072-3bb19c985b0e"  # 8.20音频处理的任务ID

def test_qa_api():
    """测试问答API接口"""
    print("=== 测试会议问答API接口 ===")
    
    # 准备请求数据
    url = f"{BASE_URL}/meeting/ask"
    headers = {
        "Content-Type": "application/json"
    }
    
    # 测试问题列表
    test_questions = [
        "会议中有多少人发言？",
        "这次会议的主要内容是什么？",
        "Speaker_0主要说了什么？",
        "会议持续了多长时间？"
    ]
    
    print(f"📋 使用任务ID: {TEST_TASK_ID}")
    print(f"🔗 请求URL: {url}")
    print(f"📤 请求头: {headers}")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- 测试问题 {i} ---")
        print(f"❓ 问题: {question}")
        
        # 构造请求体
        data = {
            "task_id": TEST_TASK_ID,
            "question": question
        }
        
        print(f"📨 请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        try:
            # 发送请求
            response = requests.post(url, headers=headers, json=data)
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    answer = result.get('data', {}).get('answer', '')
                    print(f"✅ 问答成功")
                    print(f"💡 答案: {answer[:200]}{'...' if len(answer) > 200 else ''}")
                else:
                    print(f"❌ 业务错误: {result.get('msg')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"🔍 错误详情: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        
        print("-" * 50)

def check_task_status():
    """检查任务状态"""
    print("\n=== 检查任务状态 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/task_result", params={"task_id": TEST_TASK_ID})
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'done':
                result = data.get('result', {})
                print(f"✅ 任务已完成")
                print(f"🎯 识别说话人数: {result.get('speaker_count', 0)}")
                print(f"💬 智能问答可用: {result.get('chat_available', False)}")
                return True
            else:
                print(f"⚠️ 任务状态: {data.get('status')}")
                return False
        else:
            print(f"❌ 状态查询失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 状态查询异常: {e}")
        return False

if __name__ == "__main__":
    print("🚀 会议问答API测试工具")
    print("=" * 60)
    
    # 先检查任务状态
    if check_task_status():
        # 测试问答接口
        test_qa_api()
    else:
        print("💥 任务未完成或不存在，无法进行问答测试")
        print(f"💡 请确认任务ID '{TEST_TASK_ID}' 是否正确且已完成处理")
    
    print("\n🎉 测试完成!")
    print("\n📖 在Apifox中的正确配置方式:")
    print("1. 方法: POST")
    print("2. URL: http://127.0.0.1:8080/meeting/ask")
    print("3. Headers: Content-Type: application/json")
    print("4. Body (raw JSON): {\"task_id\": \"your_task_id\", \"question\": \"your_question\"}")