#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的GET参数API格式
"""

import requests
import urllib.parse

def test_new_format():
    """测试新的GET参数格式"""
    
    base_url = "http://127.0.0.1:8080"
    
    print("🧪 测试新的GET参数API格式")
    print("=" * 50)
    
    # 测试数据
    task_id = "be486adf-37af-4995-8222-0ad34016f1e8"
    question = "会议中有多少人发言？"
    
    # 方法1: 使用requests.get的params参数（推荐）
    print("方法1: 使用requests.get的params参数")
    try:
        response = requests.get(
            f"{base_url}/meeting/ask",
            params={"task_id": task_id, "question": question}
        )
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 返回格式正确，接受GET参数!")
        print(f"返回内容: {response.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "-" * 50)
    
    # 方法2: 手动构建URL
    print("方法2: 手动构建URL")
    encoded_question = urllib.parse.quote(question)
    manual_url = f"{base_url}/meeting/ask?task_id={task_id}&question={encoded_question}"
    
    print(f"完整URL: {manual_url}")
    
    try:
        response = requests.get(manual_url)
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 手动URL构建成功!")
        print(f"返回内容: {response.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "=" * 50)
    print("📝 使用说明:")
    print("1. 接口已成功改为GET方法")
    print("2. 现在可以使用URL参数: ?task_id=xxx&question=yyy")
    print("3. 不再需要发送JSON body数据")
    print("4. 中文问题会自动进行URL编码")

def show_usage_examples():
    """显示使用示例"""
    print("\n" + "=" * 50)
    print("📋 使用示例:")
    print("=" * 50)
    
    examples = [
        "curl 'http://127.0.0.1:8080/meeting/ask?task_id=your-task-id&question=会议中有几个人'",
        "curl 'http://127.0.0.1:8080/meeting/ask?task_id=your-task-id&question=主要讨论了什么'",
        "浏览器访问: http://127.0.0.1:8080/meeting/ask?task_id=your-task-id&question=会议时长"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")

if __name__ == "__main__":
    test_new_format()
    show_usage_examples()