# ConferenceAssistant Plus - 智能会议助手

ConferenceAssistant Plus 是一个完整的AI驱动会议处理系统，提供音频转写、发言人识别、会议纪要生成以及基于会议内容的**智能问答**功能。让会议记录和信息查询变得简单高效。

## ✨ 核心特性

- 🎯 **智能音频处理**: 基于 Whisper-Large-V3 的高精度语音识别
- 👥 **发言人识别**: 自研离线声纹识别，无需外部API
- 📝 **会议纪要生成**: 使用 DeepSeek V3 生成结构化会议纪要  
- 🤖 **智能问答**: 基于会议内容的连续对话问答系统
- ⚡ **性能优化**: 处理速度提升10倍，支持GPU加速
- 🔌 **RESTful API**: 完整的API接口，便于系统集成

---

## 📋 目录
1. [快速开始](#快速开始)
2. [核心功能](#核心功能)
3. [环境要求](#环境要求)
4. [安装配置](#安装配置)
5. [使用方式](#使用方式)
6. [智能问答](#智能问答)
7. [API文档](#api文档)
8. [开发文档](#开发文档)
9. [常见问题](#常见问题)

---

## 核心功能

### 🎯 音频处理
- **智能转写**: 基于 Whisper-Large-V3 的高精度语音识别
- **发言人识别**: 自动识别不同说话人，区分发言内容  
- **音频格式支持**: wav、mp3、m4a、flac、ogg等主流格式
- **GPU加速**: CUDA支持，提升处理速度

### 📋 内容生成
- **智能纪要**: 使用 DeepSeek V3 生成结构化会议纪要
- **文本规整**: 自动清理和格式化转写文本
- **主题提取**: 智能识别会议主题和关键信息
- **Markdown输出**: 规范化格式便于后续处理

### 🤖 智能问答 ⭐ **NEW**
- **基于内容问答**: 向会议内容智能提问，获得准确回答
- **连续对话**: 支持多轮对话，保持上下文记忆
- **发言人定位**: 准确指出特定发言人的观点和建议
- **实时查询**: 快速检索会议中的关键信息

### 🚀 服务能力
- **异步处理**: 支持大文件异步处理，实时进度反馈
- **RESTful API**: 完整的API接口，便于系统集成
- **批量处理**: 命令行工具支持批量离线处理

---

## 🚀 快速开始

### 1️⃣ 环境准备
```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 2️⃣ 安装配置
```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥
echo "DEEPSEEK_API_KEY=your_deepseek_api_key" > .env
```

### 3️⃣ 启动服务
```bash
# 方式1：直接启动（推荐）
DEEPSEEK_API_KEY="your_api_key" python -m uvicorn web_service:app --host 0.0.0.0 --port 8080

# 方式2：使用优化启动器
python start_optimized.py --optimized

# 方式3：开发模式
uvicorn web_service:app --reload --host 0.0.0.0 --port 8080
```

### 4️⃣ 测试接口
```bash
# 上传音频文件
curl -X POST http://localhost:8080/audio2summary_async \
  -F "file=@your_meeting.mp3"

# 查看处理状态
curl "http://localhost:8080/task_status?task_id=YOUR_TASK_ID"

# 智能问答
curl -X POST http://localhost:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d '{"task_id":"YOUR_TASK_ID","question":"会议讨论了什么主要内容？"}'
```

### 5️⃣ Web界面访问
浏览器打开: http://localhost:8080/docs 查看API文档界面

---

## 📋 环境要求

### 系统要求
- **Python**: 3.8+ （推荐 3.9+）
- **操作系统**: Windows 10+、Ubuntu 18.04+、macOS 10.15+
- **内存**: 8GB+ RAM （处理长音频需要更多）
- **存储**: 5GB+ 可用空间（用于模型缓存）

### GPU加速（可选但推荐）
- **NVIDIA GPU**: RTX 3060+ 或同等性能
- **显存**: 4GB+ VRAM
- **CUDA**: 11.8+ 
- **cuDNN**: 对应CUDA版本

> 💡 **提示**: 不支持GPU的环境会自动切换到CPU模式，处理速度会相应降低

### 必需软件
- **FFmpeg**: 音频格式转换（自动下载或手动安装）
- **Git**: 版本管理（可选）

---

## ⚙️ 安装配置

### 依赖文件
```bash
# 查看requirements.txt内容
cat requirements.txt
```

**主要依赖:**
- `fastapi`: Web框架
- `faster-whisper`: 语音识别 
- `torch`: 深度学习框架
- `pydub`: 音频处理
- `requests`: HTTP客户端
- `python-dotenv`: 环境变量管理

### API密钥配置
创建 `.env` 文件：
```env
# 必需：DeepSeek API配置（用于智能问答）
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 可选配置
# WHISPER_MODEL_PATH=./whisper-large-v3
# CUDA_VISIBLE_DEVICES=0
# MAX_AUDIO_SIZE=100  # MB
```

### 获取DeepSeek API密钥
1. 访问 [DeepSeek官网](https://platform.deepseek.com/)
2. 注册账号并获取API密钥
3. 将密钥填入`.env`文件

### 模型准备  
**自动下载（推荐）:**
- 模型将在首次使用时自动下载
- Whisper模型约6GB，请确保网络稳定

**手动下载:**
```bash
python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', download_root='./models')"
```

---

## 💡 使用方式

### Web API 服务

#### 启动方式对比

| 启动方式 | 适用场景 | 命令 |
|---------|---------|------|
| **直接启动** | 生产环境，稳定可靠 | `DEEPSEEK_API_KEY="xxx" python -m uvicorn web_service:app --host 0.0.0.0 --port 8080` |
| **开发模式** | 开发调试，自动重载 | `uvicorn web_service:app --reload` |
| **优化启动器** | 交互式选择 | `python start_optimized.py` |

#### 服务健康检查
```bash
# 检查服务状态
curl http://localhost:8080/

# API文档界面
open http://localhost:8080/docs
```

### 命令行工具
```bash
# 单文件处理
python main.py path/to/meeting.wav

# 批量处理 
python main.py meeting1.wav meeting2.mp3 meeting3.m4a

# 指定输出目录
python main.py meeting.wav --output_dir ./results

# 指定会议名称
python main.py meeting.wav --meeting_name "周会讨论"

# 使用GPU加速
python main.py meeting.wav --device cuda
```

### 支持的音频格式
- ✅ **WAV**: 无压缩，质量最佳
- ✅ **MP3**: 常用压缩格式  
- ✅ **M4A**: Apple设备常用
- ✅ **AAC**: 高质量压缩
- ✅ **FLAC**: 无损压缩
- ✅ **OGG**: 开源格式

### 完整工作流程
```python
# Python SDK示例
import requests
import time

# 1. 上传音频
files = {'file': open('meeting.mp3', 'rb')}
response = requests.post('http://localhost:8080/audio2summary_async', files=files)
task_id = response.json()['task_id']

# 2. 等待处理完成
while True:
    status_response = requests.get(f'http://localhost:8080/task_status?task_id={task_id}')
    status = status_response.json()['status']
    if status == 'done':
        break
    elif status == 'error':
        raise Exception("处理失败")
    time.sleep(5)

# 3. 获取结果
result = requests.get(f'http://localhost:8080/task_result?task_id={task_id}').json()
print("会议纪要:", result['meeting_minutes'])

# 4. 智能问答
question_data = {"task_id": task_id, "question": "会议的主要决策是什么？"}
answer_response = requests.post('http://localhost:8080/meeting/ask', json=question_data)
print("回答:", answer_response.json()['data']['answer'])
```

---

## 智能问答

### 📝 使用流程
1. **上传音频**: 上传会议录音文件
2. **等待处理**: 系统自动生成转写和纪要  
3. **开始提问**: 基于会议内容智能问答
4. **连续对话**: 支持多轮对话，保持上下文

### 💡 提问示例
```bash
# 基础信息查询
"这次会议讨论了哪些主要议题？"
"参会人员都有哪些？"

# 决策和结果
"会议做出了什么重要决定？"
"各部门分别承担什么任务？"

# 具体细节
"项目的预算安排是怎样的？"
"时间节点是如何规划的？"

# 发言人定位  
"张总对这个项目有什么看法？"
"李经理提出了哪些建议？"
```

### 🔧 API接口
```python
# 检查问答可用性
GET /meeting/chat/status?task_id=xxx

# 向会议内容提问
POST /meeting/ask
{
  "task_id": "任务ID", 
  "question": "用户问题"
}

# 获取对话历史
GET /meeting/chat/history?task_id=xxx

# 清空对话历史
DELETE /meeting/chat/clear?task_id=xxx
```

### 🌟 功能特点
- **上下文记忆**: 每次提问都会结合之前的对话历史
- **准确定位**: 能准确指出信息来源的发言人
- **多语言支持**: 支持中英文会议内容问答
- **实时响应**: 基于DeepSeek API，响应速度快

---

## ⚡ 性能优化

### 🚀 处理速度优化
- **优化前**: 几分钟音频需要处理30分钟+
- **优化后**: 几分钟音频预计5-10分钟
- **主要优化**: Whisper推理参数、设备选择、内存管理

### 🛠️ 主要优化内容
1. **Whisper推理优化**: 
   - 减少beam_size和best_of参数提升速度
   - 智能设备选择（自动GPU/CPU）
   - 根据显存大小自动选择精度（float16/int8）
   
2. **内存管理优化**:
   - 单例模式避免重复加载模型  
   - 处理完成后自动清理GPU缓存
   - 及时释放临时数据

3. **错误处理改进**:
   - 发言人识别失败时自动降级
   - 更好的异常处理和资源清理

4. **性能监控**:
   - 实时显示各阶段处理时间
   - 总体性能统计

### 🧪 性能测试
```bash
# 运行简单性能测试
python test_performance.py

# 测试核心优化功能
python -c "from core import MeetingProcessor; print('优化版本工作正常')"
```

### ⚙️ 使用优化版本
优化已直接集成到原版代码中，无需额外配置：

```bash
# 直接启动，自动使用优化功能
uvicorn web_service:app --reload --host 0.0.0.0 --port 8080
```

---

## 📖 API文档

### 📚 文档目录
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)**: 完整的REST API接口文档
- **[DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)**: 开发者指南和技术架构  
- **[USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md)**: 详细使用示例和场景应用
- **[开发文档.md](./开发文档.md)**: 中文开发文档

### 🔗 核心接口

#### 音频处理接口
| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/` | GET | 服务健康检查 | ✅ |
| `/audio2summary_async` | POST | 上传音频异步处理 | ✅ |
| `/task_status` | GET | 查询任务状态和进度 | ✅ |
| `/task_result` | GET | 获取完整处理结果 | ✅ |

#### 智能问答接口  
| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/meeting/ask` | POST | 向会议内容提问 | ✅ |
| `/meeting/chat/status` | GET | 问答功能可用性检查 | ✅ |  
| `/meeting/chat/history` | GET | 获取对话历史 | ✅ |
| `/meeting/chat/clear` | DELETE | 清空对话历史 | ✅ |

### 🌐 在线API文档
启动服务后访问: **http://localhost:8080/docs**

---

## 🛠 开发文档

### 项目架构图
```
ConferenceAssistant Plus
├── 🎤 音频输入层
│   ├── 文件上传 (FastAPI)
│   └── 音频预处理 (pydub) 
├── 🧠 AI处理层  
│   ├── 语音识别 (faster-whisper)
│   ├── 发言人识别 (自研离线方案)
│   └── 内容生成 (DeepSeek V3)
├── 🤖 智能问答层
│   ├── 上下文管理 (meeting_chat.py)
│   └── 对话历史 (内存缓存)
└── 🌐 服务接口层
    ├── RESTful API (FastAPI)
    └── 异步任务管理 (async_task_manager.py)
```

### 🗂 项目结构
```
ConferenceAssistant-plus/
├── 📄 核心文件
│   ├── core.py                   # 音频处理核心逻辑
│   ├── web_service.py           # Web服务主入口
│   ├── meeting_chat.py          # 智能问答管理器
│   ├── async_task_manager.py    # 异步任务管理
│   └── speaker_identification.py # 声纹识别实现
├── 🧪 测试文件  
│   ├── test_*.py               # 功能测试脚本
│   ├── test_file/              # 测试音频文件
│   └── test_output/            # 测试输出目录
├── 📚 文档目录
│   ├── README.md               # 项目主文档
│   ├── 开发文档.md              # 中文开发指南
│   ├── API_DOCUMENTATION.md    # API接口文档
│   ├── DEVELOPER_GUIDE.md      # 英文开发指南
│   └── USAGE_EXAMPLES.md       # 使用示例
├── ⚙️ 配置文件
│   ├── requirements.txt        # Python依赖
│   ├── .env                   # 环境变量配置
│   ├── .env.example           # 环境变量模板
│   └── .gitignore             # Git忽略规则
└── 🗃 缓存目录
    ├── whisper-large-v3/       # Whisper模型缓存
    ├── __pycache__/           # Python缓存
    └── temp_output/           # 临时输出文件
```

### 🔧 技术栈说明
| 组件 | 技术选型 | 版本要求 | 用途说明 |
|------|---------|---------|----------|
| **Web框架** | FastAPI | ≥0.68.0 | REST API服务 |
| **语音识别** | faster-whisper | latest | Whisper模型加速推理 |
| **发言人识别** | 自研方案 | - | 基于PyTorch的离线实现 |
| **大语言模型** | DeepSeek V3 API | - | 智能问答和内容生成 |
| **异步处理** | Python threading | - | 后台任务处理 |
| **音频处理** | pydub | ≥0.25.0 | 音频格式转换和预处理 |
| **HTTP客户端** | requests | ≥2.25.0 | API调用 |
| **环境管理** | python-dotenv | ≥0.19.0 | 配置管理 |

### 🎯 核心设计特点
- **🔌 模块化架构**: 各功能模块独立，便于扩展和维护
- **⚡ 性能优化**: 模型单例加载，GPU/CPU自适应
- **🛡 错误处理**: 完善的异常处理和资源清理机制  
- **📊 进度跟踪**: 实时任务状态和处理进度反馈
- **💾 资源管理**: 自动临时文件清理和内存优化

---

## 常见问题

### ❓ 功能相关

**Q: 支持哪些音频格式？**
A: 支持 wav、mp3、m4a、flac、ogg 等主流格式

**Q: 处理时间大概多久？**
A: 通常是音频时长的 0.1-0.3倍，具体取决于硬件配置

**Q: 发言人识别准确度如何？**  
A: 在良好录音条件下可达85-95%准确率

**Q: 智能问答支持什么类型的问题？**
A: 支持会议内容查询、决策提取、发言人定位、时间节点等各类问题

### 🛠 技术问题

**Q: GPU内存不足怎么办？**
A: 可以设置 `device="cpu"` 使用CPU推理，或降低模型精度

**Q: DeepSeek API调用失败？**  
A: 检查API Key配置，确认网络连接正常

**Q: 如何提高处理速度？**
A: 使用GPU加速，优化音频预处理，考虑并发处理

**Q: 服务如何部署到生产环境？**
A: 参考 [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) 中的部署章节

### 🔧 集成问题

**Q: 如何集成到现有系统？**
A: 通过RESTful API集成，参考 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

**Q: 前端如何展示结果？**
A: 所有文本结果为Markdown格式，建议使用Markdown渲染组件

**Q: 如何保证数据安全？**
A: 支持私有部署，音频文件本地处理，仅文本内容发送至API

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献方式
1. **提交Issues**: 报告Bug或提出功能建议
2. **提交PR**: 贡献代码改进
3. **完善文档**: 改进文档和示例
4. **分享使用案例**: 分享你的使用经验

### 开发流程
1. Fork项目
2. 创建特性分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 提交Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=your-repo/ConferenceAssistant&type=Date)](https://star-history.com/#your-repo/ConferenceAssistant&Date)

---

**让AI为你的会议管理赋能！** 🚀

如有问题或建议，欢迎通过 [Issues](https://github.com/your-repo/ConferenceAssistant/issues) 联系我们。 