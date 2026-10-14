#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试完整处理流程中的声纹识别问题
"""

import os
import traceback

def debug_full_process():
    """调试完整的处理流程"""
    audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    
    print("=" * 60)
    print("调试完整处理流程")
    print("=" * 60)
    
    # 1. 检查音频文件
    print("1. 检查音频文件...")
    abs_audio_path = os.path.abspath(audio_path)
    print(f"   音频文件路径: {abs_audio_path}")
    print(f"   文件存在: {os.path.exists(abs_audio_path)}")
    
    if os.path.exists(abs_audio_path):
        file_size = os.path.getsize(abs_audio_path) / (1024 * 1024)  # MB
        print(f"   文件大小: {file_size:.2f} MB")
    
    try:
        # 2. 导入和初始化
        print("\n2. 导入核心模块...")
        from core import MeetingProcessor
        from speaker_identification import SpeakerIdentifier
        
        # 3. 创建处理器
        print("\n3. 创建会议处理器...")
        processor = MeetingProcessor()
        print(f"   处理器创建成功")
        
        # 4. 检查声纹识别器状态
        print("\n4. 检查声纹识别器状态...")
        if processor.speaker_identifier is None:
            print("   声纹识别器未初始化，手动初始化...")
            processor.speaker_identifier = SpeakerIdentifier()
        
        print(f"   声纹识别器可用: {processor.speaker_identifier.available}")
        print(f"   识别方法: {processor.speaker_identifier.method}")
        
        if not processor.speaker_identifier.available:
            print("   [ERROR] 声纹识别器不可用!")
            return False
        
        # 5. 分步测试转写部分
        print("\n5. 测试音频转写...")
        try:
            segments = processor.whisper.transcribe_with_timestamps(abs_audio_path)
            print(f"   转写成功，共 {len(segments)} 个片段")
            
            if segments:
                print(f"   前3个转写片段:")
                for i, seg in enumerate(segments[:3]):
                    print(f"     {i+1}. {seg['start']:.1f}s-{seg['end']:.1f}s: {seg['text'][:50]}...")
                    
                # 计算总时长
                if segments:
                    total_duration = segments[-1]['end']
                    print(f"   音频总时长: {total_duration:.2f}秒 ({total_duration/60:.1f}分钟)")
                    
        except Exception as e:
            print(f"   [ERROR] 转写失败: {e}")
            traceback.print_exc()
            return False
        
        # 6. 独立测试声纹识别
        print("\n6. 独立测试声纹识别...")
        try:
            speaker_result = processor.speaker_identifier.identify_speakers(
                abs_audio_path, min_speakers=2, max_speakers=8
            )
            
            print(f"   声纹识别返回结果:")
            print(f"     total_speakers: {speaker_result.get('total_speakers', 'None')}")
            print(f"     total_duration: {speaker_result.get('total_duration', 'None')}")
            print(f"     segments数量: {len(speaker_result.get('segments', []))}")
            print(f"     error: {speaker_result.get('error', 'None')}")
            
            if speaker_result.get('error'):
                print(f"   [ERROR] 声纹识别出错: {speaker_result['error']}")
                return False
                
        except Exception as e:
            print(f"   [ERROR] 声纹识别异常: {e}")
            traceback.print_exc()
            return False
        
        # 7. 测试文本匹配
        print("\n7. 测试文本与发言人匹配...")
        try:
            if speaker_result.get('segments'):
                matched_segments = processor.speaker_identifier.match_transcript_to_speakers(
                    segments, speaker_result['segments']
                )
                print(f"   匹配成功，共 {len(matched_segments)} 个匹配片段")
                
                # 统计发言人
                unique_speakers = list(set(seg.speaker_id for seg in matched_segments))
                print(f"   识别出的发言人: {len(unique_speakers)} 个")
                print(f"   发言人列表: {unique_speakers}")
                
                if len(unique_speakers) > 0:
                    print("   [SUCCESS] 文本匹配成功！")
                    return True
                else:
                    print("   [ERROR] 未识别出发言人")
                    return False
            else:
                print("   [ERROR] 没有发言人片段可匹配")
                return False
                
        except Exception as e:
            print(f"   [ERROR] 文本匹配失败: {e}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"\n[ERROR] 调试过程出错: {e}")
        traceback.print_exc()
        return False

def test_core_process_method():
    """测试Core的process_with_speaker_id方法"""
    print("\n" + "=" * 60)
    print("测试 Core.process_with_speaker_id 方法")
    print("=" * 60)
    
    audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    
    try:
        from core import MeetingProcessor
        
        processor = MeetingProcessor()
        
        # 手动设置输出目录
        output_dir = "debug_process_output"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"开始处理音频: {audio_path}")
        print("(这可能需要很长时间...)")
        
        # 调用处理方法
        result = processor.process_with_speaker_id(audio_path, output_dir=output_dir)
        
        print("\n处理完成！结果分析:")
        print(f"  speaker_count: {result.get('speaker_count', 'None')}")
        print(f"  transcript长度: {len(result.get('transcript', ''))}")
        print(f"  cleaned长度: {len(result.get('cleaned', ''))}")
        print(f"  minutes长度: {len(result.get('minutes', ''))}")
        
        # 检查transcript是否包含发言人标识
        transcript = result.get('transcript', '')
        if 'Speaker_' in transcript or '发言人' in transcript:
            print("  [SUCCESS] transcript包含发言人标识")
        else:
            print("  [WARNING] transcript不包含发言人标识")
        
        # 检查为什么speaker_count为0
        if result.get('speaker_count', 0) == 0:
            print("  [ERROR] speaker_count为0，处理失败")
            return False
        else:
            print(f"  [SUCCESS] speaker_count为{result['speaker_count']}")
            return True
            
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    print("开始调试完整处理流程\n")
    
    # 测试1: 分步调试
    print("步骤 1: 分步调试声纹识别流程")
    success1 = debug_full_process()
    
    if success1:
        print("\n[INFO] 分步测试成功，现在测试完整流程...")
        # 测试2: 完整流程测试
        print("\n步骤 2: 测试完整的process_with_speaker_id方法")
        success2 = test_core_process_method()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("[SUCCESS] 完整流程测试成功！")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("[FAIL] 完整流程存在问题")
            print(f"分步测试: {'通过' if success1 else '失败'}")
            print(f"完整流程: {'通过' if success2 else '失败'}")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("[FAIL] 分步测试失败，无法继续")
        print("=" * 60)

if __name__ == "__main__":
    main()