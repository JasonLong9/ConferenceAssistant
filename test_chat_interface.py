#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_chat_interfaces():
    """测试问答接口"""
    base_url = "http://localhost:8080"
    task_id = "c672fd80-dc13-4274-825a-830265e64d0d"
    
    print("🔍 测试ConferenceAssistant 问答接口")
    print(f"任务ID: {task_id}")
    
    # 1. 测试会话状态
    print("\n=== 测试会话状态 ===")
    try:
        response = requests.get(f"{base_url}/meeting/chat/status", params={"task_id": task_id})
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"异常: {e}")
    
    # 2. 测试问答功能
    print("\n=== 测试问答功能 ===")
    test_questions = [
        "这个会议的主要内容是什么？",
        "会议讨论了哪些健康相关的话题？",
        "谁是这次会议的主要发言人？",
        "锡的作用是什么？",
        "会议提到了多少个省份缺锡？"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- 问题 {i}: {question} ---")
        try:
            payload = {
                "task_id": task_id,
                "question": question
            }
            
            response = requests.post(f"{base_url}/meeting/ask", json=payload, timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    answer = data.get('data', {}).get('answer', '')
                    print(f"✅ 回答: {answer}")
                    print(f"对话计数: {data.get('data', {}).get('conversation_count', 0)}")
                else:
                    print(f"❌ 业务错误: {data.get('msg')}")
            else:
                print(f"❌ HTTP错误: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    # 3. 测试对话历史
    print("\n=== 测试对话历史 ===")
    try:
        response = requests.get(f"{base_url}/meeting/chat/history", params={"task_id": task_id})
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                conversations = data.get('data', {}).get('conversations', [])
                print(f"✅ 对话历史: {len(conversations)}条记录")
                for idx, conv in enumerate(conversations[-3:], 1):  # 显示最后3条
                    print(f"  {idx}. Q: {conv.get('question', '')[:50]}...")
                    print(f"     A: {conv.get('answer', '')[:50]}...")
            else:
                print(f"❌ 业务错误: {data.get('msg')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 4. 测试清空对话历史
    print("\n=== 测试清空对话历史 ===")
    try:
        response = requests.delete(f"{base_url}/meeting/chat/clear", params={"task_id": task_id})
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                print(f"✅ 清空成功: {data.get('data', {}).get('message', '')}")
            else:
                print(f"❌ 业务错误: {data.get('msg')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
    test_chat_interfaces()