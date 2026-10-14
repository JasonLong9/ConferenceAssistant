#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的性能测试脚本
测试优化后的音频处理性能
"""

import time
import os
from core import MeetingProcessor

def create_test_audio():
    """创建测试音频文件"""
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
        
        # 创建1分钟的测试音频
        print("创建测试音频...")
        duration = 60 * 1000  # 1分钟
        test_tone = Sine(440).to_audio_segment(duration=duration)
        
        test_file = "test_audio.wav"
        test_tone.export(test_file, format="wav")
        print(f"测试音频已创建: {test_file}")
        return test_file
        
    except Exception as e:
        print(f"创建测试音频失败: {e}")
        return None

def test_processing_speed():
    """测试处理速度"""
    print("=== ConferenceAssistant 性能测试 ===")
    
    # 创建测试音频
    test_file = create_test_audio()
    if not test_file:
        print("无法创建测试音频，测试结束")
        return
    
    try:
        # 初始化处理器
        print("\\n初始化处理器...")
        processor = MeetingProcessor()
        
        # 开始性能测试
        print("\\n开始处理测试...")
        start_time = time.time()
        
        # 使用简化的处理（不使用发言人识别以加快测试）
        result = processor.process(test_file)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 输出结果
        print(f"\\n=== 测试结果 ===")
        print(f"音频时长: 1分钟")
        print(f"处理时间: {processing_time:.1f}秒")
        print(f"处理速度: {60/processing_time:.1f}x 实时速度")
        print(f"转写长度: {len(result.get('transcript', ''))} 字符")
        print(f"会议主题: {result.get('meeting_name', 'N/A')}")
        
        # 性能评估
        if processing_time < 30:
            print("\\n✅ 优秀！处理速度很快")
        elif processing_time < 60:
            print("\\n✅ 良好！处理速度还行") 
        else:
            print("\\n⚠️  处理速度较慢，可能需要进一步优化")
            
    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理测试文件
        try:
            if os.path.exists(test_file):
                os.remove(test_file)
                print(f"\\n🗑️ 已清理测试文件: {test_file}")
        except:
            pass

if __name__ == "__main__":
    test_processing_speed()