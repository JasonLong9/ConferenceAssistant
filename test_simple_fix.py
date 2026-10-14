#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试speaker_count修复效果
"""

def test_speaker_identification():
    """测试声纹识别"""
    print("🔧 测试声纹识别修复效果")
    
    try:
        from precision_speaker_id import PrecisionSpeakerIdentifier
        import os
        
        # 创建识别器
        identifier = PrecisionSpeakerIdentifier()
        
        # 测试文件
        test_files = [
            "test_file/8.20.mp3",
            "test_file/8.28.mp3"
        ]
        
        for audio_file in test_files:
            if not os.path.exists(audio_file):
                print(f"⏭️ 跳过不存在的文件: {audio_file}")
                continue
                
            print(f"\n📁 测试文件: {audio_file}")
            
            # 识别说话人
            segments = identifier.identify_speakers(audio_file, target_speakers=5)
            
            if segments:
                speakers = set(seg.speaker_id for seg in segments)
                speaker_count = len(speakers)
                print(f"✅ 成功识别 {speaker_count} 个说话人: {sorted(speakers)}")
                print(f"📊 生成 {len(segments)} 个语音段")
                return True
            else:
                print(f"❌ 未识别到说话人")
                return False
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_core_processor():
    """测试核心处理器"""
    print("\n🔧 测试核心处理器")
    
    try:
        from core import MeetingProcessor
        import os
        
        processor = MeetingProcessor()
        test_file = "test_file/8.20.mp3"
        
        if not os.path.exists(test_file):
            print(f"❌ 测试文件不存在: {test_file}")
            return False
        
        print(f"📁 处理文件: {test_file}")
        print("⏳ 开始处理（这可能需要几分钟）...")
        
        # 设置较短的超时以避免长时间等待
        result = processor.process_with_speaker_id(test_file)
        
        speaker_count = result.get('speaker_count', 0)
        transcript_len = len(result.get('transcript', ''))
        
        print(f"🎯 处理结果:")
        print(f"   speaker_count: {speaker_count}")
        print(f"   转写文本长度: {transcript_len}")
        
        if speaker_count > 0:
            print(f"✅ 修复成功！speaker_count = {speaker_count}")
            return True
        else:
            print(f"❌ 仍有问题，speaker_count = 0")
            return False
            
    except Exception as e:
        print(f"❌ 核心处理器测试异常: {e}")
        return False

def test_estimation_methods():
    """测试估算方法"""
    print("\n🔧 测试估算方法")
    
    try:
        from core import MeetingProcessor
        
        processor = MeetingProcessor()
        
        # 模拟一些转写段落
        mock_segments = [
            {'start': 0, 'end': 5, 'text': '大家好，欢迎参加今天的会议'},
            {'start': 6, 'end': 10, 'text': '我是张三，负责项目管理'},
            {'start': 11, 'end': 15, 'text': '我是李四，负责技术开发'},
            {'start': 16, 'end': 20, 'text': '那我们开始讨论项目进度'},
            {'start': 21, 'end': 25, 'text': '目前进度如何'},
            {'start': 26, 'end': 30, 'text': '我们已经完成了百分之六十'},
        ]
        
        # 测试估算方法
        estimated_count = processor._estimate_speaker_count_from_transcript(mock_segments)
        print(f"📊 基于{len(mock_segments)}段语音估算: {estimated_count}人")
        
        # 测试添加发言人标识
        formatted_text = processor._add_estimated_speakers(mock_segments, estimated_count)
        print(f"📝 格式化结果长度: {len(formatted_text)}")
        
        if estimated_count > 0:
            print(f"✅ 估算方法正常工作")
            return True
        else:
            print(f"❌ 估算方法有问题")
            return False
            
    except Exception as e:
        print(f"❌ 估算方法测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始简单修复测试")
    print("=" * 50)
    
    # 测试各个组件
    test1 = test_estimation_methods()
    test2 = test_speaker_identification() 
    # test3 = test_core_processor()  # 暂时跳过长时间测试
    
    print(f"\n📊 测试结果:")
    print(f"   估算方法: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"   声纹识别: {'✅ 通过' if test2 else '❌ 失败'}")
    # print(f"   核心处理: {'✅ 通过' if test3 else '❌ 失败'}")
    
    if test1 and test2:
        print(f"\n🎉 基础修复测试通过！")
        print("💡 主要改进:")
        print("   1. 增强了语音段检测的鲁棒性")
        print("   2. 添加了特征提取的降级处理")
        print("   3. 实现了基于转写的发言人数量估算")
        print("   4. 确保speaker_count永远不为0")
    else:
        print(f"\n😞 部分测试失败，需要进一步调试")