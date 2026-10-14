#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
带发言人识别的会议助手
整合发言人分离功能和语音转文字功能
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 导入本地发言人分离模块
from speaker_diarization_local import SimpleSpeakerDiarization

# 尝试导入原有的会议处理模块
try:
    from core import MeetingProcessor
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    print("警告: 原有core模块未找到，将使用简化版本")

# 尝试导入语音识别模块
try:
    import speech_recognition as sr
    import pydub
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("提示: speech_recognition未安装，转写功能将受限")

class ConferenceAssistantWithSpeakerID:
    """带发言人识别的会议助手"""
    
    def __init__(self):
        """初始化"""
        self.speaker_diarizer = SimpleSpeakerDiarization()
        
        if CORE_AVAILABLE:
            self.meeting_processor = MeetingProcessor()
        else:
            self.meeting_processor = None
        
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
    
    def process_audio_with_speaker_id(self, audio_path, output_dir="output", meeting_name=None):
        """处理音频文件，包含发言人识别和转写"""
        print("=" * 80)
        print("带发言人识别的会议音频处理")
        print("=" * 80)
        
        if not os.path.exists(audio_path):
            print(f"错误: 音频文件不存在 - {audio_path}")
            return None
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成会议名称
        if not meeting_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            meeting_name = f"会议_{timestamp}"
        
        # 1. 发言人分离
        print("\n第一步: 发言人分离")
        print("-" * 40)
        diarization_results = self.speaker_diarizer.diarize(audio_path)
        
        if not diarization_results:
            print("发言人分离失败")
            return None
        
        # 2. 如果有原有的处理器，使用它进行转写
        transcript_text = None
        if self.meeting_processor and CORE_AVAILABLE:
            print("\n第二步: 语音转写 (使用原有处理器)")
            print("-" * 40)
            try:
                # 这里需要根据原有processor的接口调整
                result = self.meeting_processor.process_audio(audio_path)
                if result and 'transcript' in result:
                    transcript_text = result['transcript']
                    print("语音转写完成")
                else:
                    print("语音转写失败或结果为空")
            except Exception as e:
                print(f"使用原有处理器转写失败: {e}")
        
        # 3. 生成带发言人标识的转写文本
        print("\n第三步: 生成带发言人标识的转写")
        print("-" * 40)
        
        speaker_transcript = self.generate_speaker_transcript(
            diarization_results, 
            transcript_text,
            audio_path
        )
        
        # 4. 保存结果
        print("\n第四步: 保存结果")
        print("-" * 40)
        
        results = {
            'meeting_name': meeting_name,
            'audio_path': audio_path,
            'processing_time': time.time(),
            'speaker_count': len(set(segment['speaker'] for segment in diarization_results)),
            'diarization_results': diarization_results,
            'transcript': speaker_transcript,
            'output_files': []
        }
        
        # 保存发言人分离结果
        diarization_file = os.path.join(output_dir, f"{meeting_name}_发言人分离.json")
        with open(diarization_file, 'w', encoding='utf-8') as f:
            json.dump(diarization_results, f, ensure_ascii=False, indent=2)
        results['output_files'].append(diarization_file)
        
        # 保存带发言人标识的转写
        transcript_file = os.path.join(output_dir, f"{meeting_name}_转写_带发言人.md")
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(f"# {meeting_name} - 会议转写 (带发言人识别)\n\n")
            f.write(f"**处理时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**音频文件:** {os.path.basename(audio_path)}\n\n")
            f.write(f"**识别发言人数:** {results['speaker_count']}\n\n")
            f.write("## 发言人统计\n\n")
            
            # 统计每个发言人的信息
            speaker_stats = {}
            total_duration = 0
            for segment in diarization_results:
                speaker = segment['speaker']
                duration = segment['duration']
                total_duration += duration
                
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {'segments': 0, 'total_time': 0}
                speaker_stats[speaker]['segments'] += 1
                speaker_stats[speaker]['total_time'] += duration
            
            for speaker, stats in speaker_stats.items():
                percentage = (stats['total_time'] / total_duration) * 100
                f.write(f"- **{speaker}:** {stats['segments']}个发言片段, "
                       f"总时长 {stats['total_time']:.1f}秒 ({percentage:.1f}%)\n")
            
            f.write(f"\n## 转写内容\n\n")
            f.write(speaker_transcript)
        
        results['output_files'].append(transcript_file)
        results['transcript_file'] = transcript_file
        
        # 保存处理结果摘要
        summary_file = os.path.join(output_dir, f"{meeting_name}_处理结果.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            # 为了JSON序列化，移除不能序列化的对象
            summary_results = results.copy()
            summary_results['processing_time'] = datetime.now().isoformat()
            json.dump(summary_results, f, ensure_ascii=False, indent=2)
        results['output_files'].append(summary_file)
        
        print(f"\n处理完成!")
        print(f"输出目录: {output_dir}")
        print(f"生成文件: {len(results['output_files'])} 个")
        for file_path in results['output_files']:
            print(f"  - {os.path.basename(file_path)}")
        
        return results
    
    def generate_speaker_transcript(self, diarization_results, original_transcript=None, audio_path=None):
        """生成带发言人标识的转写文本"""
        
        if original_transcript:
            # 如果有原始转写，尝试将其与发言人信息结合
            print("结合原始转写和发言人信息...")
            
            # 简单的时间对齐方法
            transcript_lines = []
            for segment in diarization_results:
                speaker = segment['speaker']
                start_time = segment['start']
                end_time = segment['end']
                duration = segment['duration']
                
                # 这里是简化版本，实际应用中需要更复杂的对齐算法
                transcript_lines.append(
                    f"**{speaker}** ({start_time:.1f}s - {end_time:.1f}s):\n"
                    f"> [此处应有该时间段的转写内容，时长{duration:.1f}秒]\n\n"
                )
        else:
            # 如果没有原始转写，只生成发言人时间轴
            print("生成发言人时间轴...")
            
            transcript_lines = []
            transcript_lines.append("## 发言人时间轴\n\n")
            transcript_lines.append("由于没有可用的语音转写功能，以下仅显示发言人切换时间点：\n\n")
            
            for i, segment in enumerate(diarization_results):
                speaker = segment['speaker']
                start_time = segment['start']
                end_time = segment['end']
                duration = segment['duration']
                
                transcript_lines.append(
                    f"{i+1}. **{speaker}** "
                    f"({start_time:.1f}s - {end_time:.1f}s, 时长{duration:.1f}秒)\n"
                )
                
                if i < len(diarization_results) - 1:
                    next_segment = diarization_results[i + 1]
                    if next_segment['speaker'] != speaker:
                        transcript_lines.append(f"   → 发言人切换到 {next_segment['speaker']}\n")
                
                transcript_lines.append("\n")
        
        return ''.join(transcript_lines)
    
    def analyze_meeting_dynamics(self, results):
        """分析会议动态"""
        if not results or not results.get('diarization_results'):
            return None
        
        diarization_results = results['diarization_results']
        
        analysis = {
            'total_speakers': len(set(segment['speaker'] for segment in diarization_results)),
            'total_duration': sum(segment['duration'] for segment in diarization_results),
            'speaker_switches': 0,
            'average_turn_length': 0,
            'speaker_participation': {}
        }
        
        # 计算发言人切换次数
        for i in range(1, len(diarization_results)):
            if diarization_results[i]['speaker'] != diarization_results[i-1]['speaker']:
                analysis['speaker_switches'] += 1
        
        # 计算平均发言时长
        if diarization_results:
            analysis['average_turn_length'] = analysis['total_duration'] / len(diarization_results)
        
        # 计算每个发言人的参与度
        for segment in diarization_results:
            speaker = segment['speaker']
            duration = segment['duration']
            
            if speaker not in analysis['speaker_participation']:
                analysis['speaker_participation'][speaker] = {
                    'total_time': 0,
                    'segments': 0,
                    'average_segment_length': 0
                }
            
            analysis['speaker_participation'][speaker]['total_time'] += duration
            analysis['speaker_participation'][speaker]['segments'] += 1
        
        # 计算每个发言人的平均发言长度
        for speaker, data in analysis['speaker_participation'].items():
            if data['segments'] > 0:
                data['average_segment_length'] = data['total_time'] / data['segments']
                data['participation_percentage'] = (data['total_time'] / analysis['total_duration']) * 100
        
        return analysis

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='带发言人识别的会议音频处理')
    parser.add_argument('audio_file', help='输入音频文件路径')
    parser.add_argument('--output', '-o', default='output', help='输出目录 (默认: output)')
    parser.add_argument('--name', '-n', help='会议名称')
    parser.add_argument('--analyze', '-a', action='store_true', help='进行会议动态分析')
    
    args = parser.parse_args()
    
    # 检查音频文件
    if not os.path.exists(args.audio_file):
        print(f"错误: 音频文件不存在 - {args.audio_file}")
        return 1
    
    # 创建处理器
    assistant = ConferenceAssistantWithSpeakerID()
    
    # 处理音频
    results = assistant.process_audio_with_speaker_id(
        audio_path=args.audio_file,
        output_dir=args.output,
        meeting_name=args.name
    )
    
    if not results:
        print("处理失败")
        return 1
    
    # 如果需要分析
    if args.analyze:
        print("\n" + "=" * 80)
        print("会议动态分析")
        print("=" * 80)
        
        analysis = assistant.analyze_meeting_dynamics(results)
        if analysis:
            print(f"总发言人数: {analysis['total_speakers']}")
            print(f"总会议时长: {analysis['total_duration']:.1f}秒")
            print(f"发言人切换次数: {analysis['speaker_switches']}")
            print(f"平均发言时长: {analysis['average_turn_length']:.1f}秒")
            
            print("\n发言人参与度分析:")
            for speaker, data in analysis['speaker_participation'].items():
                print(f"  {speaker}:")
                print(f"    发言时长: {data['total_time']:.1f}秒 ({data['participation_percentage']:.1f}%)")
                print(f"    发言片段: {data['segments']}个")
                print(f"    平均片段长度: {data['average_segment_length']:.1f}秒")
    
    print(f"\n处理完成! 结果保存在: {args.output}")
    return 0

if __name__ == "__main__":
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