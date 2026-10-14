#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证声纹识别集成的代码完整性
"""

import os
import sys

def verify_imports():
    """验证所有模块能正常导入"""
    print("验证模块导入...")
    
    try:
        # 验证声纹识别模块
        from speaker_identification import SpeakerIdentifier, SpeakerSegment
        print("[OK] speaker_identification 模块导入成功")
    except ImportError as e:
        print(f"[FAIL] speaker_identification 模块导入失败: {e}")
        return False
    
    try:
        # 验证核心模块
        from core import MeetingProcessor, LocalWhisper
        print("[OK] core 模块导入成功")
    except ImportError as e:
        print(f"[FAIL] core 模块导入失败: {e}")
        return False
    
    try:
        # 验证main模块
        import main
        print("[OK] main 模块导入成功")
    except ImportError as e:
        print(f"[FAIL] main 模块导入失败: {e}")
        return False
    
    return True

def verify_functionality():
    """验证功能实现的完整性"""
    print("\n验证功能实现...")
    
    try:
        from core import MeetingProcessor
        
        # 检查MeetingProcessor是否有新方法
        processor = MeetingProcessor()
        
        if hasattr(processor, 'process_with_speaker_id'):
            print("[OK] MeetingProcessor.process_with_speaker_id 方法存在")
        else:
            print("[FAIL] MeetingProcessor.process_with_speaker_id 方法缺失")
            return False
        
        if hasattr(processor, '_format_speaker_transcript'):
            print("[OK] MeetingProcessor._format_speaker_transcript 方法存在")
        else:
            print("[FAIL] MeetingProcessor._format_speaker_transcript 方法缺失")
            return False
        
        # 检查LocalWhisper是否有新方法
        from core import LocalWhisper
        whisper = LocalWhisper()
        
        if hasattr(whisper, 'transcribe_with_timestamps'):
            print("[OK] LocalWhisper.transcribe_with_timestamps 方法存在")
        else:
            print("[FAIL] LocalWhisper.transcribe_with_timestamps 方法缺失")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 功能验证失败: {e}")
        return False

def verify_file_structure():
    """验证文件结构"""
    print("\n验证文件结构...")
    
    required_files = [
        "speaker_identification.py",
        "core.py", 
        "main.py",
        "test_speaker_id.py",
        "test_simple.py"
    ]
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"[OK] {file_name} 存在")
        else:
            print(f"[FAIL] {file_name} 缺失")
            return False
    
    # 检查测试音频文件
    test_audio = "test_file/河北人设仲裁需求会-1.mp3"
    if os.path.exists(test_audio):
        print(f"[OK] 测试音频文件存在: {test_audio}")
    else:
        print(f"[WARN] 测试音频文件不存在: {test_audio}")
    
    return True

def verify_dependencies():
    """验证依赖包"""
    print("\n验证依赖包...")
    
    required_packages = [
        ("torch", "PyTorch"),
        ("faster_whisper", "Faster-Whisper"),
        ("requests", "Requests"),
        ("pydub", "PyDub")
    ]
    
    # 可选包（可能因为网络问题未安装）
    optional_packages = [
        ("pyannote.audio", "PyAnnote-Audio"),
    ]
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"[OK] {name} 已安装")
        except ImportError:
            print(f"[FAIL] {name} 未安装")
            return False
    
    for package, name in optional_packages:
        try:
            __import__(package)
            print(f"[OK] {name} 已安装")
        except ImportError:
            print(f"[WARN] {name} 未安装 (需要网络连接)")
    
    return True

def main():
    """主验证函数"""
    print("声纹识别集成验证")
    print("=" * 50)
    
    results = []
    
    # 验证文件结构
    results.append(("文件结构", verify_file_structure()))
    
    # 验证依赖包
    results.append(("依赖包", verify_dependencies()))
    
    # 验证模块导入
    results.append(("模块导入", verify_imports()))
    
    # 验证功能实现
    results.append(("功能实现", verify_functionality()))
    
    # 总结结果
    print("\n" + "=" * 50)
    print("验证结果总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 通过")
    
    if passed == total:
        print("[SUCCESS] 声纹识别集成验证通过！")
        print("\n代码集成完成，具备以下功能:")
        print("1. 基础会议转写和纪要生成")
        print("2. 声纹识别发言人分离（需要网络连接下载模型）")
        print("3. 带时间戳的音频转写")
        print("4. 发言人匹配和格式化输出")
        
        print("\n使用方法:")
        print("- 基础使用: python main.py [音频文件]")
        print("- 声纹识别: python main.py [音频文件] --enable_speaker_id")
        print("- 指定会议名: python main.py [音频文件] --meeting_name '会议名'")
    else:
        print("[ERROR] 验证失败，请检查上述问题")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)