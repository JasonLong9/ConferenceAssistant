#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试集成系统
"""

import sys
import os

def test_imports():
    """测试所有导入"""
    print("测试导入模块...")
    
    try:
        from speaker_identification import SpeakerIdentifier, SpeakerSegment
        print("[OK] speaker_identification 导入成功")
    except Exception as e:
        print(f"[ERROR] speaker_identification 导入失败: {e}")
        return False
    
    try:
        from core import MeetingProcessor
        print("[OK] core 导入成功")
    except Exception as e:
        print(f"[ERROR] core 导入失败: {e}")
        return False
    
    return True

def test_speaker_id_creation():
    """测试声纹识别器创建"""
    print("\n测试声纹识别器创建...")
    
    try:
        from speaker_identification import SpeakerIdentifier
        identifier = SpeakerIdentifier()
        print(f"[OK] 声纹识别器创建成功: {identifier.method}, 可用: {identifier.available}")
        return True
    except Exception as e:
        print(f"[ERROR] 声纹识别器创建失败: {e}")
        return False

def test_meeting_processor():
    """测试会议处理器创建"""
    print("\n测试会议处理器创建...")
    
    try:
        from core import MeetingProcessor
        processor = MeetingProcessor()
        print("[OK] 会议处理器创建成功")
        return True
    except Exception as e:
        print(f"[ERROR] 会议处理器创建失败: {e}")
        return False

def main():
    print("=" * 50)
    print("集成系统测试")
    print("=" * 50)
    
    # 测试导入
    if not test_imports():
        print("\n[FAIL] 导入测试失败")
        return 1
    
    # 测试声纹识别器
    if not test_speaker_id_creation():
        print("\n[FAIL] 声纹识别器测试失败")
        return 1
    
    # 测试会议处理器
    if not test_meeting_processor():
        print("\n[FAIL] 会议处理器测试失败")
        return 1
    
    print("\n" + "=" * 50)
    print("[SUCCESS] 所有集成测试通过!")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())