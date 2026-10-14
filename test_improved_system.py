#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试改进的声纹识别系统
"""

import os
import time
from improved_speaker_id import ImprovedSpeakerIdentifier

def test_improved_speaker_system():
    """测试改进版声纹识别系统"""
    
    # 查找可用的测试音频
    audio_files = [
        "test_file/admin.MP3",
        "temp_20250830_021028_河北人设仲裁需求会-1.mp3", 
        "temp_20250830_172409_admin.mp3",
        "temp_20250830_030100_admin.mp3"
    ]
    
    test_file = None
    for file in audio_files:
        if os.path.exists(file):
            test_file = file
            break
    
    if not test_file:
        print("❌ 未找到测试音频文件")
        return
    
    print(f"🎵 测试文件: {test_file}")
    file_size = os.path.getsize(test_file) / (1024 * 1024)  # MB
    print(f"📊 文件大小: {file_size:.2f} MB")
    
    try:
        # 创建改进版识别器
        print("\n=== 初始化改进版声纹识别器 ===")
        identifier = ImprovedSpeakerIdentifier()
        
        # 执行识别
        print("\n=== 开始声纹识别 ===")
        start_time = time.time()
        
        result = identifier.identify_speakers(test_file, min_speakers=2, max_speakers=5)
        
        end_time = time.time()
        
        # 显示结果
        print("\n" + "="*50)
        print("🎯 声纹识别结果")
        print("="*50)
        
        if result.get('error'):
            print(f"❌ 识别失败: {result['error']}")
            return
        
        print(f"⏱️  处理时间: {end_time - start_time:.2f}秒")
        print(f"🎤 识别的说话人数: {result['total_speakers']}")
        print(f"🕒 音频总时长: {result['total_duration']:.2f}秒")
        print(f"🔧 识别方法: {result.get('method', 'Unknown')}")
        
        # 统计每个说话人
        segments = result.get('segments', [])
        if segments:
            speaker_stats = {}
            
            for seg in segments:
                speaker = seg['speaker']
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {
                        'count': 0, 
                        'total_time': 0, 
                        'confidences': []
                    }
                
                speaker_stats[speaker]['count'] += 1
                speaker_stats[speaker]['total_time'] += seg['duration']
                speaker_stats[speaker]['confidences'].append(seg['confidence'])
            
            print(f"\n📊 说话人统计:")
            for i, (speaker, stats) in enumerate(sorted(speaker_stats.items()), 1):
                avg_confidence = sum(stats['confidences']) / len(stats['confidences'])
                time_percent = (stats['total_time'] / result['total_duration']) * 100
                
                print(f"  {i}. {speaker}:")
                print(f"     - 发言段数: {stats['count']}")
                print(f"     - 发言时长: {stats['total_time']:.1f}秒 ({time_percent:.1f}%)")
                print(f"     - 平均置信度: {avg_confidence:.3f}")
        
        # 测试结果评估
        expected_speakers = 5  # 你说8.20音频只有5个人
        actual_speakers = result['total_speakers']
        
        print(f"\n🎯 识别准确性评估:")
        print(f"   期望说话人数: {expected_speakers}")
        print(f"   实际识别数: {actual_speakers}")
        
        if actual_speakers == expected_speakers:
            print("   ✅ 完美匹配!")
        elif abs(actual_speakers - expected_speakers) <= 1:
            print("   🟡 接近准确 (误差±1)")
        else:
            print("   🔴 需要进一步调优")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_with_core_system():
    """测试改进的核心系统"""
    print("\n" + "="*60)
    print("测试改进的核心系统")
    print("="*60)
    
    try:
        from core import MeetingProcessor
        
        processor = MeetingProcessor()
        
        # 使用admin.MP3进行测试
        test_file = "test_file/admin.MP3"
        if not os.path.exists(test_file):
            print("❌ 未找到admin.MP3测试文件")
            return
        
        print(f"🎵 测试文件: {test_file}")
        
        start_time = time.time()
        
        # 使用改进的声纹识别
        result = processor.process_with_speaker_id(test_file, output_dir="temp_output")
        
        end_time = time.time()
        
        print(f"\n✅ 处理完成! 总用时: {end_time - start_time:.2f}秒")
        print(f"🎤 识别的说话人数: {result['speaker_count']}")
        print(f"📝 转录长度: {len(result['transcript'])}字符")
        print(f"🧹 清理后长度: {len(result['cleaned'])}字符") 
        print(f"📋 会议纪要长度: {len(result['minutes'])}字符")
        print(f"📄 转录文件: {result.get('transcript_markdown_path', 'N/A')}")
        print(f"📋 纪要文件: {result.get('minutes_markdown_path', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 核心系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 开始测试改进的声纹识别系统")
    
    # 1. 测试改进版声纹识别
    speaker_result = test_improved_speaker_system()
    
    # 2. 测试核心系统集成
    if speaker_result:
        core_result = test_with_core_system()
    
    print("\n🎉 测试完成!")