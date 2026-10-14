#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速测试路径修复是否有效
"""

import os

def test_audio_path():
    """测试音频文件路径处理"""
    print("=" * 50)
    print("测试音频文件路径处理")
    print("=" * 50)
    
    audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    abs_audio_path = os.path.abspath(audio_path)
    
    print(f"原始路径: {audio_path}")
    print(f"绝对路径: {abs_audio_path}")
    print(f"文件存在: {os.path.exists(abs_audio_path)}")
    
    if os.path.exists(abs_audio_path):
        file_size = os.path.getsize(abs_audio_path) / (1024 * 1024)
        print(f"文件大小: {file_size:.2f} MB")
        return True
    else:
        print("[ERROR] 音频文件不存在!")
        return False

def test_speaker_id_with_abs_path():
    """使用绝对路径测试声纹识别"""
    print("\n" + "=" * 50)
    print("使用绝对路径测试声纹识别")
    print("=" * 50)
    
    try:
        from speaker_identification import SpeakerIdentifier
        
        # 使用绝对路径
        audio_path = "test_file/河北人设仲裁需求会-1.mp3"
        abs_audio_path = os.path.abspath(audio_path)
        
        print(f"使用路径: {abs_audio_path}")
        
        identifier = SpeakerIdentifier()
        print(f"声纹识别器可用: {identifier.available}")
        
        if not identifier.available:
            print("[ERROR] 声纹识别器不可用")
            return False
        
        # 执行声纹识别
        print("执行声纹识别...")
        result = identifier.identify_speakers(abs_audio_path, min_speakers=2, max_speakers=6)
        
        print(f"识别结果:")
        print(f"  total_speakers: {result.get('total_speakers', 'None')}")
        print(f"  error: {result.get('error', 'None')}")
        
        if result.get('error'):
            print(f"[ERROR] 声纹识别失败: {result['error']}")
            return False
        elif result.get('total_speakers', 0) > 0:
            print(f"[SUCCESS] 成功识别 {result['total_speakers']} 个发言人")
            return True
        else:
            print("[WARNING] 未识别到发言人")
            return False
            
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        return False

def test_core_with_debug():
    """测试修复后的Core模块"""
    print("\n" + "=" * 50)  
    print("测试修复后的Core模块")
    print("=" * 50)
    
    try:
        from core import MeetingProcessor
        
        processor = MeetingProcessor()
        
        # 创建一个小的测试音频文件路径 (模拟)
        audio_path = "test_file/河北人设仲裁需求会-1.mp3"
        
        print(f"测试音频路径: {audio_path}")
        print(f"绝对路径: {os.path.abspath(audio_path)}")
        
        # 只测试声纹识别器初始化和路径处理
        if processor.speaker_identifier is None:
            from speaker_identification import SpeakerIdentifier
            processor.speaker_identifier = SpeakerIdentifier()
        
        print(f"声纹识别器状态: {processor.speaker_identifier.available}")
        
        if processor.speaker_identifier.available:
            print("[INFO] Core模块准备就绪，声纹识别器可用")
            print("[INFO] 路径修复应该已生效")
            return True
        else:
            print("[ERROR] 声纹识别器不可用")  
            return False
            
    except Exception as e:
        print(f"[ERROR] Core测试失败: {e}")
        return False

def main():
    print("快速测试路径修复效果\n")
    
    # 测试1: 路径处理
    test1 = test_audio_path()
    
    # 测试2: 声纹识别
    test2 = test_speaker_id_with_abs_path() if test1 else False
    
    # 测试3: Core模块
    test3 = test_core_with_debug()
    
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    print(f"路径测试: {'通过' if test1 else '失败'}")
    print(f"声纹识别测试: {'通过' if test2 else '失败'}")  
    print(f"Core模块测试: {'通过' if test3 else '失败'}")
    
    if test1 and test2 and test3:
        print("\n[SUCCESS] 路径修复生效，系统准备就绪!")
        print("建议: 现在可以运行完整的音频处理测试")
    else:
        print("\n[FAIL] 仍有问题需要解决")

if __name__ == "__main__":
    main()