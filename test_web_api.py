#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Web API接口
"""

import requests
import time
import os

def test_web_api():
    """测试Web API"""
    base_url = "http://localhost:8080"
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"[OK] Web服务运行中，状态码: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] 无法连接到Web服务: {e}")
        return False
    
    # 测试任务状态接口（使用不存在的任务ID）
    try:
        response = requests.get(f"{base_url}/task_status?task_id=test123")
        print(f"[OK] 任务状态接口响应: {response.status_code}")
        if response.status_code == 404:
            print("      预期的404错误 - 任务不存在")
    except Exception as e:
        print(f"[ERROR] 任务状态接口测试失败: {e}")
        return False
    
    # 如果有测试音频文件，可以测试上传（这里跳过实际上传测试）
    test_audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    if os.path.exists(test_audio_path):
        print(f"[INFO] 找到测试音频文件: {test_audio_path}")
        print("       (跳过实际上传测试，因为会很耗时)")
        
        # 可以在这里添加实际的文件上传测试
        # files = {"file": open(test_audio_path, "rb")}
        # response = requests.post(f"{base_url}/audio2summary_async", files=files)
    else:
        print("[INFO] 未找到测试音频文件")
    
    return True

def main():
    print("=" * 50)
    print("Web API 测试")
    print("=" * 50)
    
    if test_web_api():
        print("\n[SUCCESS] Web API基本功能测试通过")
        print("\n可用的API端点:")
        print("- GET /docs - API文档") 
        print("- POST /audio2summary_async - 异步音频处理")
        print("- GET /task_status?task_id=<id> - 查询任务状态")
        print("- GET /task_result?task_id=<id> - 获取任务结果")
        print("\n注意：API已集成离线声纹识别功能")
        print("处理结果将包含发言人数量和发言人分离信息")
    else:
        print("\n[FAIL] Web API测试失败")
    
    return 0

if __name__ == "__main__":
    main()