#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能声纹识别模块 - 离线版本
优先使用完全离线的声纹识别方案
"""

import torch
from typing import List, Dict, Tuple, Optional
import os
from dataclasses import dataclass
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

@dataclass
class SpeakerSegment:
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float

# 导入离线声纹识别
try:
    from offline_speaker_id import OfflineSpeakerIdentifier
    OFFLINE_AVAILABLE = True
    print("[+] 离线声纹识别可用")
except ImportError as e:
    OFFLINE_AVAILABLE = False
    print(f"[-] 离线声纹识别不可用: {e}")

class SpeakerIdentifier:
    def __init__(self, model_name="offline"):
        """
        智能声纹识别器 - 离线优先版本
        """
        self.method = "offline"
        self.identifier = None
        self.available = False
        
        if OFFLINE_AVAILABLE:
            try:
                self.identifier = OfflineSpeakerIdentifier()
                self.available = True
                print("[OK] 离线声纹识别已就绪")
            except Exception as e:
                print(f"离线声纹识别初始化失败: {e}")
                self.available = False
        
        if not self.available:
            print("[WARN] 声纹识别不可用，将使用普通转写")
    
    def identify_speakers(self, audio_path: str, min_speakers=2, max_speakers=8) -> Dict:
        """执行发言人识别"""
        if not self.available or not self.identifier:
            return {
                'segments': [],
                'total_speakers': 0,
                'total_duration': 0,
                'speaker_list': [],
                'error': '声纹识别不可用'
            }
        
        try:
            return self.identifier.identify_speakers(audio_path, min_speakers, max_speakers)
        except Exception as e:
            print(f"声纹识别执行失败: {e}")
            return {
                'segments': [],
                'total_speakers': 0,
                'total_duration': 0,
                'speaker_list': [],
                'error': f'识别失败: {str(e)}'
            }
    
    def match_transcript_to_speakers(self, whisper_segments: List, speaker_segments: List) -> List[SpeakerSegment]:
        """匹配转写文本与发言人"""
        if not self.available or not self.identifier:
            return []
        
        try:
            return self.identifier.match_transcript_to_speakers(whisper_segments, speaker_segments)
        except Exception as e:
            print(f"文本匹配失败: {e}")
            return []

def test_speaker_identification(audio_path: str):
    """测试声纹识别功能"""
    print("="*60)
    print("智能声纹识别测试 (离线版本)")
    print("="*60)
    
    if not os.path.exists(audio_path):
        print(f"错误：音频文件不存在: {audio_path}")
        return None
    
    try:
        # 创建识别器
        identifier = SpeakerIdentifier()
        
        print(f"使用方案: {identifier.method}")
        print(f"识别器可用: {identifier.available}")
        
        if not identifier.available:
            print("声纹识别不可用")
            return None
        
        # 执行识别
        result = identifier.identify_speakers(audio_path, min_speakers=2, max_speakers=6)
        
        print(f"\n识别结果:")
        print(f"发言人数量: {result['total_speakers']}")
        print(f"音频总长: {result['total_duration']:.2f}秒")
        
        if result.get('error'):
            print(f"错误: {result['error']}")
        else:
            print(f"\n前10个发言人段落:")
            for i, seg in enumerate(result['segments'][:10]):
                conf = seg.get('confidence', 0)
                print(f"  {i+1:2d}. {seg['speaker']}: {seg['start']:.1f}s-{seg['end']:.1f}s "
                      f"({seg['duration']:.1f}s) 置信度:{conf:.2f}")
            
            if len(result['segments']) > 10:
                print(f"  ... 还有 {len(result['segments']) - 10} 个段落")
        
        return result
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import sys
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "test_file/河北人设仲裁需求会-1.mp3"
    test_speaker_identification(audio_file)
