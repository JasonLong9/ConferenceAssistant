#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于SpeechBrain的声纹识别实现
使用开源免费的ECAPA-TDNN模型进行发言人识别
"""

import torch
import torchaudio
import numpy as np
from typing import List, Dict, Tuple, Optional
import os
from dataclasses import dataclass
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# 尝试导入SpeechBrain
try:
    from speechbrain.pretrained import EncoderClassifier
    SPEECHBRAIN_AVAILABLE = True
    print("SpeechBrain 可用")
except ImportError:
    SPEECHBRAIN_AVAILABLE = False
    print("警告: SpeechBrain 未安装，请运行: pip install speechbrain")

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

class SpeechBrainSpeakerIdentifier:
    def __init__(self, model_name="speechbrain/spkrec-ecapa-voxceleb"):
        """
        初始化基于SpeechBrain的声纹识别器
        """
        self.model_name = model_name
        self.classifier = None
        self.available = False
        
        if not SPEECHBRAIN_AVAILABLE:
            print("错误: SpeechBrain 库未安装")
            return
        
        print(f"加载SpeechBrain模型: {model_name}")
        
        if self._load_model():
            print("✓ SpeechBrain声纹识别模型加载成功!")
            self.available = True
        else:
            print("✗ SpeechBrain声纹识别模型加载失败")
            self.available = False
    
    def _load_model(self) -> bool:
        """加载SpeechBrain模型"""
        try:
            # 设置缓存目录
            cache_dir = "./speechbrain_cache"
            os.makedirs(cache_dir, exist_ok=True)
            
            # 加载预训练的说话人识别模型
            self.classifier = EncoderClassifier.from_hparams(
                source=self.model_name,
                savedir=cache_dir,
                run_opts={"device": "cuda" if torch.cuda.is_available() else "cpu"}
            )
            
            print(f"模型已加载到: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
            return True
            
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False
    
    def _extract_speaker_embeddings(self, audio_path: str, segment_length: float = 3.0) -> List[Dict]:
        """
        提取音频的声纹特征
        """
        if not self.available:
            return []
        
        try:
            # 加载音频
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # 确保单声道
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # 重采样到16kHz（如果需要）
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000
            
            # 分段提取特征
            segment_samples = int(segment_length * sample_rate)
            hop_samples = int(segment_length * sample_rate * 0.5)  # 50% 重叠
            
            embeddings = []
            audio_length = waveform.shape[1]
            
            for start_sample in range(0, audio_length, hop_samples):
                end_sample = min(start_sample + segment_samples, audio_length)
                
                if end_sample - start_sample < sample_rate:  # 至少1秒
                    continue
                
                segment = waveform[:, start_sample:end_sample]
                
                # 提取声纹特征
                embedding = self.classifier.encode_batch(segment)
                
                embeddings.append({
                    'start_time': start_sample / sample_rate,
                    'end_time': end_sample / sample_rate,
                    'embedding': embedding.squeeze().cpu().numpy(),
                    'duration': (end_sample - start_sample) / sample_rate
                })
            
            print(f"提取了 {len(embeddings)} 个音频段的声纹特征")
            return embeddings
            
        except Exception as e:
            print(f"声纹特征提取失败: {e}")
            return []
    
    def _cluster_speakers(self, embeddings: List[Dict], min_speakers: int = 2, max_speakers: int = 8) -> List[Dict]:
        """
        基于声纹特征聚类识别发言人
        """
        if len(embeddings) == 0:
            return []
        
        try:
            from sklearn.cluster import AgglomerativeClustering
            from sklearn.metrics.pairwise import cosine_similarity
            
            # 提取特征向量
            features = np.array([emb['embedding'] for emb in embeddings])
            
            # 计算相似度矩阵
            similarity_matrix = cosine_similarity(features)
            distance_matrix = 1 - similarity_matrix
            
            # 自动确定最佳聚类数
            best_n_clusters = self._find_optimal_clusters(
                distance_matrix, min_speakers, max_speakers
            )
            
            # 执行聚类
            clustering = AgglomerativeClustering(
                n_clusters=best_n_clusters,
                metric='precomputed',
                linkage='average'
            )
            
            labels = clustering.fit_predict(distance_matrix)
            
            # 生成发言人段落
            speaker_segments = []
            for i, (embedding, label) in enumerate(zip(embeddings, labels)):
                speaker_segments.append({
                    'speaker': f'Speaker_{label}',
                    'start': embedding['start_time'],
                    'end': embedding['end_time'],
                    'duration': embedding['duration'],
                    'confidence': float(np.max(similarity_matrix[i]))
                })
            
            # 合并连续的相同发言人段落
            merged_segments = self._merge_consecutive_segments(speaker_segments)
            
            return merged_segments
            
        except ImportError:
            print("错误: 需要安装 scikit-learn: pip install scikit-learn")
            return self._simple_clustering(embeddings, min_speakers)
        except Exception as e:
            print(f"聚类失败: {e}")
            return self._simple_clustering(embeddings, min_speakers)
    
    def _find_optimal_clusters(self, distance_matrix: np.ndarray, min_clusters: int, max_clusters: int) -> int:
        """自动找到最佳聚类数"""
        try:
            from sklearn.cluster import AgglomerativeClustering
            
            best_score = -1
            best_n = min_clusters
            
            for n in range(min_clusters, min(max_clusters + 1, len(distance_matrix))):
                clustering = AgglomerativeClustering(
                    n_clusters=n,
                    metric='precomputed',
                    linkage='average'
                )
                labels = clustering.fit_predict(distance_matrix)
                
                # 计算轮廓系数作为评估标准
                try:
                    from sklearn.metrics import silhouette_score
                    score = silhouette_score(distance_matrix, labels, metric='precomputed')
                    
                    if score > best_score:
                        best_score = score
                        best_n = n
                except:
                    pass
            
            return best_n
            
        except Exception:
            return min_clusters
    
    def _simple_clustering(self, embeddings: List[Dict], min_speakers: int) -> List[Dict]:
        """简化的聚类方法（不依赖scikit-learn）"""
        # 基于时间的简单分配
        speaker_segments = []
        segment_duration = 10.0  # 10秒一个发言人段落
        
        for i, embedding in enumerate(embeddings):
            speaker_id = f'Speaker_{i % min_speakers}'
            speaker_segments.append({
                'speaker': speaker_id,
                'start': embedding['start_time'],
                'end': embedding['end_time'],
                'duration': embedding['duration'],
                'confidence': 0.7
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
            # 如果是同一个发言人且时间连续（间隔<1秒）
            if (current['speaker'] == seg['speaker'] and 
                seg['start'] - current['end'] < 1.0):
                # 合并段落
                current['end'] = seg['end']
                current['duration'] = current['end'] - current['start']
            else:
                # 添加当前段落，开始新段落
                merged.append(current)
                current = seg.copy()
        
        # 添加最后一个段落
        merged.append(current)
        
        return merged
    
    def identify_speakers(self, audio_path: str, min_speakers=2, max_speakers=8) -> Dict:
        """
        执行发言人分离
        """
        if not self.available:
            return {
                'segments': [],
                'total_speakers': 0,
                'total_duration': 0,
                'speaker_list': [],
                'error': 'SpeechBrain模型不可用'
            }
        
        print(f"开始SpeechBrain声纹识别: {audio_path}")
        
        try:
            # 1. 提取声纹特征
            embeddings = self._extract_speaker_embeddings(audio_path)
            
            if not embeddings:
                return {
                    'segments': [],
                    'total_speakers': 0,
                    'total_duration': 0,
                    'speaker_list': [],
                    'error': '音频特征提取失败'
                }
            
            # 2. 聚类识别发言人
            speaker_segments = self._cluster_speakers(embeddings, min_speakers, max_speakers)
            
            # 3. 统计信息
            unique_speakers = list(set(seg['speaker'] for seg in speaker_segments))
            total_duration = max(seg['end'] for seg in speaker_segments) if speaker_segments else 0
            
            print(f"SpeechBrain识别完成: {len(unique_speakers)} 个发言人")
            for speaker in unique_speakers:
                segments_count = sum(1 for seg in speaker_segments if seg['speaker'] == speaker)
                total_time = sum(seg['duration'] for seg in speaker_segments if seg['speaker'] == speaker)
                print(f"  {speaker}: {segments_count} 个段落, {total_time:.1f}s 总时长")
            
            return {
                'segments': speaker_segments,
                'total_speakers': len(unique_speakers),
                'total_duration': total_duration,
                'speaker_list': unique_speakers
            }
            
        except Exception as e:
            print(f"SpeechBrain声纹识别失败: {e}")
            return {
                'segments': [],
                'total_speakers': 0,
                'total_duration': 0,
                'speaker_list': [],
                'error': f'识别过程失败: {str(e)}'
            }
    
    def match_transcript_to_speakers(self, whisper_segments: List[Dict], speaker_segments: List[Dict]) -> List[SpeakerSegment]:
        """
        将转写文本与发言人段落匹配
        """
        matched_segments = []
        
        for wseg in whisper_segments:
            # 找到时间重叠最大的发言人
            best_match = "Speaker_0"
            best_overlap = 0
            
            for sseg in speaker_segments:
                overlap = self._calculate_overlap(
                    wseg['start'], wseg['end'],
                    sseg['start'], sseg['end']
                )
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = sseg['speaker']
            
            matched_segments.append(SpeakerSegment(
                speaker_id=best_match,
                start_time=wseg['start'],
                end_time=wseg['end'],
                text=wseg['text'],
                confidence=best_overlap
            ))
        
        return matched_segments
    
    def _calculate_overlap(self, start1: float, end1: float, start2: float, end2: float) -> float:
        """计算两个时间段的重叠度"""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        if overlap_start < overlap_end:
            duration1 = end1 - start1
            if duration1 > 0:
                return (overlap_end - overlap_start) / duration1
        return 0.0

def test_speechbrain_speaker_identification(audio_path: str):
    """
    测试SpeechBrain声纹识别
    """
    print("="*60)
    print("测试 SpeechBrain 声纹识别")
    print("="*60)
    
    if not os.path.exists(audio_path):
        print(f"错误: 音频文件不存在: {audio_path}")
        return
    
    try:
        # 创建识别器
        identifier = SpeechBrainSpeakerIdentifier()
        
        if not identifier.available:
            print("SpeechBrain模型不可用")
            return
        
        # 执行识别
        result = identifier.identify_speakers(audio_path, min_speakers=2, max_speakers=6)
        
        print(f"\n识别结果:")
        print(f"发言人数量: {result['total_speakers']}")
        print(f"音频总长: {result['total_duration']:.2f}秒")
        
        if result.get('error'):
            print(f"错误: {result['error']}")
        else:
            print(f"\n发言人段落:")
            for i, seg in enumerate(result['segments'][:10]):  # 显示前10个
                print(f"  {i+1}. {seg['speaker']}: {seg['start']:.1f}s-{seg['end']:.1f}s "
                      f"({seg['duration']:.1f}s, 置信度:{seg.get('confidence', 0):.2f})")
            
            if len(result['segments']) > 10:
                print(f"  ... 还有 {len(result['segments']) - 10} 个段落")
    
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "test_file/河北人设仲裁需求会-1.mp3"
    test_speechbrain_speaker_identification(audio_file)