#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的完整API测试脚本
测试从音频上传到问答的完整流程
"""

import requests
import time
import json
import os

def test_full_workflow():
    """测试完整的工作流程"""
    base_url = "http://localhost:8080"
    
    print("=== ConferenceAssistant 完整功能测试 ===")
    
    # 1. 检查服务状态
    print("1. 检查服务状态...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   服务正常运行")
        else:
            print(f"   服务状态异常: {response.status_code}")
            return
    except Exception as e:
        print(f"   无法连接到服务: {e}")
        return
    
    # 2. 检查是否有测试音频文件
    test_audio = "test_file/河北人设仲裁需求会-1.mp3"
    if not os.path.exists(test_audio):
        print(f"   警告: 测试音频文件不存在: {test_audio}")
        print("   将跳过音频上传测试")
        test_with_fake_id()
        return
    
    # 3. 上传音频文件
    print("2. 上传音频文件...")
    try:
        with open(test_audio, 'rb') as f:
            files = {'file': (os.path.basename(test_audio), f, 'audio/mpeg')}
            response = requests.post(f"{base_url}/audio2summary_async", files=files)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   音频上传成功，任务ID: {task_id}")
        else:
            print(f"   音频上传失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return
    except Exception as e:
        print(f"   上传异常: {e}")
        return
    
    # 4. 监控任务状态
    print("3. 监控任务处理状态...")
    max_wait_time = 600  # 最多等待10分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{base_url}/task_status", params={'task_id': task_id})
            
            if response.status_code == 200:
                status_result = response.json()
                status = status_result.get('status')
                progress = status_result.get('progress', 0)
                
                print(f"   状态: {status}, 进度: {progress}%")
                
                if status == 'done':
                    print("   任务处理完成!")
                    break
                elif status == 'error':
                    print("   任务处理失败")
                    return
                
            else:
                print(f"   状态查询失败: {response.status_code}")
                
        except Exception as e:
            print(f"   状态查询异常: {e}")
        
        time.sleep(10)  # 每10秒检查一次
    else:
        print("   任务处理超时")
        return
    
    # 5. 获取处理结果
    print("4. 获取处理结果...")
    try:
        response = requests.get(f"{base_url}/task_result", params={'task_id': task_id})
        
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get('status') == 'done':
                meeting_result = result_data.get('result', {})
                print(f"   会议名称: {meeting_result.get('meeting_name', 'unknown')}")
                print(f"   发言人数: {meeting_result.get('speaker_count', 'unknown')}")
                print(f"   转写长度: {len(meeting_result.get('transcript', ''))} 字符")
                print(f"   纪要长度: {len(meeting_result.get('minutes', ''))} 字符")
                print(f"   问答可用: {meeting_result.get('chat_available', False)}")
                
                if not meeting_result.get('chat_available'):
                    print("   问答功能不可用，测试结束")
                    return
            else:
                print(f"   任务未完成: {result_data.get('status')}")
                return
        else:
            print(f"   获取结果失败: {response.status_code}")
            return
            
    except Exception as e:
        print(f"   获取结果异常: {e}")
        return
    
    # 6. 测试问答功能
    print("5. 测试问答功能...")
    test_questions = [
        "这次会议有几个发言人？",
        "会议的主要内容是什么？",
        "请总结一下会议的关键决策"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"   问题{i}: {question}")
        try:
            response = requests.post(
                f"{base_url}/meeting/ask",
                json={'task_id': task_id, 'question': question}
            )
            
            if response.status_code == 200:
                answer_result = response.json()
                if answer_result.get('code') == 0:
                    answer = answer_result.get('data', {}).get('answer', '')
                    conv_count = answer_result.get('data', {}).get('conversation_count', 0)
                    print(f"   回答: {answer[:100]}{'...' if len(answer) > 100 else ''}")
                    print(f"   对话数: {conv_count}")
                else:
                    print(f"   问答失败: {answer_result.get('msg')}")
            else:
                print(f"   问答请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"   问答异常: {e}")
        
        time.sleep(2)  # 避免请求过快
    
    # 7. 测试对话历史
    print("6. 测试对话历史...")
    try:
        response = requests.get(f"{base_url}/meeting/chat/history", params={'task_id': task_id})
        
        if response.status_code == 200:
            history_result = response.json()
            if history_result.get('code') == 0:
                data = history_result.get('data', {})
                conv_count = data.get('conversation_count', 0)
                conversations = data.get('conversations', [])
                print(f"   总对话数: {conv_count}")
                print(f"   历史记录: {len(conversations)} 条")
            else:
                print(f"   获取历史失败: {history_result.get('msg')}")
        else:
            print(f"   历史请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"   历史查询异常: {e}")
    
    print("\n=== 完整功能测试完成 ===")

def test_with_fake_id():
    """使用虚假ID测试接口可访问性"""
    base_url = "http://localhost:8080"
    fake_id = "fake-task-id-12345"
    
    print("使用虚假ID测试接口...")
    
    # 测试各个接口
    endpoints = [
        ('GET', '/task_status', {'task_id': fake_id}),
        ('GET', '/task_result', {'task_id': fake_id}),
        ('POST', '/meeting/ask', {'task_id': fake_id, 'question': '测试问题'}),
        ('GET', '/meeting/chat/history', {'task_id': fake_id}),
        ('GET', '/meeting/chat/status', {'task_id': fake_id}),
        ('DELETE', '/meeting/chat/clear', {'task_id': fake_id}),
    ]
    
    for method, endpoint, data in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f"{base_url}{endpoint}", params=data)
            elif method == 'POST':
                response = requests.post(f"{base_url}{endpoint}", json=data)
            elif method == 'DELETE':
                response = requests.delete(f"{base_url}{endpoint}", params=data)
            
            print(f"   {method} {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"   {method} {endpoint}: 异常 - {e}")

if __name__ == "__main__":
    test_full_workflow()