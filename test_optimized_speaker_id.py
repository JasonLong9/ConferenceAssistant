#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试优化后的声纹识别系统
"""

import sys
import time

def test_optimized_system():
    """测试优化后的完整系统"""
    audio_path = "test_file/河北人设仲裁需求会-1.mp3"
    
    print("=" * 60)
    print("测试优化后的声纹识别系统")
    print("=" * 60)
    
    try:
        from core import MeetingProcessor
        
        print("创建会议处理器...")
        processor = MeetingProcessor()
        
        print(f"开始处理音频: {audio_path}")
        print("注意: 这是一个46分钟的音频文件，处理时间较长")
        
        start_time = time.time()
        result = processor.process_with_speaker_id(audio_path, output_dir="optimized_output")
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"\n处理完成！用时: {processing_time:.2f}秒")
        print("=" * 60)
        print("结果统计:")
        print(f"  发言人数量: {result.get('speaker_count', 0)}")
        print(f"  转写文本长度: {len(result.get('transcript', ''))}")
        print(f"  清理后文本长度: {len(result.get('cleaned', ''))}")
        print(f"  会议纪要长度: {len(result.get('minutes', ''))}")
        print(f"  会议名称: {result.get('meeting_name', '未识别')}")
        
        # 检查是否成功识别发言人
        speaker_count = result.get('speaker_count', 0)
        if speaker_count > 0:
            print(f"\n[SUCCESS] 成功! 识别出 {speaker_count} 个发言人")
            
            # 显示转写文本片段（带发言人）
            transcript = result.get('transcript', '')
            lines = transcript.split('\n')[:10]  # 显示前10行
            
            print("\n前10行转写结果:")
            for i, line in enumerate(lines, 1):
                if line.strip():
                    print(f"  {i:2d}. {line}")
        else:
            print("\n[FAIL] 失败: 未能识别出发言人")
            
        return speaker_count > 0
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("开始测试优化后的声纹识别系统\n")
    
    success = test_optimized_system()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 优化成功！声纹识别系统工作正常")
        print("现在可以正确识别多个发言人并生成带标签的转写文本")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 仍有问题需要进一步调试")
        print("=" * 60)

if __name__ == "__main__":
    main()