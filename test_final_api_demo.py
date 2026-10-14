#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示所有修改后的API接口使用方法
"""

import requests
import urllib.parse

def demo_api_usage():
    """演示API使用方法"""
    
    base_url = "http://127.0.0.1:8080"
    
    print("🎯 会议API接口使用演示")
    print("=" * 60)
    print("所有接口都已改为GET方法，使用URL参数！")
    print()
    
    # 使用实际的task_id进行演示
    real_task_id = "cfc3c818-16b7-4dbd-afa9-f1ca3cb91609"  # 从日志中看到的实际任务ID
    
    test_cases = [
        {
            "name": "1. 问答接口",
            "endpoint": "/meeting/ask",
            "params": {"task_id": real_task_id, "question": "会议有几个人参与发言？"},
            "description": "向会议内容提问"
        },
        {
            "name": "2. 获取对话历史",
            "endpoint": "/meeting/chat/history", 
            "params": {"task_id": real_task_id},
            "description": "获取之前的问答记录"
        },
        {
            "name": "3. 检查会话状态",
            "endpoint": "/meeting/chat/status",
            "params": {"task_id": real_task_id},
            "description": "检查会话是否可用"
        },
        {
            "name": "4. 清空对话历史",
            "endpoint": "/meeting/chat/clear",
            "params": {"task_id": real_task_id},
            "description": "清空所有问答记录"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}: {test_case['description']}")
        print(f"接口: GET {test_case['endpoint']}")
        
        # 构建完整URL
        params_str = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in test_case['params'].items()])
        full_url = f"{base_url}{test_case['endpoint']}?{params_str}"
        print(f"URL: {full_url}")
        
        try:
            response = requests.get(f"{base_url}{test_case['endpoint']}", params=test_case['params'])
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print("✅ 成功!")
                    if 'answer' in result.get('data', {}):
                        print(f"   回答: {result['data']['answer']}")
                    elif 'conversation_count' in result.get('data', {}):
                        print(f"   对话数量: {result['data']['conversation_count']}")
                    elif 'available' in result.get('data', {}):
                        print(f"   会话状态: {'可用' if result['data']['available'] else '不可用'}")
                else:
                    print(f"⚠️  返回信息: {result.get('msg', '未知错误')}")
            else:
                result = response.json()
                print(f"❌ 错误 ({response.status_code}): {result.get('msg', '未知错误')}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
        
        print("-" * 50)

def show_curl_examples():
    """显示curl命令示例"""
    
    print("\n\n📋 curl命令示例")
    print("=" * 60)
    
    task_id = "your-task-id"
    examples = [
        f'# 问答',
        f'curl "http://127.0.0.1:8080/meeting/ask?task_id={task_id}&question=会议讨论了什么主题"',
        '',
        f'# 获取对话历史',
        f'curl "http://127.0.0.1:8080/meeting/chat/history?task_id={task_id}"',
        '',
        f'# 检查会话状态',  
        f'curl "http://127.0.0.1:8080/meeting/chat/status?task_id={task_id}"',
        '',
        f'# 清空对话历史',
        f'curl "http://127.0.0.1:8080/meeting/chat/clear?task_id={task_id}"'
    ]
    
    for example in examples:
        print(example)

def show_browser_examples():
    """显示浏览器访问示例"""
    
    print("\n\n🌐 浏览器访问示例")
    print("=" * 60)
    print("可以直接在浏览器地址栏输入以下URL:")
    print()
    
    task_id = "your-task-id"
    urls = [
        f"http://127.0.0.1:8080/meeting/ask?task_id={task_id}&question=会议时长多少",
        f"http://127.0.0.1:8080/meeting/chat/history?task_id={task_id}",
        f"http://127.0.0.1:8080/meeting/chat/status?task_id={task_id}",
        f"http://127.0.0.1:8080/meeting/chat/clear?task_id={task_id}"
    ]
    
    for url in urls:
        print(f"  {url}")

def show_summary():
    """显示修改总结"""
    
    print("\n\n📝 修改总结")
    print("=" * 60)
    
    changes = [
        "✅ /meeting/ask - 改为GET方法，接受task_id和question参数",
        "✅ /meeting/chat/history - 已是GET方法，接受task_id参数",
        "✅ /meeting/chat/clear - 改为GET方法，接受task_id参数",
        "✅ /meeting/chat/status - 已是GET方法，接受task_id参数",
        "",
        "🎯 统一特点:",
        "  • 全部使用GET方法",
        "  • 全部使用URL参数（不需要JSON body）",
        "  • 统一的JSON响应格式 {code, msg, data}",
        "  • 完善的参数验证",
        "  • 支持中文URL编码"
    ]
    
    for change in changes:
        print(change)

if __name__ == "__main__":
    demo_api_usage()
    show_curl_examples()
    show_browser_examples()
    show_summary()