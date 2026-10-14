#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接测试Whisper模型是否能正常工作
"""

import os
import time
from core import LocalWhisper

def test_whisper_direct():
    """直接测试Whisper转写功能"""
    audio_file = "test_file/admin.MP3"
    
    if not os.path.exists(audio_file):
        print(f"❌ 测试文件不存在: {audio_file}")
        return
    
    file_size = os.path.getsize(audio_file)
    print(f"📁 测试文件: {audio_file}")
    print(f"📊 文件大小: {file_size / 1024:.2f} KB")
    
    try:
        print("🚀 初始化Whisper模型...")
        whisper = LocalWhisper()
        
        print("🎵 开始音频转写...")
        start_time = time.time()
        
        transcript = whisper.transcribe(audio_file)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ 转写完成! 耗时: {processing_time:.2f}秒")
        print(f"📝 转写结果长度: {len(transcript)}字符")
        print("=" * 50)
        print("转写内容预览:")
        print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
        print("=" * 50)
        
        # 保存结果
        with open("whisper_test_result.txt", "w", encoding="utf-8") as f:
            f.write(transcript)
        print("💾 转写结果已保存到 whisper_test_result.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Whisper转写失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 直接测试Whisper转写功能")
    success = test_whisper_direct()
    
    if success:
        print("🎉 Whisper测试成功!")
    else:
        print("💥 Whisper测试失败!")