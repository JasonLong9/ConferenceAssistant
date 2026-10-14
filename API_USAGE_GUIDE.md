# ConferenceAssistant API 使用指南

## 🚨 解决 "Field required" 错误

如果你在调用 `/meeting/ask` 接口时遇到以下错误：

```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["body"],
            "msg": "Field required",
            "input": null
        }
    ]
}
```

这表示**请求体(body)缺失或格式不正确**。

## ✅ 正确的调用方式

### 1. 使用curl命令

```bash
curl -X POST http://127.0.0.1:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "your-actual-task-id",
    "question": "这次会议讨论了什么内容？"
  }'
```

### 2. 使用Python requests

```python
import requests

url = "http://127.0.0.1:8080/meeting/ask"
payload = {
    "task_id": "your-actual-task-id",
    "question": "这次会议讨论了什么内容？"
}

response = requests.post(url, json=payload)
print(response.json())
```

### 3. 使用JavaScript fetch

```javascript
const response = await fetch('http://127.0.0.1:8080/meeting/ask', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        task_id: 'your-actual-task-id',
        question: '这次会议讨论了什么内容？'
    })
});

const result = await response.json();
console.log(result);
```

## ❌ 常见错误及解决方案

### 错误1: 缺少Content-Type头
```bash
# 错误的调用方式
curl -X POST http://127.0.0.1:8080/meeting/ask \
  -d '{"task_id":"xxx","question":"yyy"}'

# 正确的调用方式 - 添加Content-Type
curl -X POST http://127.0.0.1:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d '{"task_id":"xxx","question":"yyy"}'
```

### 错误2: 使用form-data而不是JSON
```bash
# 错误的调用方式
curl -X POST http://127.0.0.1:8080/meeting/ask \
  -F "task_id=xxx" \
  -F "question=yyy"

# 正确的调用方式 - 使用JSON
curl -X POST http://127.0.0.1:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d '{"task_id":"xxx","question":"yyy"}'
```

### 错误3: 缺少必需字段
```bash
# 错误 - 缺少question字段
curl -X POST http://127.0.0.1:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d '{"task_id":"xxx"}'

# 正确 - 包含所有必需字段
curl -X POST http://127.0.0.1:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d '{"task_id":"xxx","question":"yyy"}'
```

## 📋 完整的API调用流程

### 步骤1: 上传音频文件
```bash
curl -X POST http://127.0.0.1:8080/audio2summary_async \
  -F "file=@your_audio.wav"
```

**响应示例:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

### 步骤2: 查询处理状态
```bash
curl "http://127.0.0.1:8080/task_status?task_id=550e8400-e29b-41d4-a716-446655440000"
```

**等待status变为"done"**

### 步骤3: 获取处理结果
```bash
curl "http://127.0.0.1:8080/task_result?task_id=550e8400-e29b-41d4-a716-446655440000"
```

**确认chat_available为true**

### 步骤4: 开始问答
```bash
curl -X POST http://127.0.0.1:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "这次会议的主要议题是什么？"
  }'
```

## 🔍 接口响应说明

### 成功响应
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "answer": "根据会议内容，主要议题包括...",
    "question": "这次会议的主要议题是什么？",
    "conversation_count": 1
  }
}
```

### 错误响应示例

#### 1. 任务不存在
```json
{
  "code": 1,
  "msg": "任务不存在，请先完成音频处理",
  "data": null
}
```

#### 2. 任务未完成
```json
{
  "code": 1,
  "msg": "任务尚未完成，当前状态: processing",
  "data": null
}
```

#### 3. 参数为空
```json
{
  "code": 1,
  "msg": "task_id不能为空",
  "data": null
}
```

## 🧪 测试API接口

你可以使用提供的测试脚本来验证接口：

```bash
python test_api.py
```

这将测试各种边界情况和错误处理。

## 📝 调试提示

1. **检查服务是否运行**: 
   ```bash
   curl http://127.0.0.1:8080/
   ```

2. **查看API文档**: 
   访问 http://127.0.0.1:8080/docs

3. **查看服务日志**: 
   启动服务时的控制台输出

4. **使用正确的端口**: 
   确保使用8080端口，不是8000

## 🔧 故障排除

### 问题: 连接被拒绝
**解决**: 确保服务已启动
```bash
uvicorn web_service:app --reload --host 0.0.0.0 --port 8080
```

### 问题: 任务不存在
**解决**: 确保先上传音频并等待处理完成

### 问题: JSON解析错误
**解决**: 检查JSON格式是否正确，使用JSON验证器

### 问题: 405 Method Not Allowed
**解决**: 确保使用POST方法，不是GET

---

遵循以上指南，你应该能够成功调用 `/meeting/ask` 接口了！