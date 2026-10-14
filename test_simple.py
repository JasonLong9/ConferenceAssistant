#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的测试脚本 - 先测试不需要网络连接的部分
"""

import os
import sys
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import MeetingProcessor

def test_basic_processing():
    """测试基础的会议处理功能（不使用声纹识别）"""
    print("="*60)
    print("测试1: 基础会议处理功能（无声纹识别）")
    print("="*60)
    
    test_audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    
    if not os.path.exists(test_audio_path):
        print(f"错误：测试音频文件不存在: {test_audio_path}")
        return False
    
    try:
        print("初始化会议处理器...")
        processor = MeetingProcessor()
        
        print("开始处理（不使用声纹识别）...")
        start_time = time.time()
        
        result = processor.process_with_speaker_id(
            audio_path=test_audio_path,
            meeting_name="基础测试会议",
            output_dir="test_output",
            enable_speaker_id=False  # 关闭声纹识别
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print("\n" + "="*40)
        print("处理完成！结果摘要:")
        print("="*40)
        print(f"处理时间: {processing_time:.2f}秒")
        print(f"识别发言人数: {result['speaker_count']}")
        print(f"会议名称: {result['meeting_name']}")
        print(f"转写内容文件: {result.get('transcript_markdown_path', '未生成')}")
        print(f"会议纪要文件: {result.get('minutes_markdown_path', '未生成')}")
        
        print(f"\n转写内容预览（前300字符）:")
        print("-" * 50)
        print(result['transcript'][:300] + "..." if len(result['transcript']) > 300 else result['transcript'])
        
        return True
        
    except Exception as e:
        print(f"基础测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_whisper_only():
    """只测试Whisper转写功能"""
    print("\n" + "="*60)
    print("测试2: 纯Whisper转写功能")
    print("="*60)
    
    test_audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    
    if not os.path.exists(test_audio_path):
        print(f"错误：测试音频文件不存在: {test_audio_path}")
        return False
    
    try:
        from core import LocalWhisper
        
        print("初始化Whisper模型...")
        whisper = LocalWhisper()
        
        print("开始转写...")
        start_time = time.time()
        
        # 测试普通转写
        transcript = whisper.transcribe(test_audio_path)
        
        # 测试带时间戳的转写
        segments = whisper.transcribe_with_timestamps(test_audio_path)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n转写完成！时间: {processing_time:.2f}秒")
        print(f"识别到 {len(segments)} 个音频片段")
        
        print(f"\n转写结果预览（前300字符）:")
        print("-" * 50)
        print(transcript[:300] + "..." if len(transcript) > 300 else transcript)
        
        print(f"\n时间戳片段预览（前3个）:")
        print("-" * 50)
        for i, seg in enumerate(segments[:3]):
            print(f"片段{i+1}: {seg['start']:.2f}s - {seg['end']:.2f}s: {seg['text'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"Whisper测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("声纹识别集成测试（简化版）")
    print("=" * 60)
    
    # 创建测试输出目录
    os.makedirs("test_output", exist_ok=True)
    
    test_results = []
    
    # 测试1: Whisper转写
    try:
        result1 = test_whisper_only()
        test_results.append(("Whisper转写", result1))
    except Exception as e:
        print(f"测试1异常: {e}")
        test_results.append(("Whisper转写", False))
    
    # 测试2: 基础处理
    try:
        result2 = test_basic_processing()
        test_results.append(("基础处理", result2))
    except Exception as e:
        print(f"测试2异常: {e}")
        test_results.append(("基础处理", False))
    
    # 总结测试结果
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 通过")
    
    if passed == total:
        print("基础功能测试通过！")
        print("\n接下来可以尝试:")
        print("1. 解决网络问题后测试声纹识别功能")
        print("2. 使用 python main.py [音频文件] 进行完整测试")
        print("3. 使用 python main.py [音频文件] --enable_speaker_id 测试声纹识别")
    else:
        print("警告: 部分测试失败，请检查错误信息")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未预期错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)