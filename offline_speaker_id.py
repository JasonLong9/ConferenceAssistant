#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完全离线的声纹识别实现
基于音频特征分析，不需要外部模型下载
使用PyTorch内置功能进行音频处理和特征提取
"""

import torch
import torchaudio
import numpy as np
from typing import List, Dict, Tuple, Optional
import os
from dataclasses import dataclass
import math

@dataclass
class SpeakerSegment:
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float

class OfflineSpeakerIdentifier:
    def __init__(self):
        """
        离线声纹识别器
        基于音频频谱特征进行发言人分离
        """
        self.available = True
        self.sample_rate = 16000
        self.window_size = 2.0  # 2秒窗口
        self.hop_size = 1.0     # 1秒跳跃
        
        print("离线声纹识别器已初始化")
        print("- 基于频谱特征分析")
        print("- 无需外部模型下载")
        print("- 完全本地化处理")
    
    def _load_audio(self, audio_path: str) -> Tuple[torch.Tensor, int]:
        """加载音频文件"""
        try:
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # 转换为单声道
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # 重采样到16kHz
            if sample_rate != self.sample_rate:
                resampler = torchaudio.transforms.Resample(sample_rate, self.sample_rate)
                waveform = resampler(waveform)
            
            return waveform.squeeze(), self.sample_rate
            
        except Exception as e:
            print(f"音频加载失败: {e}")
            raise e
    
    def _extract_features(self, waveform: torch.Tensor) -> np.ndarray:
        """
        提取音频特征：MFCC + 频谱质心 + 过零率
        """
        # MFCC特征
        mfcc_transform = torchaudio.transforms.MFCC(
            sample_rate=self.sample_rate,
            n_mfcc=13,
            melkwargs={"n_fft": 1024, "hop_length": 512, "n_mels": 40}
        )
        mfcc = mfcc_transform(waveform.unsqueeze(0)).squeeze(0)
        mfcc_mean = torch.mean(mfcc, dim=1)  # 取时间维度的平均值
        mfcc_std = torch.std(mfcc, dim=1)    # 取时间维度的标准差
        
        # 频谱质心 (Spectral Centroid)
        spectral_centroid = self._compute_spectral_centroid(waveform)
        
        # 过零率 (Zero Crossing Rate)
        zcr = self._compute_zero_crossing_rate(waveform)
        
        # 基频估计 (简化版本)
        f0 = self._estimate_f0(waveform)
        
        # 合并所有特征
        features = torch.cat([
            mfcc_mean,      # 13维
            mfcc_std,       # 13维  
            torch.tensor([spectral_centroid]),  # 1维
            torch.tensor([zcr]),                # 1维
            torch.tensor([f0])                  # 1维
        ])
        
        return features.numpy()  # 总共29维特征
    
    def _compute_spectral_centroid(self, waveform: torch.Tensor) -> float:
        """计算频谱质心"""
        try:
            # 计算短时傅里叶变换
            stft = torch.stft(
                waveform, 
                n_fft=1024, 
                hop_length=512, 
                return_complex=True
            )
            
            # 计算功率谱
            power_spectrum = torch.abs(stft) ** 2
            
            # 频率轴
            freqs = torch.linspace(0, self.sample_rate / 2, power_spectrum.shape[0])
            
            # 计算频谱质心
            numerator = torch.sum(freqs.unsqueeze(1) * power_spectrum, dim=0)
            denominator = torch.sum(power_spectrum, dim=0)
            
            # 避免除零
            denominator = torch.where(denominator == 0, torch.ones_like(denominator), denominator)
            centroid = numerator / denominator
            
            return float(torch.mean(centroid))
            
        except Exception:
            return 1000.0  # 默认值
    
    def _compute_zero_crossing_rate(self, waveform: torch.Tensor) -> float:
        """计算过零率"""
        try:
            # 计算符号变化
            signs = torch.sign(waveform)
            sign_changes = torch.abs(torch.diff(signs))
            zcr = torch.sum(sign_changes) / (2 * len(waveform))
            return float(zcr)
        except Exception:
            return 0.1  # 默认值
    
    def _estimate_f0(self, waveform: torch.Tensor) -> float:
        """基频估计（简化版）"""
        try:
            # 使用自相关方法估计基频
            correlation = torch.fft.irfft(torch.abs(torch.fft.rfft(waveform)) ** 2)
            
            # 寻找第一个峰值（排除零延迟）
            min_period = int(self.sample_rate / 400)  # 400Hz对应的周期
            max_period = int(self.sample_rate / 80)   # 80Hz对应的周期
            
            correlation = correlation[min_period:max_period]
            if len(correlation) > 0:
                peak_index = torch.argmax(correlation) + min_period
                f0 = self.sample_rate / peak_index
                return float(f0)
            else:
                return 150.0  # 默认基频
                
        except Exception:
            return 150.0  # 默认基频
    
    def _segment_audio(self, waveform: torch.Tensor) -> List[Dict]:
        """将音频分段并提取特征"""
        segments = []
        
        window_samples = int(self.window_size * self.sample_rate)
        hop_samples = int(self.hop_size * self.sample_rate)
        
        for start_sample in range(0, len(waveform), hop_samples):
            end_sample = min(start_sample + window_samples, len(waveform))
            
            if end_sample - start_sample < self.sample_rate * 0.5:  # 至少0.5秒
                break
            
            segment_waveform = waveform[start_sample:end_sample]
            
            # 只处理有足够能量的段落
            energy = torch.mean(segment_waveform ** 2)
            if energy < 1e-6:  # 静音段落跳过
                continue
            
            features = self._extract_features(segment_waveform)
            
            segments.append({
                'start_time': start_sample / self.sample_rate,
                'end_time': end_sample / self.sample_rate,
                'duration': (end_sample - start_sample) / self.sample_rate,
                'features': features,
                'energy': float(energy)
            })
        
        print(f"分段完成: {len(segments)} 个有效段落")
        return segments
    
    def _cluster_speakers(self, segments: List[Dict], min_speakers: int = 2, max_speakers: int = 8) -> List[Dict]:
        """基于特征的发言人聚类"""
        if len(segments) == 0:
            return []
        
        try:
            # 使用简化的K-means聚类
            features = np.array([seg['features'] for seg in segments])
            
            # 标准化特征
            features_mean = np.mean(features, axis=0)
            features_std = np.std(features, axis=0)
            features_std = np.where(features_std == 0, 1, features_std)  # 避免除零
            features_normalized = (features - features_mean) / features_std
            
            # 自适应确定聚类数
            # 基于音频长度和段落数量智能确定聚类数
            segment_count = len(segments)
            
            if segment_count < 10:
                # 段落太少，使用最小值
                n_clusters = min_speakers
            elif segment_count < 50:
                # 中等数量段落，保守估计
                n_clusters = min(max_speakers, max(min_speakers, segment_count // 5))
            else:
                # 大量段落，基于经验值
                estimated_clusters = min(max_speakers, max(min_speakers, segment_count // 10))
                n_clusters = max(min_speakers, min(estimated_clusters, max_speakers))
            
            # 确保聚类数在合理范围内
            n_clusters = max(min_speakers, min(n_clusters, min(max_speakers, segment_count)))
            
            print(f"自动确定聚类数: {n_clusters} (基于{segment_count}个段落)")
            
            # 简化的K-means聚类
            labels = self._simple_kmeans(features_normalized, n_clusters)
            
            # 生成发言人段落
            speaker_segments = []
            for i, (segment, label) in enumerate(zip(segments, labels)):
                speaker_segments.append({
                    'speaker': f'Speaker_{label}',
                    'start': segment['start_time'],
                    'end': segment['end_time'],
                    'duration': segment['duration'],
                    'confidence': 0.8 - 0.1 * (label % 3)  # 简单的置信度计算
                })
            
            # 合并连续段落
            merged = self._merge_consecutive_segments(speaker_segments)
            
            return merged
            
        except Exception as e:
            print(f"聚类失败: {e}")
            return self._fallback_clustering(segments, min_speakers)
    
    def _simple_kmeans(self, features: np.ndarray, k: int, max_iters: int = 20) -> List[int]:
        """简化的K-means聚类实现"""
        n_samples, n_features = features.shape
        
        print(f"开始K-means聚类: {n_samples}个样本, {k}个聚类, {n_features}维特征")
        
        if k > n_samples:
            print(f"警告: 聚类数({k})大于样本数({n_samples})，调整为{n_samples}")
            k = n_samples
        
        if k <= 0:
            print(f"错误: 聚类数无效({k})，使用默认值2")
            k = 2
        
        try:
            # 初始化聚类中心
            np.random.seed(42)  # 固定随机种子
            centroids = features[np.random.choice(n_samples, k, replace=False)]
        
            for iter_count in range(max_iters):
                # 分配样本到最近的聚类中心
                distances = np.sqrt(((features - centroids[:, np.newaxis])**2).sum(axis=2))
                labels = np.argmin(distances, axis=0)
                
                # 更新聚类中心
                new_centroids = np.array([features[labels == i].mean(axis=0) if np.sum(labels == i) > 0 
                                         else centroids[i] for i in range(k)])
                
                # 检查收敛
                if np.allclose(centroids, new_centroids, rtol=1e-4):
                    print(f"K-means在第{iter_count+1}次迭代后收敛")
                    break
                    
                centroids = new_centroids
            
            # 验证聚类结果
            unique_labels = np.unique(labels)
            print(f"K-means完成，实际产生{len(unique_labels)}个聚类")
            
            return labels.tolist()
            
        except Exception as e:
            print(f"K-means聚类失败: {e}")
            # 返回简单的轮询分配
            return [i % k for i in range(n_samples)]
    
    def _fallback_clustering(self, segments: List[Dict], min_speakers: int) -> List[Dict]:
        """后备聚类方案：基于时间和能量"""
        speaker_segments = []
        
        for i, segment in enumerate(segments):
            # 基于时间和能量的简单分配
            speaker_id = f'Speaker_{i % min_speakers}'
            
            speaker_segments.append({
                'speaker': speaker_id,
                'start': segment['start_time'],
                'end': segment['end_time'],
                'duration': segment['duration'],
                'confidence': 0.6
            })
        
        return speaker_segments
    
    def _merge_consecutive_segments(self, segments: List[Dict]) -> List[Dict]:
        """合并连续的相同发言人段落"""
        if not segments:
            return []
        
        # 按时间排序
        segments.sort(key=lambda x: x['start'])
        
        merged = []
        current = segments[0].copy()
        
        for seg in segments[1:]:
            # 如果是同一发言人且时间接近（间隔<2秒）
            if (current['speaker'] == seg['speaker'] and 
                seg['start'] - current['end'] < 2.0):
                # 合并段落
                current['end'] = seg['end']
                current['duration'] = current['end'] - current['start']
            else:
                merged.append(current)
                current = seg.copy()
        
        merged.append(current)
        return merged
    
    def identify_speakers(self, audio_path: str, min_speakers: int = 2, max_speakers: int = 8) -> Dict:
        """
        执行离线声纹识别
        """
        print(f"开始离线声纹识别: {audio_path}")
        
        try:
            # 1. 加载音频
            waveform, sample_rate = self._load_audio(audio_path)
            total_duration = len(waveform) / sample_rate
            print(f"音频时长: {total_duration:.2f}秒")
            
            # 2. 分段和特征提取
            segments = self._segment_audio(waveform)
            
            if not segments:
                return {
                    'segments': [],
                    'total_speakers': 0,
                    'total_duration': total_duration,
                    'speaker_list': [],
                    'error': '未检测到有效音频段落'
                }
            
            # 3. 发言人聚类
            speaker_segments = self._cluster_speakers(segments, min_speakers, max_speakers)
            
            # 4. 统计信息
            unique_speakers = list(set(seg['speaker'] for seg in speaker_segments))
            
            print(f"离线识别完成: {len(unique_speakers)} 个发言人")
            for speaker in unique_speakers:
                count = sum(1 for seg in speaker_segments if seg['speaker'] == speaker)
                duration = sum(seg['duration'] for seg in speaker_segments if seg['speaker'] == speaker)
                print(f"  {speaker}: {count} 段, {duration:.1f}s")
            
            return {
                'segments': speaker_segments,
                'total_speakers': len(unique_speakers),
                'total_duration': total_duration,
                'speaker_list': unique_speakers
            }
            
        except Exception as e:
            print(f"离线声纹识别失败: {e}")
            return {
                'segments': [],
                'total_speakers': 0,
                'total_duration': 0,
                'speaker_list': [],
                'error': f'识别失败: {str(e)}'
            }
    
    def match_transcript_to_speakers(self, whisper_segments: List[Dict], speaker_segments: List[Dict]) -> List[SpeakerSegment]:
        """匹配转写文本与发言人"""
        print(f"开始匹配文本与发言人: {len(whisper_segments)}个转写片段, {len(speaker_segments)}个发言人片段")
        
        if not whisper_segments:
            print("警告: 没有转写片段")
            return []
        
        if not speaker_segments:
            print("警告: 没有发言人片段，所有文本将分配给Speaker_0")
            return [SpeakerSegment(
                speaker_id="Speaker_0",
                start_time=wseg['start'],
                end_time=wseg['end'],
                text=wseg['text'],
                confidence=0.0
            ) for wseg in whisper_segments]
        
        matched = []
        successful_matches = 0
        
        for i, wseg in enumerate(whisper_segments):
            # 找到时间重叠最大的发言人段落
            best_speaker = "Speaker_0"
            best_overlap = 0
            
            for sseg in speaker_segments:
                overlap = self._calculate_overlap(
                    wseg['start'], wseg['end'],
                    sseg['start'], sseg['end']
                )
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = sseg['speaker']
            
            if best_overlap > 0.1:  # 至少10%重叠才算成功匹配
                successful_matches += 1
            
            matched.append(SpeakerSegment(
                speaker_id=best_speaker,
                start_time=wseg['start'],
                end_time=wseg['end'],
                text=wseg['text'],
                confidence=best_overlap
            ))
        
        match_rate = successful_matches / len(whisper_segments) * 100
        print(f"文本匹配完成: {successful_matches}/{len(whisper_segments)} 片段成功匹配 ({match_rate:.1f}%)")
        
        return matched
    
    def _calculate_overlap(self, start1: float, end1: float, start2: float, end2: float) -> float:
        """计算时间重叠度"""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        if overlap_start < overlap_end:
            duration1 = end1 - start1
            if duration1 > 0:
                return (overlap_end - overlap_start) / duration1
        return 0.0

def test_offline_speaker_identification(audio_path: str):
    """测试离线声纹识别"""
    print("="*60)
    print("离线声纹识别测试")
    print("="*60)
    
    if not os.path.exists(audio_path):
        print(f"错误: 音频文件不存在: {audio_path}")
        return
    
    try:
        # 创建识别器
        identifier = OfflineSpeakerIdentifier()
        
        # 执行识别
        result = identifier.identify_speakers(audio_path, min_speakers=2, max_speakers=6)
        
        print(f"\n识别结果:")
        print(f"发言人数量: {result['total_speakers']}")
        print(f"音频总长: {result['total_duration']:.2f}秒")
        
        if result.get('error'):
            print(f"错误: {result['error']}")
        else:
            print(f"\n发言人段落 (前15个):")
            for i, seg in enumerate(result['segments'][:15]):
                conf = seg.get('confidence', 0)
                print(f"{i+1:2d}. {seg['speaker']}: {seg['start']:.1f}s-{seg['end']:.1f}s "
                      f"({seg['duration']:.1f}s) 置信度:{conf:.2f}")
            
            if len(result['segments']) > 15:
                print(f"... 还有 {len(result['segments']) - 15} 个段落")
        
        return result
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import sys
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "test_file/河北人设仲裁需求会-1.mp3"
    test_offline_speaker_identification(audio_file)