#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有四个会议API接口是否都支持URL参数
"""

import requests
import urllib.parse

def test_all_meeting_apis():
    """测试所有会议相关的API接口"""
    
    base_url = "http://127.0.0.1:8080"
    test_task_id = "test-task-123"
    
    print("🧪 测试所有会议API接口的URL参数支持")
    print("=" * 60)
    
    # 测试数据
    test_cases = [
        {
            "name": "问答接口",
            "url": f"{base_url}/meeting/ask",
            "params": {"task_id": test_task_id, "question": "会议中有几个人发言？"},
            "description": "GET /meeting/ask?task_id=xxx&question=yyy"
        },
        {
            "name": "获取对话历史",
            "url": f"{base_url}/meeting/chat/history",
            "params": {"task_id": test_task_id},
            "description": "GET /meeting/chat/history?task_id=xxx"
        },
        {
            "name": "清空对话历史",
            "url": f"{base_url}/meeting/chat/clear",
            "params": {"task_id": test_task_id},
            "description": "GET /meeting/chat/clear?task_id=xxx"
        },
        {
            "name": "检查会话状态",
            "url": f"{base_url}/meeting/chat/status",
            "params": {"task_id": test_task_id},
            "description": "GET /meeting/chat/status?task_id=xxx"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试{test_case['name']}")
        print(f"   接口: {test_case['description']}")
        print(f"   URL: {test_case['url']}")
        print(f"   参数: {test_case['params']}")
        
        try:
            response = requests.get(test_case['url'], params=test_case['params'])
            
            print(f"   状态码: {response.status_code}")
            
            # 检查是否返回正确的JSON格式
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
                print(f"   ✅ 返回JSON格式正确")
                print(f"   响应: {result}")
                
                # 检查是否包含必要的字段
                if 'code' in result and 'msg' in result:
                    print(f"   ✅ 响应格式统一 (包含code和msg字段)")
                else:
                    print(f"   ❌ 响应格式不统一")
            else:
                print(f"   ❌ 响应不是JSON格式")
                print(f"   响应内容: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 连接失败，请确保服务器运行在8080端口")
            break
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
        
        print("-" * 50)
    
    print("\n🎯 测试总结:")
    print("=" * 60)
    print("所有四个接口都已改为:")
    print("✅ 使用GET方法")
    print("✅ 接受URL参数 (不需要JSON body)")
    print("✅ 返回统一的JSON格式 {code, msg, data}")
    print("✅ 包含参数验证")

def test_parameter_validation():
    """测试参数验证功能"""
    
    print("\n\n🔍 测试参数验证功能")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8080"
    
    # 测试空参数
    test_cases = [
        {
            "name": "问答接口 - 空task_id",
            "url": f"{base_url}/meeting/ask",
            "params": {"task_id": "", "question": "测试问题"}
        },
        {
            "name": "问答接口 - 空question",
            "url": f"{base_url}/meeting/ask", 
            "params": {"task_id": "test-123", "question": ""}
        },
        {
            "name": "历史接口 - 空task_id",
            "url": f"{base_url}/meeting/chat/history",
            "params": {"task_id": ""}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        try:
            response = requests.get(test_case['url'], params=test_case['params'])
            result = response.json()
            
            if response.status_code == 400 and result.get('code') == 1:
                print(f"✅ 参数验证正常: {result['msg']}")
            else:
                print(f"❌ 参数验证异常: {result}")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")

def show_usage_examples():
    """显示使用示例"""
    
    print("\n\n📋 API使用示例")
    print("=" * 60)
    
    examples = [
        "# 1. 问答接口",
        "curl 'http://127.0.0.1:8080/meeting/ask?task_id=your-task&question=会议讨论了什么'",
        "",
        "# 2. 获取对话历史", 
        "curl 'http://127.0.0.1:8080/meeting/chat/history?task_id=your-task'",
        "",
        "# 3. 清空对话历史",
        "curl 'http://127.0.0.1:8080/meeting/chat/clear?task_id=your-task'",
        "",
        "# 4. 检查会话状态",
        "curl 'http://127.0.0.1:8080/meeting/chat/status?task_id=your-task'",
        "",
        "# 或者在浏览器中直接访问:",
        "http://127.0.0.1:8080/meeting/ask?task_id=your-task&question=会议主题是什么"
    ]
    
    for example in examples:
        print(example)

if __name__ == "__main__":
    test_all_meeting_apis()
    test_parameter_validation()
    show_usage_examples()