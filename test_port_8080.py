#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import os

def test_8080_with_improvements():
    """测试8080端口的服务是否使用了改进版声纹识别"""
    base_url = "http://localhost:8080"
    audio_file = "test_file/admin.MP3"
    
    print("🔍 测试8080端口服务的改进效果")
    print(f"📁 测试文件: {audio_file}")
    
    if not os.path.exists(audio_file):
        print(f"❌ 测试文件不存在: {audio_file}")
        return
    
    # 1. 检查服务状态
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ 服务响应: {response.status_code}")
        print(f"📊 服务信息: {response.json()}")
    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        return
    
    # 2. 上传音频文件
    print("\n=== 上传音频文件 ===")
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': (os.path.basename(audio_file), f, 'audio/mpeg')}
            response = requests.post(f"{base_url}/audio2summary_async", files=files, timeout=10)
            
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"✅ 上传成功，任务ID: {task_id}")
        else:
            print(f"❌ 上传失败: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return
    
    # 3. 简单监控 - 只检查几次
    print(f"\n=== 快速检查任务状态 ===")
    for i in range(5):
        try:
            response = requests.get(f"{base_url}/task_status", params={"task_id": task_id})
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                progress = status_data.get('progress', 0)
                stage = status_data.get('stage', '')
                
                print(f"检查 {i+1}: {status} - {progress}% - {stage}")
                
                if status == 'done':
                    print("✅ 任务快速完成!")
                    break
                elif status == 'error':
                    error = status_data.get('error', '未知错误')
                    print(f"❌ 任务失败: {error}")
                    return task_id
                else:
                    time.sleep(10)  # 10秒间隔
            else:
                print(f"❌ 状态查询失败: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ 状态查询异常: {e}")
            break
    
    print(f"\n💡 任务ID: {task_id}")
    print("📋 如果任务仍在处理中，可以稍后手动检查结果")
    
    return task_id

def check_task_result(task_id):
    """检查任务结果"""
    base_url = "http://localhost:8080"
    
    print(f"\n=== 检查任务结果 ===")
    print(f"🆔 任务ID: {task_id}")
    
    try:
        response = requests.get(f"{base_url}/task_result", params={"task_id": task_id})
        if response.status_code == 200:
            result_data = response.json()
            
            if result_data.get('status') == 'done':
                result = result_data.get('result', {})
                
                print("🎯 处理结果:")
                print(f"   📝 转录长度: {len(result.get('transcript', ''))} 字符")
                print(f"   🧹 清理长度: {len(result.get('cleaned', ''))} 字符")
                print(f"   📋 纪要长度: {len(result.get('minutes', ''))} 字符")
                print(f"   🎤 识别的说话人数: {result.get('speaker_count', 0)}")
                print(f"   💬 问答功能可用: {result.get('chat_available', False)}")
                
                # 分析是否使用了改进版
                speaker_count = result.get('speaker_count', 0)
                print(f"\n📊 改进效果分析:")
                
                if speaker_count <= 5:
                    print(f"   ✅ 说话人数控制良好 ({speaker_count}个)")
                    print(f"   ✅ 可能使用了改进版声纹识别")
                elif speaker_count > 6:
                    print(f"   ⚠️ 说话人数较多 ({speaker_count}个)")
                    print(f"   ⚠️ 可能仍在使用旧版声纹识别")
                
                # 保存结果
                with open("port_8080_result.json", "w", encoding="utf-8") as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                print(f"   💾 结果已保存: port_8080_result.json")
                
                return result
                
            elif result_data.get('status') == 'processing':
                progress = result_data.get('progress', 0)
                print(f"⏳ 任务仍在处理中: {progress}%")
                
            else:
                print(f"❌ 任务状态: {result_data.get('status')}")
                if result_data.get('error'):
                    print(f"   错误: {result_data.get('error')}")
        else:
            print(f"❌ 结果获取失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 结果获取异常: {e}")
    
    return None

if __name__ == "__main__":
    print("🚀 测试8080端口服务的改进效果")
    
    # 运行测试
    task_id = test_8080_with_improvements()
    
    if task_id:
        print("\n⏱️ 等待30秒后检查结果...")
        time.sleep(30)
        
        # 检查结果
        result = check_task_result(task_id)
        
        if not result:
            print("\n💡 提示:")
            print("   - 如果任务仍在处理中，请稍后再次运行检查")
            print(f"   - 任务ID: {task_id}")
            print("   - 大型音频文件可能需要5-10分钟处理时间")
    
    print("\n🎉 测试完成!")