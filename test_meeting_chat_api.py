#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试会议问答API接口
"""

import requests
import json
import time
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8080"

def test_meeting_chat_api():
    """测试会议问答API功能"""
    print("=" * 60)
    print("会议问答API接口测试")
    print("=" * 60)
    
    # 模拟一个已完成的任务ID (通常由上传音频后获得)
    test_task_id = "test_meeting_chat_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 首先检查会话状态 (应该不存在)
    print("\n1. 检查会话状态...")
    try:
        response = requests.get(f"{BASE_URL}/meeting/chat/status", params={"task_id": test_task_id})
        result = response.json()
        print(f"会话状态检查: {result}")
        print(f"会话可用: {result['data']['available'] if result['code'] == 0 else False}")
    except Exception as e:
        print(f"检查会话状态失败: {e}")
    
    # 2. 模拟创建一个会话 (通常在音频处理完成后自动创建)
    print(f"\n2. 手动创建测试会话 (task_id: {test_task_id})...")
    
    from meeting_chat import meeting_chat_manager
    
    # 模拟会议内容
    test_cleaned = """【发言人A】我们今天讨论AI技术在企业中的应用，特别是在知识产权开发方面。这是一个非常重要的议题。

【发言人B】是的，我认为AI可以大大降低成本，提高效率。根据我们的调研，AI技术可以提高30%的工作效率。我建议我们投资100万人民币来开发这个项目。

【发言人A】那么时间安排呢？我们需要一个明确的时间表。

【发言人B】我建议3个月内完成第一阶段的开发，包括核心算法和基础架构。然后用6个月时间完成全部开发并上线。

【发言人A】听起来很合理。那么团队安排呢？

【发言人B】我们需要5个工程师，包括2个AI算法工程师，2个后端工程师，1个前端工程师。"""
    
    test_minutes = """# 会议纪要

**会议主题：** AI技术企业应用讨论会
**会议时间：** 2024年12月30日
**参会人员：** 发言人A、发言人B

## 主要决策
1. 投资100万人民币开发AI应用项目
2. 项目分为两个阶段：
   - 第一阶段：3个月完成核心开发
   - 第二阶段：6个月内完成全部开发并上线
3. 组建5人技术团队

## 预期效果
- AI技术可提高30%的工作效率
- 重点关注知识产权开发应用

## 团队配置
- 2个AI算法工程师
- 2个后端工程师  
- 1个前端工程师

## 后续行动
1. 准备项目预算申请
2. 开始招聘技术人员
3. 制定详细的项目计划"""
    
    # 创建会话
    session_created = meeting_chat_manager.create_session(test_task_id, test_cleaned, test_minutes)
    print(f"会话创建结果: {'成功' if session_created else '失败'}")
    
    if not session_created:
        print("无法创建测试会话，终止测试")
        return
    
    # 3. 再次检查会话状态
    print("\n3. 再次检查会话状态...")
    try:
        response = requests.get(f"{BASE_URL}/meeting/chat/status", params={"task_id": test_task_id})
        result = response.json()
        print(f"会话状态: {result}")
    except Exception as e:
        print(f"检查会话状态失败: {e}")
    
    # 4. 测试问答功能
    print("\n4. 测试会议问答功能...")
    
    test_questions = [
        "这次会议的主要决策是什么？",
        "项目预算是多少？",
        "项目的时间安排如何？", 
        "需要多少人的技术团队？",
        "AI技术预期能提高多少效率？",
        "发言人B对项目有什么建议？"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n问题{i}: {question}")
        try:
            response = requests.post(
                f"{BASE_URL}/meeting/ask",
                json={"task_id": test_task_id, "question": question},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["code"] == 0:
                    print(f"✓ 回答: {result['data']['answer']}")
                    print(f"  对话计数: {result['data']['conversation_count']}")
                else:
                    print(f"✗ 错误: {result['msg']}")
            else:
                print(f"✗ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"✗ 请求失败: {e}")
        
        # 避免请求太频繁
        time.sleep(1)
    
    # 5. 获取对话历史
    print("\n5. 获取对话历史...")
    try:
        response = requests.get(f"{BASE_URL}/meeting/chat/history", params={"task_id": test_task_id})
        if response.status_code == 200:
            result = response.json()
            if result["code"] == 0:
                print(f"✓ 对话历史获取成功")
                print(f"  总对话数: {result['data']['conversation_count']}")
                print(f"  会话创建时间: {result['data']['created_at']}")
                
                # 显示最近3条对话
                conversations = result['data']['conversations']
                recent_count = min(3, len(conversations))
                print(f"  最近{recent_count}条对话:")
                for conv in conversations[-recent_count:]:
                    print(f"    Q: {conv['question']}")
                    print(f"    A: {conv['answer'][:100]}...")
                    print(f"    时间: {conv['timestamp']}")
                    print()
            else:
                print(f"✗ 错误: {result['msg']}")
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 获取对话历史失败: {e}")
    
    # 6. 测试清空对话历史
    print("\n6. 测试清空对话历史...")
    try:
        response = requests.delete(f"{BASE_URL}/meeting/chat/clear", params={"task_id": test_task_id})
        if response.status_code == 200:
            result = response.json()
            if result["code"] == 0:
                print(f"✓ {result['data']['message']}")
            else:
                print(f"✗ 错误: {result['msg']}")
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 清空对话历史失败: {e}")
    
    # 7. 确认对话历史已清空
    print("\n7. 确认对话历史已清空...")
    try:
        response = requests.get(f"{BASE_URL}/meeting/chat/history", params={"task_id": test_task_id})
        if response.status_code == 200:
            result = response.json()
            if result["code"] == 0:
                count = result['data']['conversation_count']
                print(f"✓ 当前对话数: {count} {'(已清空)' if count == 0 else '(未清空)'}")
            else:
                print(f"✗ 错误: {result['msg']}")
                
    except Exception as e:
        print(f"✗ 确认清空失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

def print_api_usage():
    """打印API使用说明"""
    print("\n" + "=" * 60)
    print("会议问答API使用说明")
    print("=" * 60)
    
    endpoints = [
        {
            "method": "POST",
            "path": "/meeting/ask",
            "description": "向会议内容提问",
            "body": {"task_id": "任务ID", "question": "用户问题"},
            "example": "curl -X POST http://localhost:8080/meeting/ask -H 'Content-Type: application/json' -d '{\"task_id\":\"test_123\",\"question\":\"会议的主要决策是什么？\"}'"
        },
        {
            "method": "GET", 
            "path": "/meeting/chat/history",
            "description": "获取对话历史",
            "params": {"task_id": "任务ID"},
            "example": "curl http://localhost:8080/meeting/chat/history?task_id=test_123"
        },
        {
            "method": "DELETE",
            "path": "/meeting/chat/clear", 
            "description": "清空对话历史",
            "params": {"task_id": "任务ID"},
            "example": "curl -X DELETE http://localhost:8080/meeting/chat/clear?task_id=test_123"
        },
        {
            "method": "GET",
            "path": "/meeting/chat/status",
            "description": "检查会话状态",
            "params": {"task_id": "任务ID"},
            "example": "curl http://localhost:8080/meeting/chat/status?task_id=test_123"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n{endpoint['method']} {endpoint['path']}")
        print(f"描述: {endpoint['description']}")
        if 'body' in endpoint:
            print(f"请求体: {endpoint['body']}")
        if 'params' in endpoint:
            print(f"参数: {endpoint['params']}")
        print(f"示例: {endpoint['example']}")
        print("-" * 40)

if __name__ == "__main__":
    print("请确保web服务已启动 (python -m uvicorn web_service:app --reload --port 8080)")
    
    choice = input("\n选择操作:\n1. 运行API测试\n2. 查看API使用说明\n请输入选项 (1/2): ").strip()
    
    if choice == "1":
        test_meeting_chat_api()
    elif choice == "2":
        print_api_usage()
    else:
        print("无效选项")