# ConferenceAssistant API 接口文档

## 概述

ConferenceAssistant 提供完整的会议音频处理和问答服务，包括音频转写、发言人识别、会议纪要生成以及基于会议内容的智能问答功能。

**基础URL**: `http://localhost:8080`

## 认证

目前所有接口均无需认证，但需要确保 DeepSeek API Key 已正确配置在环境变量中：
```bash
export DEEPSEEK_API_KEY="your_deepseek_api_key"
```

---

## 1. 音频处理接口

### 1.1 异步音频处理

**POST** `/audio2summary_async`

上传音频文件进行异步处理，包括转写、发言人识别、纪要生成和问答会话创建。

#### 请求参数
- **Content-Type**: `multipart/form-data`
- **file**: 音频文件（支持 wav, mp3, m4a 等格式）

#### 响应示例
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

#### 错误响应
```json
{
  "detail": "处理失败: 错误信息"
}
```

---

### 1.2 查询任务状态

**GET** `/task_status`

查询异步任务的处理状态和进度。

#### 请求参数
- **task_id** (string): 任务ID

#### 响应示例
```json
{
  "status": "processing",
  "progress": 50,
  "eta": 120.5
}
```

#### 状态说明
- `pending`: 任务等待中
- `processing`: 处理中
- `done`: 完成
- `error`: 错误

---

### 1.3 获取任务结果

**GET** `/task_result`

获取已完成任务的处理结果。

#### 请求参数
- **task_id** (string): 任务ID

#### 成功响应示例
```json
{
  "status": "done",
  "result": {
    "transcript": "完整转写文本...",
    "cleaned": "规整后的会议内容...",
    "minutes": "会议纪要...",
    "speaker_count": 3,
    "meeting_name": "AI技术讨论会",
    "chat_available": true
  }
}
```

---

## 2. 会议问答接口

### 2.1 向会议内容提问

**POST** `/meeting/ask`

基于会议内容和纪要向AI助手提问，支持连续对话。

#### 请求体
```json
{
  "task_id": "任务ID",
  "question": "用户问题"
}
```

#### 成功响应
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "answer": "基于会议内容的AI回答...",
    "question": "用户原问题",
    "conversation_count": 5
  }
}
```

#### 错误响应
```json
{
  "code": 1,
  "msg": "会话不存在，请先完成会议处理",
  "data": null
}
```

#### 使用示例
```bash
curl -X POST http://localhost:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "这次会议的主要决策是什么？"
  }'
```

---

### 2.2 获取对话历史

**GET** `/meeting/chat/history`

获取指定任务的完整对话历史记录。

#### 请求参数
- **task_id** (string): 任务ID

#### 成功响应
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "conversation_count": 3,
    "conversations": [
      {
        "timestamp": "2024-12-30T10:30:45.123456",
        "question": "这次会议的主要决策是什么？",
        "answer": "根据会议内容，主要决策包括..."
      }
    ],
    "created_at": "2024-12-30T10:00:00.000000"
  }
}
```

#### 使用示例
```bash
curl "http://localhost:8080/meeting/chat/history?task_id=550e8400-e29b-41d4-a716-446655440000"
```

---

### 2.3 清空对话历史

**DELETE** `/meeting/chat/clear`

清空指定任务的所有对话历史记录。

#### 请求参数
- **task_id** (string): 任务ID

#### 成功响应
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message": "对话历史已清空"
  }
}
```

#### 使用示例
```bash
curl -X DELETE "http://localhost:8080/meeting/chat/clear?task_id=550e8400-e29b-41d4-a716-446655440000"
```

---

### 2.4 检查会话状态

**GET** `/meeting/chat/status`

检查指定任务的问答会话是否可用及基本信息。

#### 请求参数
- **task_id** (string): 任务ID

#### 会话存在时的响应
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "available": true,
    "conversation_count": 5,
    "created_at": "2024-12-30T10:00:00.000000"
  }
}
```

#### 会话不存在时的响应
```json
{
  "code": 1,
  "msg": "会话不存在",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "available": false
  }
}
```

---

## 3. 完整使用流程

### 步骤1: 上传音频文件
```bash
curl -X POST http://localhost:8080/audio2summary_async \
  -F "file=@meeting_audio.wav"
```

响应获得 `task_id`

### 步骤2: 轮询任务状态
```bash
curl "http://localhost:8000/task_status?task_id=YOUR_TASK_ID"
```

等待 `status` 变为 `done`

### 步骤3: 获取处理结果
```bash
curl "http://localhost:8000/task_result?task_id=YOUR_TASK_ID"
```

确认 `chat_available` 为 `true`

### 步骤4: 开始问答
```bash
curl -X POST http://localhost:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "YOUR_TASK_ID",
    "question": "会议的主要议题是什么？"
  }'
```

### 步骤5: 连续对话
继续使用相同的 `task_id` 提问，系统会自动维护对话上下文。

---

## 4. 错误码说明

### HTTP 状态码
- `200`: 请求成功
- `404`: 资源不存在（如任务ID不存在）
- `500`: 服务器内部错误

### 业务错误码
- `code: 0`: 成功
- `code: 1`: 业务逻辑错误（如会话不存在、API调用失败等）

---

## 5. 注意事项

1. **会话生命周期**: 问答会话在服务重启后会丢失，建议保存重要的对话记录
2. **并发限制**: 音频处理为CPU密集型任务，建议控制并发请求数量
3. **文件大小**: 建议音频文件不超过100MB，处理时间与文件大小成正比
4. **API调用频率**: DeepSeek API有调用频率限制，避免过于频繁的问答请求
5. **超时设置**: 长音频处理可能需要几分钟时间，请设置合适的超时时间

---

## 6. SDK 示例

### Python 客户端示例
```python
import requests
import time

class ConferenceAssistantClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_audio(self, file_path):
        """上传音频文件"""
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/audio2summary_async",
                files={"file": f}
            )
        return response.json()["task_id"]
    
    def wait_for_completion(self, task_id, timeout=300):
        """等待任务完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.base_url}/task_status",
                params={"task_id": task_id}
            )
            status = response.json()["status"]
            if status == "done":
                return True
            elif status == "error":
                return False
            time.sleep(5)
        return False
    
    def get_result(self, task_id):
        """获取处理结果"""
        response = requests.get(
            f"{self.base_url}/task_result",
            params={"task_id": task_id}
        )
        return response.json()["result"]
    
    def ask_question(self, task_id, question):
        """向会议内容提问"""
        response = requests.post(
            f"{self.base_url}/meeting/ask",
            json={"task_id": task_id, "question": question}
        )
        return response.json()

# 使用示例
client = ConferenceAssistantClient()

# 1. 上传并处理音频
task_id = client.upload_audio("meeting.wav")
print(f"任务ID: {task_id}")

# 2. 等待处理完成
if client.wait_for_completion(task_id):
    # 3. 获取结果
    result = client.get_result(task_id)
    print(f"会议主题: {result['meeting_name']}")
    print(f"发言人数: {result['speaker_count']}")
    
    # 4. 开始问答
    if result['chat_available']:
        answer = client.ask_question(task_id, "这次会议的主要决策是什么？")
        print(f"AI回答: {answer['data']['answer']}")
```

---

## 7. 技术支持

如有问题，请检查：
1. DeepSeek API Key 是否正确配置
2. 服务是否正常启动
3. 音频文件格式是否支持
4. 网络连接是否正常

更多技术细节请参考项目源码和开发文档。