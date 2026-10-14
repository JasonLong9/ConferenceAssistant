#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试修复后的完整系统
"""

import os
import time

def test_fixed_system():
    """测试修复后的完整系统"""
    audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    
    print("=" * 60)
    print("测试修复后的完整声纹识别系统")
    print("=" * 60)
    
    try:
        from core import MeetingProcessor
        
        print("创建会议处理器...")
        processor = MeetingProcessor()
        
        print(f"开始处理音频: {audio_path}")
        print(f"音频文件绝对路径: {os.path.abspath(audio_path)}")
        print(f"音频文件存在: {os.path.exists(os.path.abspath(audio_path))}")
        
        start_time = time.time()
        result = processor.process_with_speaker_id(audio_path, output_dir="fixed_output")
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"\n处理完成！用时: {processing_time:.1f}秒")
        print("=" * 60)
        print("结果分析:")
        
        # 检查发言人数量
        speaker_count = result.get('speaker_count', 0)
        print(f"  发言人数量: {speaker_count}")
        
        # 检查各个结果的长度
        transcript = result.get('transcript', '')
        cleaned = result.get('cleaned', '')
        minutes = result.get('minutes', '')
        
        print(f"  转写文本长度: {len(transcript)} 字符")
        print(f"  清理后文本长度: {len(cleaned)} 字符")
        print(f"  会议纪要长度: {len(minutes)} 字符")
        print(f"  会议名称: {result.get('meeting_name', '未识别')}")
        
        # 检查是否包含发言人标识
        has_speaker_labels = False
        if 'Speaker_' in transcript or '发言人A' in transcript or '发言人B' in transcript:
            has_speaker_labels = True
            print("  [SUCCESS] 转写文本包含发言人标识")
        else:
            print("  [WARNING] 转写文本不包含发言人标识")
        
        # 显示转写文本的前几行
        print(f"\n  转写文本前10行:")
        lines = transcript.split('\n')[:10]
        for i, line in enumerate(lines, 1):
            if line.strip():
                print(f"    {i:2d}. {line[:80]}{'...' if len(line) > 80 else ''}")
        
        # 最终判断
        success = speaker_count > 0
        
        if success:
            print(f"\n🎉 [SUCCESS] 系统修复成功!")
            print(f"   ✓ 声纹识别工作正常，识别出 {speaker_count} 个发言人")
            print(f"   ✓ 音频处理完成，用时 {processing_time:.1f} 秒")
            if has_speaker_labels:
                print(f"   ✓ 转写文本包含发言人区分")
            else:
                print(f"   ⚠ 转写文本需要进一步检查发言人标识")
        else:
            print(f"\n❌ [FAIL] 系统仍有问题:")
            print(f"   ✗ 发言人数量为 {speaker_count}")
            
        return success
        
    except Exception as e:
        print(f"❌ [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_audio_file_info():
    """显示音频文件信息"""
    print("=" * 60)
    print("音频文件信息")
    print("=" * 60)
    
    audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    abs_path = os.path.abspath(audio_path)
    
    if os.path.exists(abs_path):
        file_size = os.path.getsize(abs_path) / (1024 * 1024)
        print(f"文件路径: {abs_path}")
        print(f"文件大小: {file_size:.2f} MB")
        
        # 从之前的测试结果，我们知道音频时长约46.6分钟
        print(f"音频时长: 约46.6分钟 (2794秒)")
        print(f"预期发言人数: 3-6个")
    else:
        print(f"音频文件不存在: {abs_path}")

def main():
    print("开始测试修复后的声纹识别系统\n")
    
    # 显示音频信息
    show_audio_file_info()
    
    print(f"\n注意: 由于音频文件较长(46分钟)，完整处理可能需要5-10分钟")
    print("建议: 如需测试其他音频文件，请更改audio_path变量")
    
    # 询问是否继续
    print(f"\n是否继续进行完整测试？这将需要较长时间...")
    print("(直接运行，无需确认)")
    
    # 执行测试
    success = test_fixed_system()
    
    print(f"\n" + "=" * 60)
    if success:
        print("🎉 声纹识别系统修复成功!")
        print("现在speaker_count应该不再为0")
        print("转写文本应该包含发言人区分")
    else:
        print("❌ 系统仍需进一步调试")
    print("=" * 60)

if __name__ == "__main__":
    main()