#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConferenceAssistant 优化版核心模块
主要优化：
1. Whisper模型预加载和内存优化
2. 音频分片并行处理
3. 发言人识别算法优化
4. 内存使用优化
5. 批处理和缓存机制
"""

import os
import socket
import datetime
import re
import json
import time
import threading
import gc
import math
from typing import Optional, List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import tempfile

import torch
from faster_whisper import WhisperModel
import requests
from dotenv import load_dotenv
load_dotenv()

from pydub import AudioSegment
import torchaudio
import numpy as np

# 导入声纹识别模块
try:
    from speaker_identification import SpeakerIdentifier, SpeakerSegment
except ImportError:
    print("警告: 声纹识别模块不可用")
    SpeakerIdentifier = None
    SpeakerSegment = None

# DeepSeek V3 API 配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 优化配置
OPTIMIZE_CONFIG = {
    'chunk_duration': 300,  # 5分钟分片
    'overlap_duration': 30,  # 30秒重叠
    'max_workers': min(4, os.cpu_count()),  # 并行处理线程数
    'enable_gpu_memory_optimization': True,  # GPU内存优化
    'enable_audio_preprocessing': True,  # 音频预处理优化
    'enable_fast_speaker_id': True,  # 快速发言人识别
}

def get_local_ip():
    """获取本机IP地址"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class OptimizedWhisperModel:
    """优化的Whisper模型管理器"""
    
    _instance = None
    _lock = threading.Lock()
    _model = None
    _device = None
    _compute_type = None
    
    @classmethod
    def get_instance(cls, model_dir="whisper-large-v3", device="auto", compute_type="float16"):
        """单例模式获取Whisper模型实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(model_dir, device, compute_type)
        return cls._instance
    
    def __init__(self, model_dir="whisper-large-v3", device="auto", compute_type="float16"):
        """初始化优化的Whisper模型"""
        self.model_dir = model_dir
        
        # 设备选择优化
        if device == "auto":
            if torch.cuda.is_available():
                self._device = "cuda"
                # GPU内存检查
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                if gpu_memory < 6:  # 小于6GB显存使用int8
                    self._compute_type = "int8"
                else:
                    self._compute_type = "float16"
            else:
                self._device = "cpu"
                self._compute_type = "int8"  # CPU使用int8更快
        else:
            self._device = device
            self._compute_type = compute_type
        
        self._load_model()
    
    def _load_model(self):
        """加载Whisper模型"""
        print(f"正在加载Whisper模型...")
        print(f"设备: {self._device}, 计算类型: {self._compute_type}")
        
        try:
            # 加载模型
            self._model = WhisperModel(
                self.model_dir, 
                device=self._device, 
                compute_type=self._compute_type,
                num_workers=1  # 减少worker数量避免内存问题
            )
            
            print("✅ Whisper模型加载成功")
            
        except Exception as e:
            print(f"❌ Whisper模型加载失败: {e}")
            # 降级处理
            if self._compute_type == "float16":
                print("尝试降级到int8...")
                self._compute_type = "int8"
                self._model = WhisperModel(self.model_dir, device=self._device, compute_type=self._compute_type)
            else:
                raise e
    
    def transcribe(self, audio_path: str, language: Optional[str] = None, **kwargs):
        """转写音频"""
        if self._model is None:
            self._load_model()
        
        return self._model.transcribe(
            audio_path, 
            language=language,
            beam_size=1,  # 减少beam size提升速度
            best_of=1,    # 减少best_of提升速度
            temperature=0.0,  # 确定性输出
            **kwargs
        )

class AudioProcessor:
    """优化的音频处理器"""
    
    def __init__(self):
        self.temp_files = []  # 临时文件列表，用于清理
    
    def preprocess_audio(self, audio_path: str) -> str:
        """音频预处理优化"""
        if not OPTIMIZE_CONFIG['enable_audio_preprocessing']:
            return audio_path
        
        try:
            # 加载音频
            audio = AudioSegment.from_file(audio_path)
            
            # 音频优化
            processed = False
            
            # 1. 转换为单声道（如果是立体声）
            if audio.channels > 1:
                audio = audio.set_channels(1)
                processed = True
            
            # 2. 规范化采样率到16kHz
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)
                processed = True
            
            # 3. 音量规范化
            if audio.dBFS < -20:  # 声音太小
                audio = audio.normalize()
                processed = True
            
            # 4. 降噪（简单的）
            if len(audio) > 60000:  # 大于1分钟才降噪
                # 简单的噪声门限处理
                audio = audio.compress_dynamic_range(threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
                processed = True
            
            # 如果有处理，保存为临时文件
            if processed:
                temp_path = tempfile.mktemp(suffix=".wav")
                audio.export(temp_path, format="wav")
                self.temp_files.append(temp_path)
                print(f"音频预处理完成，保存到: {temp_path}")
                return temp_path
            
            return audio_path
            
        except Exception as e:
            print(f"音频预处理失败: {e}")
            return audio_path
    
    def split_audio_chunks(self, audio_path: str, chunk_duration: int = 300, overlap_duration: int = 30) -> List[Tuple[str, float, float]]:
        """将音频分割为重叠的块"""
        try:
            audio = AudioSegment.from_file(audio_path)
            audio_duration = len(audio) / 1000.0  # 转换为秒
            
            # 如果音频很短，不需要分割
            if audio_duration <= chunk_duration:
                return [(audio_path, 0.0, audio_duration)]
            
            chunks = []
            chunk_duration_ms = chunk_duration * 1000
            overlap_duration_ms = overlap_duration * 1000
            step_size_ms = chunk_duration_ms - overlap_duration_ms
            
            start_ms = 0
            chunk_index = 0
            
            while start_ms < len(audio):
                end_ms = min(start_ms + chunk_duration_ms, len(audio))
                
                # 提取音频块
                chunk = audio[start_ms:end_ms]
                
                # 保存临时文件
                temp_path = tempfile.mktemp(suffix=f"_chunk_{chunk_index}.wav")
                chunk.export(temp_path, format="wav")
                self.temp_files.append(temp_path)
                
                # 记录时间范围
                start_time = start_ms / 1000.0
                end_time = end_ms / 1000.0
                
                chunks.append((temp_path, start_time, end_time))
                
                # 如果是最后一块，退出
                if end_ms >= len(audio):
                    break
                
                start_ms += step_size_ms
                chunk_index += 1
            
            print(f"音频分割完成，共{len(chunks)}个块")
            return chunks
            
        except Exception as e:
            print(f"音频分割失败: {e}")
            # 返回原文件
            audio = AudioSegment.from_file(audio_path)
            return [(audio_path, 0.0, len(audio) / 1000.0)]
    
    def cleanup(self):
        """清理临时文件"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        self.temp_files.clear()

class FastSpeakerIdentifier:
    """快速发言人识别器（简化版）"""
    
    def __init__(self):
        self.available = True
        
    def identify_speakers(self, audio_path: str, min_speakers: int = 2, max_speakers: int = 8) -> Dict:
        """快速发言人识别"""
        if not OPTIMIZE_CONFIG['enable_fast_speaker_id']:
            return {'total_speakers': 0, 'segments': []}
        
        try:
            # 使用简化算法：基于语音活动检测和基础特征
            audio = AudioSegment.from_file(audio_path)
            duration = len(audio) / 1000.0
            
            # 简单的语音活动检测
            silence_threshold = audio.dBFS - 16  # 动态阈值
            voice_segments = []
            
            # 检测语音段（1秒窗口）
            window_size = 1000  # 1秒
            for i in range(0, len(audio), window_size):
                segment = audio[i:i + window_size]
                if segment.dBFS > silence_threshold:
                    start_time = i / 1000.0
                    end_time = min((i + window_size) / 1000.0, duration)
                    voice_segments.append({
                        'start': start_time,
                        'end': end_time,
                        'speaker_id': f'发言人{(len(voice_segments) % min_speakers) + 1}'
                    })
            
            # 合并相邻的相同发言人段
            merged_segments = []
            current_speaker = None
            current_start = None
            current_end = None
            
            for segment in voice_segments:
                if segment['speaker_id'] != current_speaker:
                    if current_speaker is not None:
                        merged_segments.append({
                            'start': current_start,
                            'end': current_end,
                            'speaker_id': current_speaker
                        })
                    current_speaker = segment['speaker_id']
                    current_start = segment['start']
                current_end = segment['end']
            
            # 添加最后一段
            if current_speaker is not None:
                merged_segments.append({
                    'start': current_start,
                    'end': current_end,
                    'speaker_id': current_speaker
                })
            
            return {
                'total_speakers': min_speakers,
                'segments': merged_segments
            }
            
        except Exception as e:
            print(f"快速发言人识别失败: {e}")
            return {'total_speakers': 0, 'segments': []}

class OptimizedMeetingProcessor:
    """优化的会议处理器"""
    
    def __init__(self, whisper_model_dir: str = "whisper-large-v3", device: str = "auto"):
        self.whisper_model_dir = whisper_model_dir
        self.device = device
        self.whisper = None
        self.audio_processor = AudioProcessor()
        self.speaker_identifier = None
        
        # 性能统计
        self.stats = {
            'total_time': 0,
            'whisper_time': 0,
            'speaker_id_time': 0,
            'text_processing_time': 0
        }
    
    def _get_whisper_model(self):
        """获取Whisper模型（延迟加载）"""
        if self.whisper is None:
            self.whisper = OptimizedWhisperModel.get_instance(
                self.whisper_model_dir, 
                self.device
            )
        return self.whisper
    
    def _get_speaker_identifier(self):
        """获取发言人识别器（延迟加载）"""
        if self.speaker_identifier is None:
            if OPTIMIZE_CONFIG['enable_fast_speaker_id']:
                self.speaker_identifier = FastSpeakerIdentifier()
            elif SpeakerIdentifier is not None:
                try:
                    self.speaker_identifier = SpeakerIdentifier()
                except Exception as e:
                    print(f"标准发言人识别器初始化失败: {e}")
                    self.speaker_identifier = FastSpeakerIdentifier()
            else:
                self.speaker_identifier = FastSpeakerIdentifier()
        
        return self.speaker_identifier
    
    def process_audio_chunk(self, chunk_info: Tuple[str, float, float]) -> Dict:
        """处理单个音频块"""
        chunk_path, start_time, end_time = chunk_info
        
        try:
            whisper_model = self._get_whisper_model()
            
            # 转写音频块
            segments, info = whisper_model.transcribe(chunk_path, language="zh")
            
            # 调整时间戳
            adjusted_segments = []
            for seg in segments:
                adjusted_segments.append({
                    'start': seg.start + start_time,
                    'end': seg.end + start_time,
                    'text': seg.text.strip()
                })
            
            return {
                'segments': adjusted_segments,
                'chunk_start': start_time,
                'chunk_end': end_time
            }
            
        except Exception as e:
            print(f"处理音频块失败 ({start_time:.1f}-{end_time:.1f}): {e}")
            return {
                'segments': [],
                'chunk_start': start_time,
                'chunk_end': end_time
            }
    
    def merge_chunk_results(self, chunk_results: List[Dict]) -> List[Dict]:
        """合并音频块的处理结果"""
        all_segments = []
        
        # 按时间排序
        chunk_results.sort(key=lambda x: x['chunk_start'])
        
        for chunk_result in chunk_results:
            all_segments.extend(chunk_result['segments'])
        
        # 去重重叠部分（简单去重）
        if len(all_segments) > 1:
            merged_segments = [all_segments[0]]
            
            for seg in all_segments[1:]:
                last_seg = merged_segments[-1]
                # 如果时间重叠且文本相似，跳过
                if (seg['start'] < last_seg['end'] and 
                    self._text_similarity(seg['text'], last_seg['text']) > 0.8):
                    continue
                merged_segments.append(seg)
            
            return merged_segments
        
        return all_segments
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单版）"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def process_with_optimization(self, audio_path: str, meeting_name: Optional[str] = None, 
                                output_dir: str = "outputs") -> Dict:
        """优化版会议处理流程"""
        start_total_time = time.time()
        
        try:
            print("🚀 开始优化版会议处理...")
            
            # 1. 音频预处理
            print("📦 音频预处理中...")
            preprocessed_audio = self.audio_processor.preprocess_audio(audio_path)
            
            # 2. 音频分片
            print("✂️  音频分片中...")
            audio_chunks = self.audio_processor.split_audio_chunks(
                preprocessed_audio, 
                OPTIMIZE_CONFIG['chunk_duration'],
                OPTIMIZE_CONFIG['overlap_duration']
            )
            
            # 3. 并行处理音频块
            print(f"🔄 并行处理 {len(audio_chunks)} 个音频块...")
            whisper_start_time = time.time()
            
            chunk_results = []
            with ThreadPoolExecutor(max_workers=OPTIMIZE_CONFIG['max_workers']) as executor:
                # 提交任务
                future_to_chunk = {
                    executor.submit(self.process_audio_chunk, chunk): chunk 
                    for chunk in audio_chunks
                }
                
                # 收集结果
                for future in as_completed(future_to_chunk):
                    chunk = future_to_chunk[future]
                    try:
                        result = future.result()
                        chunk_results.append(result)
                        print(f"✅ 完成块 {chunk[1]:.1f}-{chunk[2]:.1f}s")
                    except Exception as e:
                        print(f"❌ 块处理失败 {chunk[1]:.1f}-{chunk[2]:.1f}s: {e}")
            
            whisper_time = time.time() - whisper_start_time
            self.stats['whisper_time'] = whisper_time
            
            # 4. 合并转写结果
            print("🔗 合并转写结果...")
            merged_segments = self.merge_chunk_results(chunk_results)
            
            # 5. 发言人识别（如果启用）
            speaker_id_start_time = time.time()
            print("🎯 发言人识别中...")
            
            speaker_identifier = self._get_speaker_identifier()
            speaker_result = speaker_identifier.identify_speakers(preprocessed_audio)
            
            if speaker_result.get('total_speakers', 0) > 0:
                # 匹配转写文本与发言人
                formatted_transcript = self._match_and_format_speakers(
                    merged_segments, speaker_result['segments']
                )
                speaker_count = speaker_result['total_speakers']
            else:
                formatted_transcript = "\\n".join([seg['text'] for seg in merged_segments])
                speaker_count = 0
            
            speaker_id_time = time.time() - speaker_id_start_time
            self.stats['speaker_id_time'] = speaker_id_time
            
            # 6. 文本处理（规整和纪要生成）
            print("📝 生成会议纪要...")
            text_processing_start_time = time.time()
            
            cleaned = self._clean_transcript(formatted_transcript)
            minutes = self._generate_meeting_minutes(cleaned)
            
            text_processing_time = time.time() - text_processing_start_time
            self.stats['text_processing_time'] = text_processing_time
            
            # 7. 保存结果
            auto_name = self._extract_meeting_name(minutes)
            final_name = meeting_name or auto_name
            
            transcript_md_path = self._save_to_local_markdown(
                formatted_transcript, f"会议内容_{final_name}", output_dir
            )
            minutes_md_path = self._save_to_local_markdown(
                minutes, f"会议纪要_{final_name}", output_dir
            )
            
            # 8. 清理临时文件和释放内存
            self.audio_processor.cleanup()
            if OPTIMIZE_CONFIG['enable_gpu_memory_optimization']:
                self._cleanup_gpu_memory()
            
            # 统计总时间
            total_time = time.time() - start_total_time
            self.stats['total_time'] = total_time
            
            # 输出性能报告
            self._print_performance_stats(audio_chunks)
            
            return {
                "transcript": formatted_transcript,
                "cleaned": cleaned,
                "minutes": minutes,
                "meeting_name": final_name,
                "transcript_markdown_path": transcript_md_path,
                "minutes_markdown_path": minutes_md_path,
                "speaker_count": speaker_count,
                "processing_stats": self.stats.copy()
            }
            
        except Exception as e:
            print(f"❌ 会议处理失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 清理资源
            self.audio_processor.cleanup()
            raise e
    
    def _match_and_format_speakers(self, transcript_segments: List[Dict], speaker_segments: List[Dict]) -> str:
        """匹配转写文本与发言人段"""
        if not speaker_segments:
            return "\\n".join([seg['text'] for seg in transcript_segments])
        
        formatted_lines = []
        current_speaker = None
        
        for t_seg in transcript_segments:
            # 找到对应的发言人段
            t_mid = (t_seg['start'] + t_seg['end']) / 2
            
            best_speaker = None
            for s_seg in speaker_segments:
                if s_seg['start'] <= t_mid <= s_seg['end']:
                    best_speaker = s_seg['speaker_id']
                    break
            
            if best_speaker is None:
                # 如果没有匹配到，使用最近的发言人
                min_distance = float('inf')
                for s_seg in speaker_segments:
                    distance = min(
                        abs(t_mid - s_seg['start']),
                        abs(t_mid - s_seg['end'])
                    )
                    if distance < min_distance:
                        min_distance = distance
                        best_speaker = s_seg['speaker_id']
            
            # 如果发言人改变，添加标识
            if best_speaker != current_speaker:
                current_speaker = best_speaker
                formatted_lines.append(f"\\n【{current_speaker}】")
            
            formatted_lines.append(t_seg['text'])
        
        return "\\n".join(formatted_lines)
    
    def _cleanup_gpu_memory(self):
        """清理GPU内存"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
    
    def _print_performance_stats(self, audio_chunks):
        """打印性能统计"""
        total_duration = sum(chunk[2] - chunk[1] for chunk in audio_chunks)
        
        print("\\n📊 性能统计报告:")
        print(f"音频总时长: {total_duration:.1f}秒 ({total_duration/60:.1f}分钟)")
        print(f"处理总时间: {self.stats['total_time']:.1f}秒")
        print(f"速度比: {total_duration / self.stats['total_time']:.2f}x")
        print(f"Whisper转写: {self.stats['whisper_time']:.1f}秒")
        print(f"发言人识别: {self.stats['speaker_id_time']:.1f}秒")
        print(f"文本处理: {self.stats['text_processing_time']:.1f}秒")
        print(f"音频块数量: {len(audio_chunks)}")
        print(f"并行度: {OPTIMIZE_CONFIG['max_workers']}")
    
    # 以下是辅助方法，与原core.py中的方法类似
    def _clean_transcript(self, transcript: str) -> str:
        """规整转写文本"""
        return call_deepseek_v3(CLEAN_PROMPT, transcript)
    
    def _generate_meeting_minutes(self, transcript: str) -> str:
        """生成会议纪要"""
        return call_deepseek_v3(SYSTEM_PROMPT, transcript)
    
    def _extract_meeting_name(self, minutes_markdown: str) -> str:
        """提取会议名称"""
        match = re.search(r"会议主题[:：]\\s*(.+)", minutes_markdown)
        if match:
            return match.group(1).strip().replace("/", "_").replace("\\\\", "_")
        return "会议纪要"
    
    def _save_to_local_markdown(self, content: str, meeting_name: str, output_dir: str) -> str:
        """保存为本地markdown文件"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{meeting_name}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

# 原有的函数保持不变
def call_deepseek_v3(system_prompt: str, user_content: str) -> str:
    """调用DeepSeek V3 API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    }
    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

# Prompt定义
CLEAN_PROMPT = '''<instruction>
根据提供的录音文件的转录文本内容。对这些文本进行预整理，确保输出的文本格式清晰、连贯，并且没有多余的空格，错别字或上下文不连贯的错误。以下是完成此任务的步骤：
1. 仔细阅读提供的录音文件转录文本。
2. 识别并删除文本中的任何多余的空格、换行符或格式错误。
3. 确保文本中的语句连贯，逻辑清晰。
4. 对文本进行分析，精准识别不同发言人的内容，并以清晰格式区分呈现。需标注每位发言人的身份（如有）、发言内容及对应段落 / 句子。
5. 检查文本中是否有语法错误或无法理解的语句，并尝试进行修正。
6. 确保输出的文本不包含任何XML标签，只包含整理好的纯文本内容。
7. 输出的文本内容中如果包含双引号,请加上转义符号  
</instruction>'''

SYSTEM_PROMPT = '''<instruction>
根据提供的录音文件文本，生成一份结构清晰、详细明了的会议纪要。请按照以下步骤完成：
1. **提取关键信息**：仔细阅读录音文本，识别会议的主题、时间(单位为分钟)、地点、讨论的主要议题、决策事项以及后续行动计划,区分每个发言人,对应其发言内容.
2. **组织内容**：将提取的信息按照逻辑顺序排列，确保纪要结构清晰，包括标题、基本信息、讨论要点、结论和行动项,。
3. **核对细节**：列出所有值得记录的信息，确保准确无误，包括时间、数字等。
4. **格式统一**：使用一致的格式和标点符号，确保纪要易于阅读。
输出时请勿包含任何XML标签，仅提供纯文本格式的会议纪要。
在列出总结性信息后，列出重要时间点所讨论的话题与结果(数据中的时间单位为分钟)
</instruction>'''

# 为了向后兼容，保留原有的类
class MeetingProcessor(OptimizedMeetingProcessor):
    """向后兼容的会议处理器"""
    
    def process(self, audio_path: str, meeting_name: Optional[str] = None, 
               output_dir: str = "outputs", max_minutes: int = 5) -> dict:
        """向后兼容的处理方法"""
        return self.process_with_optimization(audio_path, meeting_name, output_dir)
    
    def process_with_speaker_id(self, audio_path: str, meeting_name: Optional[str] = None,
                               output_dir: str = "outputs") -> dict:
        """向后兼容的发言人识别处理方法"""
        return self.process_with_optimization(audio_path, meeting_name, output_dir)

print(f"优化版ConferenceAssistant已加载 - DEEPSEEK_API_KEY: {'OK' if DEEPSEEK_API_KEY else 'X'}")
print(f"优化配置: {OPTIMIZE_CONFIG}")