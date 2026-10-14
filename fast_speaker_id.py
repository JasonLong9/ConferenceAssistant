#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速发言人识别模块
主要优化：
1. 基于音量和频率的简单算法，避免复杂特征提取
2. 语音活动检测优化
3. 内存使用最小化
4. 处理速度优化
"""

import torch
import torchaudio
import numpy as np
from typing import List, Dict, Tuple, Optional
import os
from dataclasses import dataclass
from pydub import AudioSegment
import time

@dataclass
class FastSpeakerSegment:
    speaker_id: str
    start_time: float
    end_time: float
    confidence: float = 1.0

class FastSpeakerIdentifier:
    """
    快速发言人识别器
    基于简化算法，优先考虑处理速度
    """
    
    def __init__(self):
        self.available = True
        self.min_segment_duration = 1.0  # 最小段长度（秒）
        self.window_size = 0.5  # 分析窗口（秒）
        self.overlap = 0.25  # 窗口重叠（秒）
        
        print("快速发言人识别器已初始化")
        print("- 基于音量和基频分析")
        print("- 优化处理速度")
        print("- 最小内存占用")
    
    def identify_speakers(self, audio_path: str, min_speakers: int = 2, max_speakers: int = 8) -> Dict:
        """
        快速发言人识别主函数
        """
        try:
            start_time = time.time()
            
            # 1. 加载和预处理音频
            audio_data, sample_rate = self._load_audio_fast(audio_path)
            duration = len(audio_data) / sample_rate
            
            print(f"音频时长: {duration:.1f}秒，采样率: {sample_rate}Hz")
            
            # 2. 语音活动检测（VAD）
            voice_segments = self._detect_voice_activity(audio_data, sample_rate)
            
            if not voice_segments:
                print("未检测到语音活动")
                return {'total_speakers': 0, 'segments': []}
            
            print(f"检测到 {len(voice_segments)} 个语音段")
            
            # 3. 基于音量和基频的简单分类
            speaker_segments = self._classify_speakers(
                audio_data, voice_segments, sample_rate, min_speakers, max_speakers
            )
            
            # 4. 后处理：合并相邻的相同发言人段
            merged_segments = self._merge_adjacent_segments(speaker_segments)
            
            processing_time = time.time() - start_time
            print(f"发言人识别完成，用时: {processing_time:.2f}秒")
            print(f"识别出 {len(set(seg.speaker_id for seg in merged_segments))} 个发言人")
            
            # 转换为API格式
            api_segments = []
            for seg in merged_segments:
                api_segments.append({
                    'start': seg.start_time,
                    'end': seg.end_time,
                    'speaker_id': seg.speaker_id
                })
            
            unique_speakers = len(set(seg.speaker_id for seg in merged_segments))
            
            return {
                'total_speakers': unique_speakers,
                'segments': api_segments
            }
            
        except Exception as e:
            print(f"发言人识别失败: {e}")
            import traceback
            traceback.print_exc()
            return {'total_speakers': 0, 'segments': []}
    
    def _load_audio_fast(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        快速加载音频文件
        """
        try:
            # 使用pydub快速加载（支持更多格式）
            audio = AudioSegment.from_file(audio_path)
            
            # 转换为单声道
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # 降采样到8kHz以提高处理速度
            target_rate = 8000
            if audio.frame_rate != target_rate:
                audio = audio.set_frame_rate(target_rate)
            
            # 转换为numpy数组
            audio_data = np.array(audio.get_array_of_samples(), dtype=np.float32)
            audio_data = audio_data / np.max(np.abs(audio_data))  # 归一化
            
            return audio_data, target_rate
            
        except Exception as e:
            print(f"音频加载失败: {e}")
            # 尝试torchaudio加载
            waveform, sample_rate = torchaudio.load(audio_path)
            audio_data = waveform.numpy().flatten()
            return audio_data, sample_rate
    
    def _detect_voice_activity(self, audio_data: np.ndarray, sample_rate: int) -> List[Tuple[float, float]]:
        """
        语音活动检测（VAD）
        基于能量阈值的简单方法
        """
        window_samples = int(self.window_size * sample_rate)
        hop_samples = int((self.window_size - self.overlap) * sample_rate)
        
        # 计算短时能量
        energies = []
        times = []
        
        for i in range(0, len(audio_data) - window_samples, hop_samples):
            window = audio_data[i:i + window_samples]
            energy = np.sum(window ** 2) / len(window)  # 平均能量
            energies.append(energy)
            times.append(i / sample_rate)
        
        if not energies:
            return []
        
        energies = np.array(energies)
        
        # 动态阈值：使用能量分布的百分位数
        threshold = np.percentile(energies, 20)  # 20%分位数作为阈值
        
        # 找到语音段
        voice_segments = []
        in_voice = False
        start_time = 0
        
        for i, (time_pos, energy) in enumerate(zip(times, energies)):
            if energy > threshold and not in_voice:
                # 语音开始
                in_voice = True
                start_time = time_pos
            elif energy <= threshold and in_voice:
                # 语音结束
                in_voice = False
                end_time = time_pos + self.window_size
                
                # 过滤太短的段
                if end_time - start_time >= self.min_segment_duration:
                    voice_segments.append((start_time, end_time))
        
        # 处理最后一个段
        if in_voice and times:
            end_time = times[-1] + self.window_size
            if end_time - start_time >= self.min_segment_duration:
                voice_segments.append((start_time, end_time))
        
        return voice_segments
    
    def _classify_speakers(self, audio_data: np.ndarray, voice_segments: List[Tuple[float, float]], 
                          sample_rate: int, min_speakers: int, max_speakers: int) -> List[FastSpeakerSegment]:
        """
        基于音频特征进行说话人分类
        使用简化特征：平均音量、基频估计
        """
        if not voice_segments:
            return []
        
        # 提取每个语音段的特征
        segment_features = []
        
        for start_time, end_time in voice_segments:
            start_sample = int(start_time * sample_rate)
            end_sample = int(end_time * sample_rate)
            segment_audio = audio_data[start_sample:end_sample]
            
            if len(segment_audio) == 0:
                continue
            
            # 特征1: 平均音量（RMS）
            rms = np.sqrt(np.mean(segment_audio ** 2))
            
            # 特征2: 基频估计（简化版）
            fundamental_freq = self._estimate_fundamental_frequency(segment_audio, sample_rate)
            
            # 特征3: 频谱质心（简化）
            spectral_centroid = self._estimate_spectral_centroid(segment_audio, sample_rate)
            
            segment_features.append({
                'start_time': start_time,
                'end_time': end_time,
                'rms': rms,
                'f0': fundamental_freq,
                'spectral_centroid': spectral_centroid
            })
        
        if not segment_features:
            return []
        
        # 简单的K-means聚类（基于特征相似性）
        speaker_assignments = self._simple_clustering(
            segment_features, min_speakers, max_speakers
        )
        
        # 创建发言人段
        speaker_segments = []
        for i, assignment in enumerate(speaker_assignments):
            feature = segment_features[i]
            speaker_id = f"发言人{assignment + 1}"
            
            segment = FastSpeakerSegment(
                speaker_id=speaker_id,
                start_time=feature['start_time'],
                end_time=feature['end_time'],
                confidence=0.8  # 固定置信度
            )
            speaker_segments.append(segment)
        
        return speaker_segments
    
    def _estimate_fundamental_frequency(self, audio_segment: np.ndarray, sample_rate: int) -> float:
        """
        估计基频（F0）- 简化版本
        """
        try:
            # 使用自相关函数估计基频
            autocorr = np.correlate(audio_segment, audio_segment, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # 寻找第二个峰值（基频周期）
            # 限制搜索范围在合理的基频范围内 (80-400 Hz)
            min_period = int(sample_rate / 400)  # 400 Hz
            max_period = int(sample_rate / 80)   # 80 Hz
            
            if max_period >= len(autocorr):
                return 150.0  # 默认值
            
            search_autocorr = autocorr[min_period:max_period]
            if len(search_autocorr) == 0:
                return 150.0
            
            peak_index = np.argmax(search_autocorr) + min_period
            f0 = sample_rate / peak_index
            
            # 限制在合理范围内
            return np.clip(f0, 80, 400)
            
        except:
            return 150.0  # 默认基频
    
    def _estimate_spectral_centroid(self, audio_segment: np.ndarray, sample_rate: int) -> float:
        """
        估计频谱质心 - 简化版本
        """
        try:
            # 简单的FFT分析
            fft = np.fft.rfft(audio_segment)
            magnitude = np.abs(fft)
            freqs = np.fft.rfftfreq(len(audio_segment), 1/sample_rate)
            
            if np.sum(magnitude) == 0:
                return 1000.0
            
            # 计算频谱质心
            centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
            return centroid
            
        except:
            return 1000.0  # 默认值
    
    def _simple_clustering(self, segment_features: List[Dict], min_speakers: int, max_speakers: int) -> List[int]:
        """
        简单的特征聚类
        基于RMS音量和基频的二维聚类
        """
        if not segment_features:
            return []
        
        # 提取特征向量
        features = []
        for feat in segment_features:
            # 归一化特征
            rms_norm = feat['rms'] / max(f['rms'] for f in segment_features)
            f0_norm = feat['f0'] / 400.0  # 归一化到0-1
            features.append([rms_norm, f0_norm])
        
        features = np.array(features)
        
        # 如果段数少于最小发言人数，每段分配不同发言人
        if len(features) <= min_speakers:
            return list(range(len(features)))
        
        # 简单的K-means聚类（手写版本，避免依赖sklearn）
        n_clusters = min(max_speakers, max(min_speakers, len(features) // 3))
        
        # 随机初始化聚类中心
        np.random.seed(42)
        centroids = features[np.random.choice(len(features), n_clusters, replace=False)]
        
        # 迭代更新
        for _ in range(10):  # 最多10次迭代
            # 分配到最近的聚类中心
            distances = np.sqrt(((features[:, np.newaxis, :] - centroids) ** 2).sum(axis=2))
            assignments = np.argmin(distances, axis=1)
            
            # 更新聚类中心
            new_centroids = []
            for i in range(n_clusters):
                cluster_points = features[assignments == i]
                if len(cluster_points) > 0:
                    new_centroids.append(np.mean(cluster_points, axis=0))
                else:
                    new_centroids.append(centroids[i])  # 保持原中心
            
            centroids = np.array(new_centroids)
        
        return assignments.tolist()
    
    def _merge_adjacent_segments(self, segments: List[FastSpeakerSegment]) -> List[FastSpeakerSegment]:
        """
        合并相邻的相同发言人段
        """
        if not segments:
            return []
        
        # 按时间排序
        segments.sort(key=lambda x: x.start_time)
        
        merged = [segments[0]]
        
        for current in segments[1:]:
            last = merged[-1]
            
            # 如果是相同发言人且时间相邻（允许小间隔）
            if (current.speaker_id == last.speaker_id and 
                current.start_time - last.end_time <= 2.0):  # 2秒间隔内合并
                
                # 合并段
                merged[-1] = FastSpeakerSegment(
                    speaker_id=last.speaker_id,
                    start_time=last.start_time,
                    end_time=current.end_time,
                    confidence=min(last.confidence, current.confidence)
                )
            else:
                merged.append(current)
        
        return merged

# 向后兼容
def create_fast_speaker_identifier():
    """创建快速发言人识别器实例"""
    return FastSpeakerIdentifier()

if __name__ == "__main__":
    # 测试代码
    identifier = FastSpeakerIdentifier()
    print("快速发言人识别器测试就绪")