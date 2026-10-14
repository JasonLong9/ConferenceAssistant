# ConferenceAssistant 开发者文档

## 项目概述

ConferenceAssistant 是一个基于AI的会议音频处理系统，提供音频转写、发言人识别、会议纪要生成和智能问答功能。

## 技术架构

### 核心组件

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Service   │    │  Core Processor │    │  Meeting Chat   │
│   (FastAPI)     │────│   (WhisperAI)   │────│   (DeepSeek)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Task Manager   │    │ Speaker ID      │    │  Chat Session   │
│  (Async Tasks)  │    │ (Voice Print)   │    │  (Context Mgmt) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术栈

- **Web框架**: FastAPI + Pydantic
- **语音识别**: faster-whisper (本地推理)
- **声纹识别**: SpeechBrain/pyannote-audio
- **大语言模型**: DeepSeek V3 API
- **异步处理**: Python Threading
- **音频处理**: pydub + AudioSegment

## 项目结构

```
ConferenceAssistant/
├── core.py                     # 核心处理逻辑
├── web_service.py             # Web API 服务
├── meeting_chat.py            # 会议问答模块
├── async_task_manager.py      # 异步任务管理
├── speaker_identification.py  # 声纹识别
├── main.py                   # 命令行入口
├── test_*.py                 # 测试文件
├── API_DOCUMENTATION.md      # API文档
├── DEVELOPER_GUIDE.md        # 开发文档
└── README.md                 # 项目说明
```

## 核心模块详解

### 1. 核心处理器 (`core.py`)

#### MeetingProcessor 类
负责整个音频处理流程的协调。

**主要方法**:
- `process_with_speaker_id()`: 完整的音频处理流程
- `_format_speaker_transcript()`: 格式化发言人转写结果

**处理流程**:
1. 音频转写 (Whisper)
2. 声纹识别 (SpeakerIdentifier)  
3. 转写结果与发言人匹配
4. 文本规整 (DeepSeek API)
5. 会议纪要生成 (DeepSeek API)
6. 保存结果文件

#### LocalWhisper 类
封装 faster-whisper 模型的本地推理。

**特性**:
- 单例模式，避免重复加载模型
- 支持带时间戳的转写
- GPU加速推理

```python
# 使用示例
whisper = LocalWhisper("whisper-large-v3", "cuda")
segments = whisper.transcribe_with_timestamps("audio.wav")
```

### 2. Web服务 (`web_service.py`)

基于 FastAPI 的RESTful API服务，提供异步音频处理和问答接口。

#### 异步任务处理
```python
@app.post("/audio2summary_async")
async def audio2summary_async(file: UploadFile = File(...)):
    # 创建异步任务
    task_id = generate_task_id()
    # 启动后台处理线程
    threading.Thread(target=process_task, daemon=True).start()
    return {"task_id": task_id, "status": "pending"}
```

#### 任务状态管理
- 使用全局字典 `TASKS` 存储任务状态
- 支持进度跟踪和ETA计算
- 错误处理和异常恢复

### 3. 会议问答 (`meeting_chat.py`)

实现基于会议内容的智能问答和连续对话功能。

#### MeetingChatSession 类
管理单个会议的对话会话。

**核心功能**:
- 维护对话历史
- 构建完整上下文
- 会话状态管理

```python
class MeetingChatSession:
    def __init__(self, task_id: str, cleaned_content: str, meeting_minutes: str):
        self.conversation_history: List[Dict[str, str]] = []
        self.context = self._build_initial_context()
    
    def get_conversation_context(self) -> str:
        # 结合初始上下文和对话历史
        pass
```

#### MeetingChatManager 类
全局会话管理器，处理多个会话的创建、查询和管理。

**主要方法**:
- `create_session()`: 创建新的对话会话
- `ask_question()`: 处理用户提问
- `get_conversation_history()`: 获取对话历史
- `_call_deepseek()`: 调用DeepSeek API

### 4. 异步任务管理 (`async_task_manager.py`)

轻量级的任务状态管理系统。

```python
TASKS = {}  # 全局任务字典

def set_task_status(task_id, status, progress=0, result=None, error=None):
    # 更新任务状态，计算ETA
    pass
```

**状态定义**:
- `pending`: 等待处理
- `processing`: 正在处理
- `done`: 处理完成
- `error`: 处理出错

### 5. 声纹识别 (`speaker_identification.py`)

基于深度学习的声纹识别和说话人分离。

#### SpeakerIdentifier 类
```python
class SpeakerIdentifier:
    def identify_speakers(self, audio_path: str, min_speakers=2, max_speakers=8):
        # 执行声纹识别
        # 返回发言人分段结果
        pass
    
    def match_transcript_to_speakers(self, transcript_segments, speaker_segments):
        # 将转写结果与发言人匹配
        pass
```

## DeepSeek API集成

### 系统提示词设计

#### 文本规整提示词
```python
CLEAN_PROMPT = '''<instruction>
根据提供的录音文件的转录文本内容。对这些文本进行预整理...
4. 对文本进行分析，精准识别不同发言人的内容，并以清晰格式区分呈现
</instruction>'''
```

#### 会议纪要生成提示词
```python
SYSTEM_PROMPT = '''<instruction>
根据提供的录音文件文本，生成一份结构清晰、详细明了的会议纪要...
在列出总结性信息后，列出重要时间点所讨论的话题与结果
</instruction>'''
```

#### 问答助手提示词
```python
system_prompt = """你是一个专业的会议助手，请基于提供的会议内容和对话历史来回答用户的问题。

要求：
1. 基于会议内容准确回答问题
2. 如果问题涉及具体人员发言，请指出是哪个发言人
3. 参考之前的对话历史，保持对话的连贯性
"""
```

## 开发环境搭建

### 1. 环境要求
- Python 3.8+
- CUDA 11.8+ (GPU推理)
- 8GB+ RAM
- 2GB+ 显存

### 2. 依赖安装
```bash
pip install fastapi uvicorn
pip install faster-whisper
pip install speechbrain pyannote-audio
pip install pydub requests python-dotenv
```

### 3. 模型下载
```bash
# Whisper 模型 (自动下载)
python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3')"

# 声纹识别模型 (自动下载)
python speaker_identification.py
```

### 4. 环境变量配置
```bash
# .env 文件
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 5. 启动服务
```bash
# 开发模式
uvicorn web_service:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn web_service:app --host 0.0.0.0 --port 8000 --workers 1
```

## 测试指南

### 单元测试
```bash
python -m pytest test_*.py -v
```

### 集成测试
```bash
# 完整流程测试
python test_meeting_chat_api.py

# 声纹识别测试
python test_speaker_id.py

# Web API测试  
python test_web_api.py
```

### 性能测试
```bash
# 音频处理性能
python -m cProfile -s cumulative main.py test_audio.wav

# API并发测试
ab -n 100 -c 10 http://localhost:8000/task_status?task_id=test
```

## 扩展开发

### 1. 添加新的音频格式支持

在 `core.py` 中扩展音频处理逻辑：
```python
def preprocess_audio(audio_path: str) -> str:
    """预处理音频，转换为支持的格式"""
    audio = AudioSegment.from_file(audio_path)
    # 转换为WAV格式
    wav_path = audio_path.replace(Path(audio_path).suffix, '.wav')
    audio.export(wav_path, format="wav")
    return wav_path
```

### 2. 集成其他大语言模型

创建新的API调用函数：
```python
def call_custom_llm(system_prompt: str, user_content: str) -> str:
    """调用自定义大语言模型API"""
    # 实现API调用逻辑
    pass
```

### 3. 添加更多问答功能

扩展 `MeetingChatManager` 类：
```python
def summarize_conversation(self, task_id: str) -> Dict:
    """总结当前对话内容"""
    pass

def export_conversation(self, task_id: str, format: str = "json") -> str:
    """导出对话记录"""
    pass
```

### 4. 优化声纹识别

```python
class AdvancedSpeakerIdentifier(SpeakerIdentifier):
    def __init__(self, model_name="custom_model"):
        # 使用自定义声纹识别模型
        pass
    
    def cluster_speakers(self, embeddings):
        # 实现更高级的说话人聚类算法
        pass
```

## 部署指南

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "web_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 100M;
        proxy_read_timeout 300s;
    }
}
```

## 监控和日志

### 日志配置
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 性能监控
```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logging.info(f"{func.__name__} took {elapsed_time:.2f} seconds")
        return result
    return wrapper
```

## 常见问题

### Q1: GPU内存不足
**解决方案**: 
- 降低Whisper模型精度: `compute_type="int8"`
- 使用CPU推理: `device="cpu"`
- 增加虚拟内存

### Q2: DeepSeek API调用失败
**解决方案**:
- 检查API Key配置
- 验证网络连接
- 增加重试机制

### Q3: 声纹识别准确度低
**解决方案**:
- 提高音频质量
- 调整最小/最大说话人数
- 使用更好的音频预处理

### Q4: 处理速度慢
**优化建议**:
- 使用GPU加速
- 优化音频预处理
- 实施并发处理

## 贡献指南

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -m 'Add new feature'`
4. 推送到分支: `git push origin feature/new-feature`
5. 提交 Pull Request

## 版本历史

- **v1.0.0**: 基础音频转写和纪要生成
- **v1.1.0**: 添加声纹识别功能
- **v1.2.0**: 集成会议问答和连续对话功能

## 许可证

MIT License - 详见 LICENSE 文件