#!/usr/bin/env python3
"""
Test script to verify the dynamic prompt generation based on audio duration
"""

from core import generate_dynamic_system_prompt, get_audio_duration

def test_dynamic_prompt():
    """Test the dynamic prompt generation for different durations"""
    print("=== 测试动态提示词生成 ===\n")
    
    # Test various durations
    test_durations = [5, 10, 15, 27, 30, 45, 60, 90, 120]
    
    for minutes in test_durations:
        print(f"--- {minutes}分钟会议的动态提示词 ---")
        prompt = generate_dynamic_system_prompt(minutes)
        
        # Extract the time segments part from the prompt
        time_part = prompt.split("请根据以下时间段生成时间点摘要：")
        if len(time_part) > 1:
            time_segments = time_part[1].split("\n</instruction>")[0]
            print(f"音频时长: {minutes}分钟")
            print(f"时间段: {time_segments}")
        print()

def test_audio_duration():
    """Test getting audio duration from 8.20.mp3"""
    print("=== 测试音频时长获取 ===\n")
    
    audio_file = "8.20.mp3"
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
            
    except Exception as e:
        print(f"获取音频时长失败: {e}")

if __name__ == "__main__":
    test_dynamic_prompt()
    test_audio_duration()