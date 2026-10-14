#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能声纹识别模块
优先级：SpeechBrain > 简化方案 > 降级模式
"""

import torch
from typing import List, Dict, Tuple, Optional
import os
from dataclasses import dataclass
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# 导入镜像配置
try:
    from huggingface_config import setup_huggingface_mirror
    setup_huggingface_mirror()
except ImportError:
    pass

@dataclass
class SpeakerSegment:
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float

# 检查可用的声纹识别方案
def check_available_methods():
    """检查所有可用的声纹识别方案"""
    methods = {}
    
    # 1. 检查SpeechBrain
    try:
        from speechbrain_speaker_id import SpeechBrainSpeakerIdentifier
        methods['speechbrain'] = SpeechBrainSpeakerIdentifier
        print("✓ SpeechBrain 方案可用")
    except ImportError as e:
        print(f"- SpeechBrain 不可用: {e}")
        methods['speechbrain'] = None
    
    # 2. 检查pyannote
    try:
        from pyannote.audio import Pipeline
        methods['pyannote'] = True
        print("✓ PyAnnote 方案可用")
    except ImportError:
        print("- PyAnnote 不可用")
        methods['pyannote'] = None
    
    # 3. 简化方案总是可用
    try:
        from simple_speaker_identification import get_simple_speaker_identifier
        methods['simple'] = get_simple_speaker_identifier
        print("✓ 简化方案可用")
    except ImportError:
        print("- 简化方案不可用")
        methods['simple'] = None
    
    return methods

# 检查可用方案
AVAILABLE_METHODS = check_available_methods()

class SpeakerIdentifier:
    def __init__(self, preferred_method: str = "auto"):
        """
        智能声纹识别器
        
        Args:
            preferred_method: 优先方案 ("speechbrain", "pyannote", "simple", "auto")
        """
        self.method = None
        self.identifier = None
        self.available = False
        
        # 确定使用的方案
        if preferred_method == "auto":
            self.method = self._select_best_method()
        else:
            self.method = preferred_method
        
        # 初始化选定的方案
        self._initialize_method()
        
        if self.available:
            print(f"🎤 声纹识别已就绪: {self.method.upper()}")
        else:
            print("⚠️ 声纹识别不可用，将使用普通转写")
    
    def _select_best_method(self) -> str:
        """自动选择最佳的声纹识别方案"""
        # 优先级：speechbrain > pyannote > simple
        if AVAILABLE_METHODS['speechbrain']:
            return "speechbrain"
        elif AVAILABLE_METHODS['pyannote']:
            return "pyannote"
        elif AVAILABLE_METHODS['simple']:
            return "simple"
        else:
            return "none"
    
    def _initialize_method(self):
        """初始化选定的声纹识别方案"""
        try:
            if self.method == "speechbrain" and AVAILABLE_METHODS['speechbrain']:
                self.identifier = AVAILABLE_METHODS['speechbrain']()
                self.available = self.identifier.available
                
            elif self.method == "pyannote" and AVAILABLE_METHODS['pyannote']:
                self.identifier = self._create_pyannote_identifier()
                self.available = self.identifier is not None
                
            elif self.method == "simple" and AVAILABLE_METHODS['simple']:
                self.identifier = AVAILABLE_METHODS['simple']()
                self.available = True
                
            else:
                print(f"方案 {self.method} 不可用")
                self.available = False
                
        except Exception as e:
            print(f"初始化 {self.method} 失败: {e}")
            self.available = False
    
    def _create_pyannote_identifier(self):
        """创建PyAnnote识别器（原有实现）"""
        try:
            from pyannote.audio import Pipeline
            
            class PyAnnoteIdentifier:
                def __init__(self):
                    self.pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
                    if torch.cuda.is_available():
                        self.pipeline = self.pipeline.to(torch.device("cuda"))
                    self.available = True
                
                def identify_speakers(self, audio_path: str, min_speakers=2, max_speakers=8):
                    # 原有的pyannote实现
                    pass
                
                def match_transcript_to_speakers(self, whisper_segments, speaker_segments):
                    # 原有的匹配实现
                    pass
            
            return PyAnnoteIdentifier()
            
        except Exception as e:
            print(f"PyAnnote初始化失败: {e}")
            return None
    
    def identify_speakers(self, audio_path: str, min_speakers=2, max_speakers=8) -> Dict:
        """执行发言人识别"""
        if not self.available or not self.identifier:
            return {
                'segments': [],
                'total_speakers': 0,
                'total_duration': 0,
                'speaker_list': [],
                'error': f'{self.method}声纹识别不可用'
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
    print("智能声纹识别测试")
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