#!/usr/bin/env python3
"""
Test the audio duration for 8.28.mp3
"""

from core import get_audio_duration, generate_dynamic_system_prompt

def test_828_audio():
    """Test getting audio duration from 8.28.mp3"""
    print("=== 测试8.28.mp3音频文件时长 ===\n")
    
    audio_file = "test_file/8.28.mp3"
    try:
        duration_seconds = get_audio_duration(audio_file)
        duration_minutes = int(duration_seconds / 60)
        print(f"文件: {audio_file}")
        print(f"时长: {duration_seconds:.1f}秒 ({duration_minutes}分钟)")
        
        # Generate prompt for this specific duration
        print(f"\n--- 为{duration_minutes}分钟音频生成的动态提示词 ---")
        prompt = generate_dynamic_system_prompt(duration_minutes)
        
        # Extract time segments
        time_part = prompt.split("请根据以下时间段生成时间点摘要：")
        if len(time_part) > 1:
            time_segments = time_part[1].split("\n</instruction>")[0]
            print(f"时间段: {time_segments}")
            
        return duration_minutes, time_segments
            
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return None, None

if __name__ == "__main__":
    test_828_audio()