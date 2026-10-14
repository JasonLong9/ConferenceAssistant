#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import os

def test_improved_api():
    """测试改进版API"""
    base_url = "http://localhost:8082"
    audio_file = "test_file/admin.MP3"
    
    print("🔍 测试改进版ConferenceAssistant API (端口8082)")
    print("🎯 重点: 声纹识别准确性改进")
    
    # 检查文件
    if not os.path.exists(audio_file):
        print(f"❌ 测试文件不存在: {audio_file}")
        return
    
    file_size = os.path.getsize(audio_file)
    print(f"📁 测试文件: {audio_file}")
    print(f"📊 文件大小: {file_size / 1024:.2f} KB")
    
    # 1. 测试基础接口
    print("\n=== 测试基础接口 ===")
    try:
        response = requests.get(f"{base_url}/")
        print(f"根路径: {response.status_code} - {response.json()['status']}")
    except Exception as e:
        print(f"基础接口错误: {e}")
        return
    
    # 2. 上传音频文件
    print("\n=== 音频上传与处理 ===")
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
    
    # 3. 监控处理进度
    print(f"\n=== 监控处理进度 ===")
    print("💡 改进重点: 更准确的说话人数量识别")
    
    max_checks = 20  # 减少检查次数
    check_interval = 15  # 每15秒检查一次
    
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
                    break
                elif status == 'error':
                    error = status_data.get('error', '未知错误')
                    print(f"❌ 任务失败: {error}")
                    return
                else:
                    print(f"   等待{check_interval}秒...")
                    time.sleep(check_interval)
            else:
                print(f"❌ 状态查询失败: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ 状态查询异常: {e}")
            break
    else:
        print("⏰ 监控超时，但任务可能仍在进行中")
        print("💡 请稍后手动检查任务结果")
        return task_id
    
    # 4. 获取处理结果
    print(f"\n=== 获取处理结果 ===")
    try:
        response = requests.get(f"{base_url}/task_result", params={"task_id": task_id})
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get('status') == 'done':
                result = result_data.get('result', {})
                
                print("🎯 改进版声纹识别结果:")
                print(f"   📝 转录长度: {len(result.get('transcript', ''))}字符")
                print(f"   🧹 清理长度: {len(result.get('cleaned', ''))}字符")
                print(f"   📋 纪要长度: {len(result.get('minutes', ''))}字符")
                print(f"   🎤 说话人数: {result.get('speaker_count', 0)}")
                print(f"   💬 问答可用: {result.get('chat_available', False)}")
                
                # 显示说话人分布（从转录文本中分析）
                transcript = result.get('transcript', '')
                speaker_analysis = analyze_speaker_distribution(transcript)
                
                if speaker_analysis:
                    print(f"\n📊 说话人分布分析:")
                    for speaker, stats in speaker_analysis.items():
                        print(f"   {speaker}: {stats['count']}段发言, 约{stats['char_count']}字符")
                
                # 保存结果供对比
                with open("improved_result.json", "w", encoding="utf-8") as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                print(f"\n💾 结果已保存: improved_result.json")
                
                return result
            else:
                print(f"❌ 任务未完成: {result_data.get('status')}")
        else:
            print(f"❌ 结果获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 结果获取异常: {e}")
    
    return task_id

def analyze_speaker_distribution(transcript):
    """分析转录文本中的说话人分布"""
    if not transcript:
        return None
    
    speaker_stats = {}
    lines = transcript.split('\n')
    
    current_speaker = None
    for line in lines:
        line = line.strip()
        if line.startswith('【') and line.endswith('】'):
            # 说话人标识行
            current_speaker = line.strip('【】')
            if current_speaker not in speaker_stats:
                speaker_stats[current_speaker] = {'count': 0, 'char_count': 0}
        elif current_speaker and line:
            # 发言内容行
            speaker_stats[current_speaker]['count'] += 1
            speaker_stats[current_speaker]['char_count'] += len(line)
    
    return speaker_stats

def compare_with_original():
    """与原始结果对比"""
    print("\n=== 对比分析 ===")
    
    # 检查是否有原始结果
    if os.path.exists("api_test_report.json"):
        try:
            with open("api_test_report.json", "r", encoding="utf-8") as f:
                original_data = json.load(f)
            
            print("📊 与原始API结果对比:")
            print(f"   原始测试成功率: {original_data.get('summary', {}).get('success_rate', 0)}%")
            print(f"   原始测试总数: {original_data.get('summary', {}).get('total_tests', 0)}")
            
        except Exception as e:
            print(f"无法读取原始结果: {e}")
    
    if os.path.exists("improved_result.json"):
        print("✅ 改进版结果已保存，可用于详细对比")
    
    print("\n🎯 改进重点验证:")
    print("   1. 说话人数量是否更准确 (目标: 接近实际5人)")
    print("   2. 是否减少了过度分割")
    print("   3. 整体处理是否更稳定")

if __name__ == "__main__":
    print("🚀 开始测试改进版ConferenceAssistant API")
    
    # 测试改进版
    result = test_improved_api()
    
    # 对比分析
    compare_with_original()
    
    print(f"\n🎉 测试完成!")
    if result:
        print("💡 请检查说话人数量是否接近预期的5人")
        print("💡 建议对比改进前后的结果文件")