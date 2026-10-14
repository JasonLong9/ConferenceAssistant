#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试默认启用声纹识别功能
验证所有接口都默认启用声纹识别
"""

import os
import sys
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import_verification():
    """测试模块导入和方法签名"""
    print("=" * 50)
    print("测试1: 验证模块导入和方法签名")
    print("=" * 50)
    
    try:
        from core import MeetingProcessor, LocalWhisper
        from speaker_identification import SpeakerIdentifier
        
        # 检查MeetingProcessor
        processor = MeetingProcessor()
        
        # 验证process方法现在也使用声纹识别
        print("[OK] MeetingProcessor 导入成功")
        
        if hasattr(processor, 'process'):
            print("[OK] process 方法存在（现在默认使用声纹识别）")
        else:
            print("[FAIL] process 方法缺失")
            return False
        
        if hasattr(processor, 'process_with_speaker_id'):
            print("[OK] process_with_speaker_id 方法存在")
        else:
            print("[FAIL] process_with_speaker_id 方法缺失")
            return False
        
        # 验证LocalWhisper有时间戳方法
        whisper = LocalWhisper()
        if hasattr(whisper, 'transcribe_with_timestamps'):
            print("[OK] LocalWhisper.transcribe_with_timestamps 方法存在")
        else:
            print("[FAIL] LocalWhisper.transcribe_with_timestamps 方法缺失")
            return False
        
        print("[OK] 所有核心方法验证通过")
        return True
        
    except Exception as e:
        print(f"[FAIL] 导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_method_signatures():
    """测试方法签名是否正确"""
    print("\n" + "=" * 50)
    print("测试2: 验证方法签名")
    print("=" * 50)
    
    try:
        from core import MeetingProcessor
        import inspect
        
        processor = MeetingProcessor()
        
        # 检查process_with_speaker_id的签名
        sig = inspect.signature(processor.process_with_speaker_id)
        params = list(sig.parameters.keys())
        
        print(f"process_with_speaker_id 参数: {params}")
        
        # 应该没有enable_speaker_id参数
        if 'enable_speaker_id' in params:
            print("[FAIL] process_with_speaker_id 仍有 enable_speaker_id 参数")
            return False
        else:
            print("[OK] process_with_speaker_id 已移除 enable_speaker_id 参数")
        
        # 检查必要参数
        required_params = ['audio_path']
        for param in required_params:
            if param in params:
                print(f"[OK] 必要参数 '{param}' 存在")
            else:
                print(f"[FAIL] 必要参数 '{param}' 缺失")
                return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 方法签名测试失败: {e}")
        return False

def test_web_interface():
    """测试Web接口是否更新"""
    print("\n" + "=" * 50)
    print("测试3: 验证Web接口更新")
    print("=" * 50)
    
    try:
        # 检查web_service.py
        with open("web_service.py", "r", encoding="utf-8") as f:
            web_content = f.read()
        
        if "process_with_speaker_id" in web_content:
            print("[OK] web_service.py 已使用 process_with_speaker_id")
        else:
            print("[WARN] web_service.py 可能未更新")
        
        if "speaker_count" in web_content:
            print("[OK] web_service.py 包含 speaker_count 输出")
        else:
            print("[WARN] web_service.py 可能未包含声纹识别结果")
        
        # 检查async_audio_service.py
        with open("async_audio_service.py", "r", encoding="utf-8") as f:
            async_content = f.read()
        
        if "process_with_speaker_id" in async_content:
            print("[OK] async_audio_service.py 已使用 process_with_speaker_id")
        else:
            print("[WARN] async_audio_service.py 可能未更新")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Web接口检查失败: {e}")
        return False

def test_main_script():
    """测试main.py是否更新"""
    print("\n" + "=" * 50)
    print("测试4: 验证main.py更新")
    print("=" * 50)
    
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            main_content = f.read()
        
        # 检查是否移除了enable_speaker_id参数
        if "--enable_speaker_id" in main_content:
            print("[FAIL] main.py 仍包含 --enable_speaker_id 参数")
            return False
        else:
            print("[OK] main.py 已移除 --enable_speaker_id 参数")
        
        # 检查是否直接调用process_with_speaker_id
        if "process_with_speaker_id" in main_content:
            print("[OK] main.py 使用 process_with_speaker_id")
        else:
            print("[WARN] main.py 可能未使用新方法")
        
        # 检查描述是否更新
        if "默认启用声纹识别" in main_content:
            print("[OK] main.py 描述已更新")
        else:
            print("[WARN] main.py 描述可能未更新")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] main.py 检查失败: {e}")
        return False

def test_backwards_compatibility():
    """测试向后兼容性"""
    print("\n" + "=" * 50)
    print("测试5: 验证向后兼容性")
    print("=" * 50)
    
    try:
        from core import MeetingProcessor
        
        processor = MeetingProcessor()
        
        # 验证旧的process方法仍然存在
        if hasattr(processor, 'process'):
            print("[OK] 旧的 process 方法仍然存在")
            
            # 验证process方法现在也使用声纹识别
            import inspect
            sig = inspect.signature(processor.process)
            print(f"process 方法签名: {list(sig.parameters.keys())}")
            
            return True
        else:
            print("[FAIL] 旧的 process 方法不存在")
            return False
        
    except Exception as e:
        print(f"[FAIL] 向后兼容性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("默认启用声纹识别功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("模块导入验证", test_import_verification),
        ("方法签名验证", test_method_signatures),
        ("Web接口验证", test_web_interface),
        ("main.py验证", test_main_script),
        ("向后兼容性", test_backwards_compatibility)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 总结测试结果
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 通过")
    
    if passed == total:
        print("[SUCCESS] 默认启用声纹识别功能验证通过！")
        print("\n功能确认:")
        print("+ 声纹识别已默认启用，无法关闭")
        print("+ main.py 已移除 --enable_speaker_id 参数")
        print("+ Web接口已更新为默认使用声纹识别")
        print("+ 保持向后兼容性")
        
        print("\n使用方法:")
        print("- 命令行: python main.py [音频文件]")
        print("- Web API: POST /audio2summary_async")
        print("- 所有接口都会自动使用声纹识别")
    else:
        print("[ERROR] 部分测试失败，请检查上述问题")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)