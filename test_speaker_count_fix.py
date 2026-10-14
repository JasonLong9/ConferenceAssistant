#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试speaker_count修复效果
验证上传音频后speaker_count不再为0
"""

import sys
import os
import json
import time
import requests
from pathlib import Path

def test_speaker_count_fix():
    """测试speaker_count修复效果"""
    print("🔧 测试speaker_count修复效果")
    print("="*50)
    
    # 配置
    base_url = "http://localhost:8080"
    test_audio = "test_file/8.20.mp3"
    
    # 检查测试文件
    if not os.path.exists(test_audio):
        print(f"❌ 测试音频文件不存在: {test_audio}")
        return False
    
    print(f"📁 使用测试文件: {test_audio}")
    file_size = os.path.getsize(test_audio) / (1024*1024)
    print(f"📊 文件大小: {file_size:.2f} MB")
    
    try:
        # 1. 上传音频文件
        print("\n📤 步骤1: 上传音频文件")
        upload_url = f"{base_url}/upload_audio"
        
        with open(test_audio, 'rb') as f:
            files = {'file': (os.path.basename(test_audio), f, 'audio/mpeg')}
            upload_response = requests.post(upload_url, files=files, timeout=30)
        
        if upload_response.status_code != 200:
            print(f"❌ 上传失败: {upload_response.status_code}")
            print(f"响应内容: {upload_response.text}")
            return False
        
        upload_result = upload_response.json()
        task_id = upload_result.get('task_id')
        
        if not task_id:
            print(f"❌ 上传响应中没有task_id: {upload_result}")
            return False
        
        print(f"✅ 上传成功，task_id: {task_id}")
        
        # 2. 轮询处理进度
        print("\n⏳ 步骤2: 轮询处理进度")
        progress_url = f"{base_url}/task_progress"
        max_wait_time = 300  # 5分钟超时
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            progress_response = requests.get(progress_url, params={'task_id': task_id}, timeout=10)
            
            if progress_response.status_code != 200:
                print(f"⚠️ 进度查询失败: {progress_response.status_code}")
                time.sleep(5)
                continue
            
            progress_data = progress_response.json()
            status = progress_data.get('status', 'unknown')
            progress = progress_data.get('progress', 0)
            
            print(f"📈 状态: {status}, 进度: {progress}%")
            
            if status == 'completed':
                print("✅ 处理完成！")
                break
            elif status == 'failed':
                print(f"❌ 处理失败: {progress_data.get('error', 'Unknown error')}")
                return False
            
            time.sleep(3)
        else:
            print("⏰ 处理超时")
            return False
        
        # 3. 获取处理结果
        print("\n📋 步骤3: 获取处理结果")
        result_url = f"{base_url}/task_result"
        result_response = requests.get(result_url, params={'task_id': task_id}, timeout=10)
        
        if result_response.status_code != 200:
            print(f"❌ 结果获取失败: {result_response.status_code}")
            print(f"响应内容: {result_response.text}")
            return False
        
        result_data = result_response.json()
        
        # 4. 验证speaker_count
        print("\n🔍 步骤4: 验证speaker_count")
        
        if 'result' not in result_data:
            print(f"❌ 响应中没有result字段: {result_data}")
            return False
        
        result = result_data['result']
        speaker_count = result.get('speaker_count', None)
        
        print(f"🎯 检测结果:")
        print(f"   speaker_count: {speaker_count}")
        print(f"   转写长度: {len(result.get('transcript', ''))}")
        print(f"   清理长度: {len(result.get('cleaned', ''))}")
        print(f"   纪要长度: {len(result.get('minutes', ''))}")
        
        # 验证修复效果
        success = True
        issues = []
        
        if speaker_count is None:
            issues.append("speaker_count字段缺失")
            success = False
        elif speaker_count == 0:
            issues.append("speaker_count仍为0")
            success = False
        elif not isinstance(speaker_count, int):
            issues.append(f"speaker_count类型错误: {type(speaker_count)}")
            success = False
        elif speaker_count < 1:
            issues.append(f"speaker_count值异常: {speaker_count}")
            success = False
        
        if success:
            print(f"\n🎉 修复成功！")
            print(f"   ✅ speaker_count = {speaker_count} (>0)")
            print(f"   ✅ 类型正确: {type(speaker_count).__name__}")
            
            # 额外检查合理性
            if 1 <= speaker_count <= 10:
                print(f"   ✅ 数值合理 (1-10范围内)")
            else:
                print(f"   ⚠️ 数值可能偏高: {speaker_count}")
            
            return True
        else:
            print(f"\n❌ 修复失败:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_scenarios():
    """测试多种场景"""
    print("\n🧪 测试多种场景")
    print("="*50)
    
    scenarios = [
        "test_file/8.20.mp3",
        "test_file/8.28.mp3",
    ]
    
    results = {}
    
    for audio_file in scenarios:
        if os.path.exists(audio_file):
            print(f"\n🎵 测试文件: {audio_file}")
            result = test_single_file(audio_file)
            results[audio_file] = result
        else:
            print(f"⏭️ 跳过不存在的文件: {audio_file}")
    
    # 汇总结果
    print(f"\n📊 测试汇总:")
    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    for file, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {os.path.basename(file)}: {status}")
    
    print(f"\n📈 成功率: {success_count}/{total_count} ({success_count/max(total_count,1)*100:.1f}%)")
    
    return success_count == total_count

def test_single_file(audio_file):
    """测试单个文件"""
    try:
        # 这里可以直接使用core.py进行本地测试
        from core import MeetingProcessor
        
        print(f"  🔄 本地处理: {os.path.basename(audio_file)}")
        
        processor = MeetingProcessor()
        result = processor.process_with_speaker_id(audio_file)
        
        speaker_count = result.get('speaker_count', 0)
        print(f"  🎯 speaker_count: {speaker_count}")
        
        if speaker_count > 0:
            print(f"  ✅ 本地测试通过")
            return True
        else:
            print(f"  ❌ 本地测试失败")
            return False
            
    except Exception as e:
        print(f"  ❌ 本地测试异常: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始speaker_count修复验证")
    print("时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # 主要测试
    main_success = test_speaker_count_fix()
    
    # 多场景测试
    multi_success = test_multiple_scenarios()
    
    print(f"\n🏁 最终结果:")
    print(f"   主要测试: {'✅ 通过' if main_success else '❌ 失败'}")
    print(f"   多场景测试: {'✅ 通过' if multi_success else '❌ 失败'}")
    
    if main_success and multi_success:
        print(f"\n🎉 所有测试通过！speaker_count修复成功！")
        sys.exit(0)
    else:
        print(f"\n😞 测试失败，需要进一步调试")
        sys.exit(1)