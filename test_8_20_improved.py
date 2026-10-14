#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试8.20.mp3文件的改进版声纹识别效果
"""

import requests
import json
import time
import os

def test_8_20_audio():
    """测试8.20音频文件"""
    base_url = "http://localhost:8080"
    audio_file = "test_file/8.20.mp3"
    
    print("🎯 测试8.20音频文件的改进版声纹识别")
    print(f"📁 测试文件: {audio_file}")
    
    # 检查文件
    if not os.path.exists(audio_file):
        print(f"❌ 测试文件不存在: {audio_file}")
        return
    
    file_size = os.path.getsize(audio_file)
    print(f"📊 文件大小: {file_size / (1024*1024):.2f} MB")
    
    # 1. 检查服务状态
    try:
        response = requests.get(f"{base_url}/")
        service_info = response.json()
        print(f"✅ 服务状态: {service_info.get('status')}")
        print(f"📋 版本: {service_info.get('version')}")
        print(f"🔬 改进版激活: {service_info.get('improved_speaker_id_active')}")
    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        return
    
    # 2. 上传音频文件
    print("\\n=== 上传8.20音频文件 ===")
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
    print(f"\\n=== 监控8.20音频处理进度 ===")
    print("🎯 目标: 识别出5个说话人（用户反馈：8.20这个音频里只有5个人讲话）")
    
    max_checks = 30  # 增加检查次数，因为文件较大
    check_interval = 20  # 每20秒检查一次
    
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
                    print("✅ 8.20音频处理完成!")
                    break
                elif status == 'error':
                    error = status_data.get('error', '未知错误')
                    print(f"❌ 任务失败: {error}")
                    return task_id
                else:
                    if i < max_checks - 1:
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
    
    # 4. 获取并分析结果
    print(f"\\n=== 获取8.20音频处理结果 ===")
    try:
        response = requests.get(f"{base_url}/task_result", params={"task_id": task_id})
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get('status') == 'done':
                result = result_data.get('result', {})
                
                print("🎯 改进版声纹识别结果分析:")
                speaker_count = result.get('speaker_count', 0)
                print(f"   🎤 识别说话人数: {speaker_count}")
                print(f"   📝 转录长度: {len(result.get('transcript', ''))}字符")
                print(f"   🧹 清理长度: {len(result.get('cleaned', ''))}字符")
                print(f"   📋 纪要长度: {len(result.get('minutes', ''))}字符")
                print(f"   💬 问答功能: {result.get('chat_available', False)}")
                
                # 分析说话人分布
                transcript = result.get('transcript', '')
                speaker_analysis = analyze_speaker_distribution(transcript)
                
                if speaker_analysis:
                    print(f"\\n📊 说话人分布详情:")
                    for speaker, stats in speaker_analysis.items():
                        print(f"   {speaker}: {stats['segments']}段发言, {stats['total_chars']}字符")
                
                # 评估改进效果
                print(f"\\n📈 改进效果评估:")
                if speaker_count == 5:
                    print(f"   🎉 完美！识别出{speaker_count}个说话人，与用户反馈完全匹配")
                elif speaker_count < 5:
                    print(f"   ✅ 良好！识别出{speaker_count}个说话人，相比原来的8个已大幅改进")
                    print(f"   💡 可能需要微调参数以达到精确的5人识别")
                elif speaker_count > 5:
                    print(f"   ⚠️ 仍需改进！识别出{speaker_count}个说话人，超过预期的5人")
                else:
                    print(f"   ❓ 异常情况：说话人数为{speaker_count}")
                
                # 保存结果
                output_file = "8_20_improved_result.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                print(f"\\n💾 结果已保存: {output_file}")
                
                return result, speaker_count
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
    lines = transcript.split('\\n')
    
    current_speaker = None
    for line in lines:
        line = line.strip()
        if line.startswith('【') and line.endswith('】'):
            # 说话人标识行
            current_speaker = line.strip('【】')
            if current_speaker not in speaker_stats:
                speaker_stats[current_speaker] = {'segments': 0, 'total_chars': 0}
        elif current_speaker and line:
            # 发言内容行
            speaker_stats[current_speaker]['segments'] += 1
            speaker_stats[current_speaker]['total_chars'] += len(line)
    
    return speaker_stats

if __name__ == "__main__":
    print("🚀 开始测试8.20音频文件的改进版声纹识别")
    
    # 测试8.20音频
    result = test_8_20_audio()
    
    if isinstance(result, tuple):
        data, speaker_count = result
        print(f"\\n🎯 最终结果总结:")
        print(f"   原始反馈: 8.20音频里只有5个人讲话")
        print(f"   改进识别: {speaker_count}个说话人")
        
        if speaker_count <= 5:
            print(f"   🎉 改进成功！大幅减少了过度分割问题")
        else:
            print(f"   ⚠️ 仍需进一步优化参数")
    
    print("\\n🎉 8.20音频测试完成!")