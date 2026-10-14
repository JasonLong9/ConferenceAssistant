import os
import socket
import datetime
import re
import json
from typing import Optional, List, Dict
import threading
import torch

from faster_whisper import WhisperModel
import requests
from dotenv import load_dotenv
load_dotenv()

from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor
import tempfile

# 导入声纹识别模块
try:
    from precision_speaker_id import PrecisionSpeakerIdentifier, SpeakerSegment
    IMPROVED_SPEAKER_ID_AVAILABLE = True
    print("[+] 精确版声纹识别可用")
except ImportError:
    try:
        from improved_speaker_id import ImprovedSpeakerIdentifier, SpeakerSegment
        IMPROVED_SPEAKER_ID_AVAILABLE = True
        print("[+] 改进版声纹识别可用")
    except ImportError:
        try:
            from speaker_identification import SpeakerIdentifier, SpeakerSegment
            IMPROVED_SPEAKER_ID_AVAILABLE = False
            print("[+] 标准声纹识别可用")
        except ImportError:
            IMPROVED_SPEAKER_ID_AVAILABLE = False
            print("[-] 声纹识别模块不可用")

def get_audio_duration(audio_path: str) -> float:
    """获取音频文件时长（秒）"""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0  # 转换为秒
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return 0

# DeepSeek V3 API 配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 自动获取本机内网 IP
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# 单例懒加载 WhisperModel - 优化版
class WhisperModelSingleton:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, model_dir="whisper-large-v3", device="auto"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print("Loading WhisperModel...（首次加载可能较慢）")
                    
                    # 智能设备和精度选择
                    if device == "auto":
                        if torch.cuda.is_available():
                            actual_device = "cuda"
                            # 检查GPU内存，小显存使用int8
                            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                            if gpu_memory < 6:
                                compute_type = "int8"
                                print(f"GPU内存较小({gpu_memory:.1f}GB)，使用int8精度")
                            else:
                                compute_type = "float16"
                        else:
                            actual_device = "cpu"
                            compute_type = "int8"  # CPU用int8更快
                            print("GPU不可用，使用CPU模式")
                    else:
                        actual_device = device
                        compute_type = "float16"
                    
                    print(f"设备: {actual_device}, 精度: {compute_type}")
                    cls._instance = WhisperModel(
                        model_dir, 
                        device=actual_device, 
                        compute_type=compute_type,
                        num_workers=1  # 减少worker避免内存问题
                    )
        return cls._instance

# 本地 faster-whisper 推理
class LocalWhisper:
    def __init__(self, model_dir: str = "whisper-large-v3", device: str = "auto"):
        self.model_dir = model_dir
        # 智能设备选择
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"自动选择设备: {self.device}")
        else:
            self.device = device

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        model = WhisperModelSingleton.get_instance(self.model_dir, self.device)
        print(f"Whisper推理设备: {self.device}")
        # 优化推理参数，提升速度
        segments, info = model.transcribe(
            audio_path, 
            language=language,
            beam_size=1,        # 减少beam size加速
            best_of=1,          # 减少候选数加速
            temperature=0.0,    # 确定性输出
            condition_on_previous_text=False,  # 减少依赖加速
            compression_ratio_threshold=2.4,   # 压缩比阈值
            log_prob_threshold=-1.0,           # 概率阈值
            no_speech_threshold=0.6            # 静音检测阈值
        )
        return "\n".join([seg.text for seg in segments])
    
    def transcribe_with_timestamps(self, audio_path: str, language: Optional[str] = None) -> List[Dict]:
        """
        返回带时间戳的转写结果 - 优化版
        """
        model = WhisperModelSingleton.get_instance(self.model_dir, self.device)
        print(f"Whisper推理设备: {self.device}")
        # 使用相同的优化参数
        segments, info = model.transcribe(
            audio_path, 
            language=language,
            beam_size=1,        # 减少beam size加速
            best_of=1,          # 减少候选数加速
            temperature=0.0,    # 确定性输出
            condition_on_previous_text=False,  # 减少依赖加速
            compression_ratio_threshold=2.4,   # 压缩比阈值
            log_prob_threshold=-1.0,           # 概率阈值
            no_speech_threshold=0.6            # 静音检测阈值
        )
        
        result_segments = []
        for seg in segments:
            result_segments.append({
                'start': seg.start,
                'end': seg.end,
                'text': seg.text.strip()  # 去除首尾空格
            })
        return result_segments

# 调用 DeepSeek V3 生成纪要
def call_deepseek_v3(system_prompt: str, user_content: str) -> str:
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

# 规整/区分发言人的大模型 prompt
CLEAN_PROMPT = '''<instruction>
根据提供的录音文件的转录文本内容进行预整理，确保输出的文本格式清晰、连贯。请严格按照以下要求完成：

1. **保持发言人格式**：严格保持原有的【Speaker_X】格式，不得修改发言人标识
2. **文本规整**：修正错别字、语法错误、专业词汇识别错误
3. **格式统一**：删除多余空格、确保换行格式一致
4. **内容优化**：优化语句连贯性，但不改变原意
5. **格式要求**：输出格式必须完全按照以下模板：

【Speaker_0】  
[规整后的发言内容]

【Speaker_1】  
[规整后的发言内容]

【Speaker_X】  
[规整后的发言内容]

**重要要求**：
- 必须保持每个发言人的【Speaker_X】标识格式不变
- 发言人之间用空行分隔
- 只修正文本内容，不改变发言人归属
- 专业词汇要准确识别和修正
- 输出纯文本，不包含XML标签
- 如有双引号，请加转义符号
</instruction>'''

# 规整转写文本，区分发言人

def clean_transcript(transcript: str) -> str:
    return call_deepseek_v3(CLEAN_PROMPT, transcript)

# 动态生成系统prompt，根据音频时长适配时间点摘要
def generate_dynamic_system_prompt(duration_minutes: int) -> str:
    # 根据时长动态生成时间段
    time_segments = []
    if duration_minutes <= 10:
        # 短会议：每2-3分钟一个时间段
        for i in range(0, duration_minutes, 3):
            end_time = min(i + 3, duration_minutes)
            time_segments.append(f"{i}-{end_time}分钟")
    elif duration_minutes <= 30:
        # 中等会议：每5分钟一个时间段
        for i in range(0, duration_minutes, 5):
            end_time = min(i + 5, duration_minutes)
            time_segments.append(f"{i}-{end_time}分钟")
    elif duration_minutes <= 60:
        # 长会议：每10分钟一个时间段
        for i in range(0, duration_minutes, 10):
            end_time = min(i + 10, duration_minutes)
            time_segments.append(f"{i}-{end_time}分钟")
    else:
        # 超长会议：每15分钟一个时间段
        for i in range(0, duration_minutes, 15):
            end_time = min(i + 15, duration_minutes)
            time_segments.append(f"{i}-{end_time}分钟")
    
    time_segments_str = "、".join(time_segments)
    # 处理时间段格式，避免f-string中的反斜杠问题
    newline_separator = "分钟：[对应时间段的主要讨论内容]\n- "
    formatted_time_segments = time_segments_str.replace("、", newline_separator) + "分钟：[对应时间段的主要讨论内容]"
    
    return f'''<instruction>
根据提供的录音文件文本，生成一份结构清晰、详细明了的会议纪要。请严格按照以下格式模板输出：

会议纪要：[提取的会议主题]

**一、会议基本信息**
- 会议主题：[从录音内容中提取的主要议题]
- 主要议题：[列出2-3个核心讨论点]
- 讨论重点：[重点关注的问题或决策]

**二、主要讨论内容与决策**

[按主题分类整理讨论内容，每个主题包含：]
1. **[主题名称]**
   - [具体讨论点1]
   - [具体讨论点2]
   - [达成的共识或决策]

2. **[主题名称]**
   - [具体讨论点1]
   - [具体讨论点2]
   - [达成的共识或决策]

[继续列出所有重要主题...]

**三、重要时间点讨论摘要（基于{duration_minutes}分钟音频内容分析）**
- {formatted_time_segments}

**四、备注**
- [会议过程中的重要说明或补充信息]
- [需要特别关注的事项]

**五、行动计划与责任分工**
- 短期行动：
  - [具体行动项1]
  - [具体行动项2]
- 中期计划：
  - [中期目标和计划]
- 责任分配：
  - [按发言人分配的具体责任]

请确保：
1. 严格按照上述格式输出
2. 从录音文本中准确提取信息
3. 保持内容的逻辑性和完整性
4. 不要包含任何XML标签，仅输出纯文本格式
</instruction>'''

def generate_meeting_minutes(transcript: str, duration_seconds: Optional[float] = None) -> str:
    if duration_seconds is not None:
        duration_minutes = max(1, int(duration_seconds / 60))  # 至少1分钟
        dynamic_prompt = generate_dynamic_system_prompt(duration_minutes)
        return call_deepseek_v3(dynamic_prompt, transcript)
    else:
        # 向后兼容：如果没有提供时长，使用固定的prompt
        fallback_prompt = generate_dynamic_system_prompt(30)  # 默认30分钟
        return call_deepseek_v3(fallback_prompt, transcript)

# 文件名清理函数
def clean_filename(filename: str) -> str:
    """清理文件名，移除Windows不支持的字符"""
    if not filename:
        return "会议纪要"
    
    # 替换Windows文件名中的非法字符
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
    clean_name = filename.strip()
    
    for char in invalid_chars:
        clean_name = clean_name.replace(char, '_')
    
    # 移除连续的下划线
    clean_name = re.sub(r'_+', '_', clean_name)
    # 移除首尾下划线
    clean_name = clean_name.strip('_')
    
    # 限制长度
    if len(clean_name) > 50:
        clean_name = clean_name[:50]
    
    return clean_name if clean_name else "会议纪要"

# 自动提取会议主题
MEETING_NAME_PATTERN = r"会议主题[:：]\s*(.+)"

def extract_meeting_name(minutes_markdown: str) -> str:
    match = re.search(MEETING_NAME_PATTERN, minutes_markdown)
    if match:
        return clean_filename(match.group(1))
    return "会议纪要"

# 保存为本地 markdown 文件
def save_to_local_markdown(content: str, meeting_name: str = "会议纪要", output_dir: str = "outputs") -> str:
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # 清理会议名称，确保文件名安全
        clean_name = clean_filename(meeting_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{clean_name}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        # 确保文件路径有效
        filepath = os.path.normpath(filepath)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"文件已保存: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"保存文件失败: {e}")
        # 使用备用文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback_filename = f"meeting_{timestamp}.md"
        fallback_path = os.path.join(output_dir, fallback_filename)
        try:
            with open(fallback_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"使用备用文件名保存: {fallback_path}")
            return fallback_path
        except Exception as e2:
            print(f"备用保存也失败: {e2}")
            raise e2

# 移除切片和并发相关常量
# SEGMENT_LENGTH_MS = 5 * 60 * 1000  # 5分钟
# MAX_WORKERS = 2  # 2线程并发

# 移除切片和并发相关函数
def split_audio(file_path, segment_length_ms=None):
    raise NotImplementedError("已禁用音频切片功能")
def transcribe_audio_segments(whisper, segment_paths, max_workers=None):
    raise NotImplementedError("已禁用并发推理功能")
def transcribe_long_audio_with_segments(whisper, audio_path, max_minutes=5):
    raise NotImplementedError("已禁用长音频切片推理功能")

def _transcribe_auto(whisper: LocalWhisper, audio_path: str, max_minutes=5):
    # 直接整体推理，不再切片
    return whisper.transcribe(audio_path)

class MeetingProcessor:
    def __init__(self, whisper_model_dir: str = "whisper-large-v3", device: str = "auto"):
        self.whisper = LocalWhisper(whisper_model_dir, device)
        self.speaker_identifier = None  # 延迟初始化，默认启用声纹识别
        
    def _cleanup_memory(self):
        """清理内存和GPU缓存"""
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("GPU内存已清理")

    def process(self, audio_path: str, meeting_name: Optional[str] = None, output_dir: str = "outputs", max_minutes: int = 5) -> dict:
        transcript = self.whisper.transcribe(audio_path)
        cleaned = clean_transcript(transcript)
        
        # 获取音频时长以生成动态会议纪要
        audio_duration = get_audio_duration(audio_path)
        minutes = generate_meeting_minutes(cleaned, audio_duration)
        auto_name = extract_meeting_name(minutes)
        final_name = meeting_name or auto_name
        md_path = save_to_local_markdown(minutes, final_name, output_dir)
        return {
            "transcript": transcript,
            "cleaned": cleaned,
            "minutes": minutes,
            "meeting_name": final_name,
            "markdown_path": md_path
        }
    
    def process_with_speaker_id(self, audio_path: str, meeting_name: Optional[str] = None, 
                               output_dir: str = "outputs") -> dict:
        """
        会议处理流程（默认启用声纹识别）- 优化版
        """
        import time
        start_time = time.time()
        
        try:
            print("开始音频转写...")
            
            # 1. 音频转写 (带时间戳)
            transcribe_start = time.time()
            segments = self.whisper.transcribe_with_timestamps(audio_path)
            transcribe_time = time.time() - transcribe_start
            print(f"音频转写完成，用时: {transcribe_time:.1f}秒")
            
            print("执行发言人识别...")
            # 2. 初始化声纹识别器（延迟初始化）
            if self.speaker_identifier is None:
                try:
                    print("正在初始化声纹识别模型...")
                    if IMPROVED_SPEAKER_ID_AVAILABLE:
                        try:
                            # 优先使用精确版
                            print("使用精确版声纹识别器")
                            self.speaker_identifier = PrecisionSpeakerIdentifier()
                        except NameError:
                            try:
                                # 降级到改进版
                                print("使用改进版声纹识别器")
                                self.speaker_identifier = ImprovedSpeakerIdentifier()
                            except NameError:
                                # 降级到标准版
                                print("使用标准声纹识别器")
                                self.speaker_identifier = SpeakerIdentifier()
                    else:
                        print("使用标准声纹识别器")
                        self.speaker_identifier = SpeakerIdentifier()
                    
                    if not self.speaker_identifier.available:
                        print("警告: 声纹识别模型初始化失败，将使用普通转写模式")
                except Exception as e:
                    print(f"声纹识别初始化失败: {e}")
                    print("降级到普通转写模式")
                    self.speaker_identifier = None
            
            # 3. 发言人识别（简化版本）
            speaker_count = 0
            if self.speaker_identifier and self.speaker_identifier.available:
                try:
                    print("开始发言人识别...")
                    abs_audio_path = os.path.abspath(audio_path)
                    # 检查是否为精确版声纹识别
                    if isinstance(self.speaker_identifier, PrecisionSpeakerIdentifier):
                        print("使用精确版算法，目标5人识别")
                        speaker_segments = self.speaker_identifier.identify_speakers(abs_audio_path, target_speakers=5)
                        # 转换为兼容格式
                        if speaker_segments:
                            unique_speakers = set(seg.speaker_id for seg in speaker_segments)
                            speaker_result = {
                                'total_speakers': len(unique_speakers),
                                'segments': [{'speaker': seg.speaker_id, 'start': seg.start_time, 'end': seg.end_time} 
                                           for seg in speaker_segments]
                            }
                        else:
                            speaker_result = {'error': 'No speakers detected', 'total_speakers': 0}
                    else:
                        # 传统方法
                        speaker_result = self.speaker_identifier.identify_speakers(abs_audio_path, min_speakers=2, max_speakers=5)
                    
                    # 检查识别结果
                    detected_speakers = speaker_result.get('total_speakers', 0)
                    print(f"声纹识别检测到 {detected_speakers} 个发言人")
                    
                    if not speaker_result.get('error') and detected_speakers > 0:
                        # 匹配转写文本与发言人
                        if isinstance(self.speaker_identifier, PrecisionSpeakerIdentifier):
                            # 精确版：直接使用分段信息格式化
                            matched_segments = self._format_precision_segments(segments, speaker_segments)
                        else:
                            # 传统方法
                            matched_segments = self.speaker_identifier.match_transcript_to_speakers(
                                segments, speaker_result['segments']
                            )
                        formatted_transcript = self._format_speaker_transcript(matched_segments)
                        speaker_count = detected_speakers
                        print(f"发言人识别成功！识别到 {speaker_count} 个发言人")
                    else:
                        print("声纹识别失败或未检测到发言人，使用智能估算")
                        formatted_transcript = "\n".join([seg['text'] for seg in segments])
                        # 智能估算发言人数量，而不是直接设为0
                        estimated_speakers = self._estimate_speaker_count_from_transcript(segments)
                        speaker_count = max(1, estimated_speakers)  # 至少1个发言人
                        print(f"基于转写内容估算发言人数: {speaker_count}")
                        
                        # 为转写添加估算的发言人标识
                        formatted_transcript = self._add_estimated_speakers(segments, speaker_count)
                except Exception as e:
                    print(f"发言人识别异常: {e}")
                    print(f"异常类型: {type(e).__name__}")
                    # 即使异常也尝试估算发言人数并强制格式化
                    try:
                        estimated_speakers = self._estimate_speaker_count_from_transcript(segments)
                        speaker_count = max(1, estimated_speakers)
                        print(f"异常恢复: 估算发言人数 {speaker_count}")
                        formatted_transcript = self._add_estimated_speakers(segments, speaker_count)
                    except:
                        speaker_count = 1  # 至少设为1而不是0
                        print(f"最终保底: 设置发言人数为 {speaker_count}")
                        # 最后的保底措施：强制添加发言人标识
                        formatted_transcript = self._add_estimated_speakers(segments, speaker_count)
            else:
                # 不使用发言人识别
                print("使用普通转写模式")
                # 即使不使用声纹识别，也估算发言人数量并强制格式化
                estimated_speakers = self._estimate_speaker_count_from_transcript(segments)
                speaker_count = max(1, estimated_speakers)
                print(f"普通模式估算发言人数: {speaker_count}")
                formatted_transcript = self._add_estimated_speakers(segments, speaker_count)
            
            print("生成会议纪要...")
            # 4. 文本规整和纪要生成
            cleaned = clean_transcript(formatted_transcript)
            
            # 获取音频时长以生成动态会议纪要
            audio_duration = get_audio_duration(audio_path)
            minutes = generate_meeting_minutes(cleaned, audio_duration)
            
            # 5. 保存结果
            auto_name = extract_meeting_name(minutes)
            final_name = meeting_name or auto_name
            
            # 同时保存转写内容和纪要
            transcript_md_path = save_to_local_markdown(formatted_transcript, f"会议内容_{final_name}", output_dir)
            minutes_md_path = save_to_local_markdown(minutes, f"会议纪要_{final_name}", output_dir)
            
            # 性能统计和清理
            total_time = time.time() - start_time
            print(f"[OK] 处理完成！总用时: {total_time:.1f}秒")
            
            # 清理内存
            self._cleanup_memory()
            
            return {
                "transcript": formatted_transcript,
                "cleaned": cleaned,
                "minutes": minutes,
                "meeting_name": final_name,
                "transcript_markdown_path": transcript_md_path,
                "minutes_markdown_path": minutes_md_path,
                "speaker_count": speaker_count
            }
        
        except Exception as e:
            print(f"[ERROR] 处理失败: {e}")
            # 确保在出错时也清理内存
            self._cleanup_memory()
            raise e
    
    # 为了向后兼容，保留旧的process方法，但现在也使用声纹识别
    def process(self, audio_path: str, meeting_name: Optional[str] = None, output_dir: str = "outputs", max_minutes: int = 5) -> dict:
        """
        旧的process方法，现在也默认使用声纹识别
        为了向后兼容而保留
        """
        return self.process_with_speaker_id(audio_path, meeting_name, output_dir)
    
    def _format_precision_segments(self, transcript_segments, speaker_segments) -> List:
        """
        匹配精确版声纹识别结果与转写文本
        """
        matched_segments = []
        
        for transcript_seg in transcript_segments:
            # 查找时间重叠最大的说话人段落
            best_match = None
            max_overlap = 0
            
            for speaker_seg in speaker_segments:
                # 计算时间重叠
                start_overlap = max(transcript_seg['start'], speaker_seg.start_time)
                end_overlap = min(transcript_seg['end'], speaker_seg.end_time)
                
                if end_overlap > start_overlap:
                    overlap = end_overlap - start_overlap
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_match = speaker_seg
            
            # 创建匹配的段落对象
            if best_match:
                matched_segments.append(SpeakerSegment(
                    start_time=transcript_seg['start'],
                    end_time=transcript_seg['end'],
                    speaker_id=best_match.speaker_id,
                    text=transcript_seg['text']
                ))
            else:
                # 默认分配给Speaker_0
                matched_segments.append(SpeakerSegment(
                    start_time=transcript_seg['start'],
                    end_time=transcript_seg['end'],
                    speaker_id="Speaker_0",
                    text=transcript_seg['text']
                ))
        
        return matched_segments
    
    def _format_speaker_transcript(self, segments: List[SpeakerSegment]) -> str:
        """
        将匹配的段落格式化为带发言人标识的文本
        """
        formatted_lines = []
        current_speaker = None
        
        for segment in segments:
            # 当发言人改变时，添加发言人标识
            if segment.speaker_id != current_speaker:
                current_speaker = segment.speaker_id
                # 如果不是第一个发言人，前面加换行
                if formatted_lines:
                    formatted_lines.append("")
                formatted_lines.append(f"【{current_speaker}】")
            
            # 添加发言内容
            formatted_lines.append(f"{segment.text.strip()}")
        
        return "\n".join(formatted_lines)
    
    def _estimate_speaker_count_from_transcript(self, segments: List[dict]) -> int:
        """
        从转写内容估算发言人数量
        基于语音停顿、语调变化等特征
        """
        try:
            if not segments or len(segments) == 0:
                return 1
            
            # 1. 基于语音段数量的简单估算
            total_segments = len(segments)
            
            # 2. 分析语音段的时间分布
            total_duration = segments[-1]['end'] - segments[0]['start'] if len(segments) > 1 else segments[0].get('end', 1) - segments[0].get('start', 0)
            
            # 3. 简单启发式规则
            if total_duration < 30:  # 30秒以下
                estimated = 1
            elif total_duration < 120:  # 2分钟以下
                estimated = min(2, max(1, total_segments // 5))
            elif total_duration < 300:  # 5分钟以下
                estimated = min(3, max(1, total_segments // 8))
            else:  # 5分钟以上
                estimated = min(5, max(2, total_segments // 12))
            
            print(f"[估算] 基于{total_segments}段语音，{total_duration:.1f}秒，估算{estimated}人")
            return estimated
            
        except Exception as e:
            print(f"[估算] 发言人数量估算失败: {e}")
            return 2  # 默认返回2人
    
    def _add_estimated_speakers(self, segments: List[dict], speaker_count: int) -> str:
        """
        为转写内容添加估算的发言人标识
        """
        try:
            if not segments:
                return ""
            
            formatted_lines = []
            
            # 简单策略：按时间顺序分配发言人
            segment_per_speaker = max(1, len(segments) // speaker_count)
            
            for i, segment in enumerate(segments):
                # 计算当前发言人ID
                speaker_id = i // segment_per_speaker
                if speaker_id >= speaker_count:
                    speaker_id = speaker_count - 1
                
                # 在发言人切换时添加标识
                if i == 0 or (i // segment_per_speaker) != ((i-1) // segment_per_speaker):
                    # 如果不是第一个发言人，前面加空行
                    if formatted_lines:
                        formatted_lines.append("")
                    formatted_lines.append(f"【Speaker_{speaker_id}】")
                
                formatted_lines.append(segment['text'].strip())
            
            return "\n".join(formatted_lines)
            
        except Exception as e:
            print(f"[估算] 添加发言人标识失败: {e}")
            return "\n".join([seg['text'] for seg in segments])

print("DEEPSEEK_API_KEY =", os.getenv("DEEPSEEK_API_KEY"))

