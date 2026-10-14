#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试声纹识别集成问题
"""

import sys
import traceback

def test_speaker_identification_integration():
    """测试完整的声纹识别集成流程"""
    audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    
    print("=" * 60)
    print("调试声纹识别集成问题")
    print("=" * 60)
    
    try:
        # 第1步：测试导入
        print("第1步：导入模块...")
        from speaker_identification import SpeakerIdentifier
        from core import LocalWhisper
        print("[OK] 模块导入成功")
        
        # 第2步：初始化Whisper
        print("\n第2步：初始化Whisper...")
        whisper = LocalWhisper()
        print("[OK] Whisper初始化成功")
        
        # 第3步：音频转写
        print("\n第3步：执行音频转写...")
        segments = whisper.transcribe_with_timestamps(audio_path)
        print(f"[OK] 转写完成，共 {len(segments)} 个片段")
        if segments:
            print(f"   前3个片段：")
            for i, seg in enumerate(segments[:3]):
                print(f"     {i+1}. {seg['start']:.1f}s-{seg['end']:.1f}s: {seg['text'][:50]}...")
        
        # 第4步：初始化声纹识别器
        print("\n第4步：初始化声纹识别器...")
        speaker_identifier = SpeakerIdentifier()
        print(f"[OK] 声纹识别器创建完成")
        print(f"   可用状态: {speaker_identifier.available}")
        print(f"   方法: {speaker_identifier.method}")
        
        if not speaker_identifier.available:
            print("[ERROR] 声纹识别器不可用，无法继续测试")
            return False
        
        # 第5步：执行声纹识别
        print("\n第5步：执行声纹识别...")
        speaker_result = speaker_identifier.identify_speakers(audio_path, min_speakers=2, max_speakers=8)
        
        print(f"[OK] 声纹识别完成")
        print(f"   总发言人数: {speaker_result.get('total_speakers', 0)}")
        print(f"   音频总长: {speaker_result.get('total_duration', 0):.2f}秒")
        
        if speaker_result.get('error'):
            print(f"[ERROR] 声纹识别错误: {speaker_result['error']}")
            return False
        
        # 第6步：匹配转写文本与发言人
        print("\n第6步：匹配转写文本与发言人...")
        matched_segments = speaker_identifier.match_transcript_to_speakers(
            segments, speaker_result['segments']
        )
        
        print(f"[OK] 文本匹配完成，共 {len(matched_segments)} 个匹配片段")
        
        if matched_segments:
            print("   前5个匹配片段：")
            for i, seg in enumerate(matched_segments[:5]):
                print(f"     {i+1}. {seg.speaker_id}: {seg.start_time:.1f}s-{seg.end_time:.1f}s")
                print(f"        {seg.text[:80]}...")
        
        # 第7步：统计发言人数量
        unique_speakers = list(set(seg.speaker_id for seg in matched_segments))
        final_speaker_count = len(unique_speakers)
        
        print(f"\n第7步：最终统计")
        print(f"[OK] 最终发言人数量: {final_speaker_count}")
        print(f"   发言人列表: {unique_speakers}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
        return False

def test_core_integration():
    """测试Core模块的集成"""
    print("\n" + "=" * 60)
    print("测试Core模块集成")
    print("=" * 60)
    
    try:
        from core import MeetingProcessor
        
        processor = MeetingProcessor()
        print("[OK] MeetingProcessor创建成功")
        
        # 测试短音频处理（如果有的话）
        audio_path = "test_file/河北人设仲裁需求会-1.mp3"
        
        print(f"\n开始处理音频: {audio_path}")
        print("(这可能需要较长时间...)")
        
        result = processor.process_with_speaker_id(audio_path, output_dir="debug_output")
        
        print(f"[OK] 处理完成")
        print(f"   发言人数量: {result.get('speaker_count', 0)}")
        print(f"   转写长度: {len(result.get('transcript', ''))}")
        print(f"   会议纪要长度: {len(result.get('minutes', ''))}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Core集成测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    print("开始调试声纹识别集成问题\n")
    
    # 测试1：独立声纹识别流程
    success1 = test_speaker_identification_integration()
    
    # 如果独立测试成功，再测试完整集成
    if success1:
        success2 = test_core_integration()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("[SUCCESS] 所有测试通过！声纹识别集成正常")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("[FAIL] Core集成存在问题")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("[FAIL] 独立声纹识别测试失败")
        print("=" * 60)

if __name__ == "__main__":
    main()