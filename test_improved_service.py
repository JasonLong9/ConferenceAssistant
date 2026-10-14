#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import os

def test_improved_service():
    """测试改进版服务"""
    base_url = "http://localhost:8081"
    audio_file = "test_file/admin.MP3"
    
    print("🔍 测试改进版ConferenceAssistant API服务 (端口8081)")
    
    # 1. 测试基础接口
    print("\n=== 测试基础接口 ===")
    try:
        response = requests.get(f"{base_url}/")
        print(f"根路径: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"服务状态: {data.get('status')}")
    except Exception as e:
        print(f"基础接口错误: {e}")
        return
    
    # 2. 测试音频上传
    print("\n=== 测试音频上传 ===")
    if not os.path.exists(audio_file):
        print(f"测试文件不存在: {audio_file}")
        return
    
    file_size = os.path.getsize(audio_file)
    print(f"文件大小: {file_size / 1024:.2f} KB")
    
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': (os.path.basename(audio_file), f, 'audio/mpeg')}
            response = requests.post(f"{base_url}/audio2summary_async", files=files, timeout=10)
            
        print(f"上传响应: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"任务ID: {task_id}")
            
            # 3. 监控任务进度（短时间）
            print("\n=== 监控任务进度 ===")
            max_checks = 10
            for i in range(max_checks):
                try:
                    response = requests.get(f"{base_url}/task_status", params={"task_id": task_id})
                    if response.status_code == 200:
                        status_data = response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        stage = status_data.get('stage', '')
                        
                        print(f"检查 {i+1}: {status} - {progress}% - {stage}")
                        
                        if status == 'done':
                            print("✅ 任务完成!")
                            
                            # 获取结果
                            response = requests.get(f"{base_url}/task_result", params={"task_id": task_id})
                            if response.status_code == 200:
                                result_data = response.json()
                                result = result_data.get('result', {})
                                print(f"转录长度: {len(result.get('transcript', ''))}字符")
                                print(f"清理长度: {len(result.get('cleaned', ''))}字符")
                                print(f"纪要长度: {len(result.get('minutes', ''))}字符")
                                print(f"说话人数: {result.get('speaker_count', 0)}")
                                print(f"问答可用: {result.get('chat_available', False)}")
                            break
                        elif status == 'error':
                            error = status_data.get('error', '未知错误')
                            print(f"❌ 任务失败: {error}")
                            break
                        else:
                            time.sleep(3)
                    else:
                        print(f"状态查询失败: {response.status_code}")
                        break
                        
                except Exception as e:
                    print(f"状态查询异常: {e}")
                    break
            else:
                print("⏰ 监控超时，任务可能仍在进行中")
                
        else:
            print(f"上传失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"上传异常: {e}")

if __name__ == "__main__":
    test_improved_service()