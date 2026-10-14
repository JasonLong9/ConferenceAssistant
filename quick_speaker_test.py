#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速测试声纹识别改进效果
"""

import os
import time

def test_speaker_import():
    """测试改进版声纹识别导入"""
    print("=== 测试改进版声纹识别导入 ===")
    
    try:
        from improved_speaker_id import ImprovedSpeakerIdentifier, SpeakerSegment
        print("✅ 改进版声纹识别导入成功")
        
        # 创建实例
        identifier = ImprovedSpeakerIdentifier()
        print("✅ 改进版识别器创建成功")
        print(f"可用状态: {identifier.available}")
        
        return True
        
    except Exception as e:
        print(f"❌ 改进版导入失败: {e}")
        
        try:
            from speaker_identification import SpeakerIdentifier, SpeakerSegment  
            print("✅ 标准版声纹识别导入成功")
            return False
        except Exception as e2:
            print(f"❌ 标准版导入也失败: {e2}")
            return False

def test_core_import():
    """测试核心系统导入改进"""
    print("\n=== 测试核心系统导入 ===")
    
    try:
        from core import MeetingProcessor, IMPROVED_SPEAKER_ID_AVAILABLE
        print("✅ 核心系统导入成功")
        print(f"改进版可用: {IMPROVED_SPEAKER_ID_AVAILABLE}")
        
        processor = MeetingProcessor()
        print("✅ 会议处理器创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 核心系统导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_loading():
    """测试音频加载功能"""
    print("\n=== 测试音频加载 ===")
    
    test_files = [
        "test_file/admin.MP3",
        "temp_20250830_172409_admin.mp3"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"📁 找到测试文件: {test_file}")
            file_size = os.path.getsize(test_file) / (1024*1024)
            print(f"📊 文件大小: {file_size:.2f} MB")
            
            try:
                from improved_speaker_id import ImprovedSpeakerIdentifier
                identifier = ImprovedSpeakerIdentifier()
                
                print("🎵 测试音频加载...")
                waveform, sample_rate = identifier._load_audio(test_file)
                duration = len(waveform) / sample_rate
                
                print(f"✅ 音频加载成功")
                print(f"   采样率: {sample_rate} Hz")
                print(f"   时长: {duration:.2f} 秒")
                print(f"   样本数: {len(waveform)}")
                
                return True
                
            except Exception as e:
                print(f"❌ 音频加载失败: {e}")
                continue
    
    print("❌ 未找到可用的测试文件")
    return False

def compare_parameters():
    """比较新旧参数设置"""
    print("\n=== 参数设置对比 ===")
    
    print("🔧 改进版参数:")
    print("   - 窗口大小: 3.0秒 (原2.0秒)")
    print("   - 跳跃大小: 1.5秒 (原1.0秒)")
    print("   - 最大说话人: 5个 (原8个)")
    print("   - 特征维度: 32维 (原29维)")
    print("   - 使用轮廓系数评估聚类质量")
    print("   - 更严格的静音检测")
    print("   - 后处理去除短时间说话人")
    
    print("\n🎯 预期改进:")
    print("   - 减少过度分割")
    print("   - 更准确的说话人数量")
    print("   - 更高的识别置信度")

if __name__ == "__main__":
    print("🚀 快速测试改进的声纹识别系统")
    
    # 1. 测试导入
    improved_available = test_speaker_import()
    
    # 2. 测试核心系统
    core_success = test_core_import()
    
    # 3. 测试音频加载
    if improved_available:
        test_audio_loading()
    
    # 4. 显示参数对比
    compare_parameters()
    
    print("\n📊 测试总结:")
    print(f"   改进版可用: {'✅' if improved_available else '❌'}")
    print(f"   核心系统OK: {'✅' if core_success else '❌'}")
    
    if improved_available and core_success:
        print("\n🎉 系统已准备就绪，可以进行完整测试!")
        print("\n💡 建议:")
        print("   1. 重启Web服务以加载改进的声纹识别")
        print("   2. 使用API测试脚本进行完整测试")
        print("   3. 对比8.20音频的识别结果")
    else:
        print("\n⚠️  需要修复问题后再进行完整测试")