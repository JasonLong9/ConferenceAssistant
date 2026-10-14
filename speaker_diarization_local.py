#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地发言人分离实现
由于网络问题无法直接使用pyannote的在线模型，提供一个基于音频特征的简单实现
"""

import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

class SimpleSpeakerDiarization:
    """简单的发言人分离实现"""
    
    def __init__(self, n_mfcc=13, window_size=2.0, hop_size=1.0):
        """
        初始化
        :param n_mfcc: MFCC特征数量
        :param window_size: 窗口大小（秒）
        :param hop_size: 跳跃大小（秒）
        """
        self.n_mfcc = n_mfcc
        self.window_size = window_size
        self.hop_size = hop_size
        self.sr = 16000  # 采样率
    
    def load_audio(self, audio_path):
        """加载音频文件"""
        try:
            # 使用librosa加载音频
            audio, sr = librosa.load(audio_path, sr=self.sr)
            print(f"音频加载成功: 时长 {len(audio)/sr:.2f}秒, 采样率 {sr}Hz")
            return audio, sr
        except Exception as e:
            print(f"音频加载失败: {e}")
            return None, None
    
    def extract_features(self, audio, sr):
        """提取音频特征"""
        print("正在提取音频特征...")
        
        # 计算窗口和跳跃的帧数
        window_frames = int(self.window_size * sr)
        hop_frames = int(self.hop_size * sr)
        
        features = []
        timestamps = []
        
        # 滑动窗口提取特征
        for start in range(0, len(audio) - window_frames, hop_frames):
            end = start + window_frames
            window_audio = audio[start:end]
            
            # 计算时间戳
            timestamp = start / sr
            timestamps.append(timestamp)
            
            # 提取MFCC特征
            mfcc = librosa.feature.mfcc(y=window_audio, sr=sr, n_mfcc=self.n_mfcc)
            mfcc_mean = np.mean(mfcc, axis=1)
            
            # 提取其他特征
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=window_audio, sr=sr))
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=window_audio, sr=sr))
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(window_audio))
            
            # 组合特征
            feature_vector = np.concatenate([
                mfcc_mean,
                [spectral_centroid, spectral_rolloff, zero_crossing_rate]
            ])
            
            features.append(feature_vector)
        
        features = np.array(features)
        timestamps = np.array(timestamps)
        
        print(f"特征提取完成: {features.shape[0]}个窗口, 每个窗口{features.shape[1]}维特征")
        return features, timestamps
    
    def detect_speech_segments(self, audio, sr, min_speech_length=0.5):
        """检测语音段落"""
        print("正在检测语音活动...")
        
        # 计算能量
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.01 * sr)     # 10ms hop
        
        # 短时能量
        energy = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i+frame_length]
            energy.append(np.sum(frame ** 2))
        
        energy = np.array(energy)
        
        # 能量阈值（基于平均能量）
        energy_threshold = np.mean(energy) * 0.1
        
        # 检测语音段
        speech_frames = energy > energy_threshold
        
        # 转换为时间段
        frame_times = np.arange(len(speech_frames)) * hop_length / sr
        
        # 找到连续的语音段
        segments = []
        in_speech = False
        start_time = 0
        
        for i, is_speech in enumerate(speech_frames):
            if is_speech and not in_speech:
                # 语音开始
                start_time = frame_times[i]
                in_speech = True
            elif not is_speech and in_speech:
                # 语音结束
                end_time = frame_times[i]
                if end_time - start_time >= min_speech_length:
                    segments.append((start_time, end_time))
                in_speech = False
        
        # 处理最后一个段落
        if in_speech:
            end_time = frame_times[-1]
            if end_time - start_time >= min_speech_length:
                segments.append((start_time, end_time))
        
        print(f"检测到 {len(segments)} 个语音段落")
        return segments
    
    def cluster_speakers(self, features, n_speakers=None):
        """聚类分离发言人"""
        print("正在进行发言人聚类...")
        
        if len(features) < 2:
            print("特征数量不足，无法进行聚类")
            return np.zeros(len(features))
        
        # 标准化特征
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # 如果没有指定发言人数量，自动估计
        if n_speakers is None:
            # 使用肘部法则估计最佳聚类数
            max_clusters = min(10, len(features) // 3)
            if max_clusters < 2:
                n_speakers = 2
            else:
                inertias = []
                cluster_range = range(2, max_clusters + 1)
                
                for k in cluster_range:
                    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                    kmeans.fit(features_scaled)
                    inertias.append(kmeans.inertia_)
                
                # 简单的肘部检测
                if len(inertias) >= 2:
                    diffs = np.diff(inertias)
                    n_speakers = cluster_range[np.argmin(diffs[1:]) + 1] if len(diffs) > 1 else 2
                else:
                    n_speakers = 2
        
        print(f"使用 {n_speakers} 个聚类进行发言人分离")
        
        # 使用K-means聚类
        kmeans = KMeans(n_clusters=n_speakers, random_state=42, n_init=10)
        speaker_labels = kmeans.fit_predict(features_scaled)
        
        print(f"聚类完成，发现 {len(np.unique(speaker_labels))} 个发言人")
        return speaker_labels
    
    def smooth_labels(self, labels, timestamps, min_segment_length=1.0):
        """平滑标签，移除过短的片段"""
        print("正在平滑发言人标签...")
        
        smoothed_labels = labels.copy()
        
        # 查找连续的相同标签段落
        segments = []
        current_label = labels[0]
        start_idx = 0
        
        for i in range(1, len(labels)):
            if labels[i] != current_label:
                segments.append((start_idx, i-1, current_label))
                start_idx = i
                current_label = labels[i]
        
        # 添加最后一个段落
        segments.append((start_idx, len(labels)-1, current_label))
        
        # 移除过短的段落
        for start_idx, end_idx, label in segments:
            duration = timestamps[end_idx] - timestamps[start_idx]
            if duration < min_segment_length and len(segments) > 1:
                # 用前一个或后一个标签替换
                if start_idx > 0:
                    replacement_label = smoothed_labels[start_idx - 1]
                elif end_idx < len(labels) - 1:
                    replacement_label = smoothed_labels[end_idx + 1]
                else:
                    continue
                
                smoothed_labels[start_idx:end_idx+1] = replacement_label
        
        print("标签平滑完成")
        return smoothed_labels
    
    def diarize(self, audio_path, n_speakers=None):
        """执行发言人分离"""
        print("=" * 60)
        print("开始发言人分离")
        print("=" * 60)
        
        # 1. 加载音频
        audio, sr = self.load_audio(audio_path)
        if audio is None:
            return None
        
        # 2. 检测语音段落
        speech_segments = self.detect_speech_segments(audio, sr)
        
        # 3. 提取特征
        features, timestamps = self.extract_features(audio, sr)
        
        # 4. 聚类分离发言人
        speaker_labels = self.cluster_speakers(features, n_speakers)
        
        # 5. 平滑标签
        speaker_labels = self.smooth_labels(speaker_labels, timestamps)
        
        # 6. 生成结果
        results = []
        current_speaker = speaker_labels[0]
        start_time = timestamps[0]
        
        for i in range(1, len(speaker_labels)):
            if speaker_labels[i] != current_speaker:
                # 发言人变化
                end_time = timestamps[i-1] + self.window_size
                results.append({
                    'speaker': f'SPEAKER_{current_speaker:02d}',
                    'start': start_time,
                    'end': end_time,
                    'duration': end_time - start_time
                })
                
                current_speaker = speaker_labels[i]
                start_time = timestamps[i]
        
        # 添加最后一个段落
        end_time = timestamps[-1] + self.window_size
        results.append({
            'speaker': f'SPEAKER_{current_speaker:02d}',
            'start': start_time,
            'end': end_time,
            'duration': end_time - start_time
        })
        
        return results
    
    def print_results(self, results):
        """打印结果"""
        if not results:
            print("没有检测到发言人分离结果")
            return
        
        print("\n发言人分离结果:")
        print("-" * 60)
        
        speakers_stats = {}
        total_speech_time = 0
        
        for segment in results:
            speaker = segment['speaker']
            start = segment['start']
            end = segment['end']
            duration = segment['duration']
            total_speech_time += duration
            
            print(f"{speaker}: {start:.2f}s - {end:.2f}s (时长: {duration:.2f}s)")
            
            if speaker not in speakers_stats:
                speakers_stats[speaker] = {'segments': 0, 'total_time': 0}
            speakers_stats[speaker]['segments'] += 1
            speakers_stats[speaker]['total_time'] += duration
        
        print(f"\n统计信息:")
        print(f"检测到 {len(speakers_stats)} 个发言人")
        print(f"总发言时长: {total_speech_time:.2f}秒")
        
        for speaker, stats in speakers_stats.items():
            percentage = (stats['total_time'] / total_speech_time) * 100
            print(f"  {speaker}: {stats['segments']}个片段, "
                  f"总时长 {stats['total_time']:.2f}秒 ({percentage:.1f}%)")

def main():
    """主函数"""
    import sys
    import os
    
    print("本地发言人分离系统")
    print("=" * 60)
    
    # 获取音频文件路径
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
    else:
        # 检查默认测试文件
        test_audio_path = "test_file/河北人设仲裁需求会-1.mp3"
        if os.path.exists(test_audio_path):
            audio_path = test_audio_path
        else:
            audio_path = input("请输入音频文件路径: ").strip()
    
    if not audio_path or not os.path.exists(audio_path):
        print("音频文件不存在或路径无效")
        return 1
    
    # 创建发言人分离器
    diarizer = SimpleSpeakerDiarization(window_size=2.0, hop_size=1.0)
    
    # 执行分离
    results = diarizer.diarize(audio_path)
    
    if results:
        diarizer.print_results(results)
        print("\n发言人分离完成!")
        return 0
    else:
        print("发言人分离失败")
        return 1

if __name__ == "__main__":
    import os
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)