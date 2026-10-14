# 会议音频转写与纪要自动化系统 API 文档（异步处理专用）

---

## 目录
1. [接口概览](#接口概览)
2. [请求参数说明](#请求参数说明)
3. [接口详细说明](#接口详细说明)
4. [接口调用示例](#接口调用示例)
5. [前端集成建议](#前端集成建议)
6. [常见问题FAQ](#常见问题faq)
7. [错误码说明](#错误码说明)

---

## 接口概览

本系统专为**2小时及以上长音频**设计，采用异步处理+进度查询机制，保证大文件处理稳定、用户体验友好。

| 接口名称         | 方法 | 路径                    | 说明                     |
|------------------|------|-------------------------|--------------------------|
| 上传音频-异步    | POST | /audio2summary_async    | 上传音频，返回任务ID     |
| 查询进度         | GET  | /task_status            | 查询任务进度、剩余时间   |
| 获取结果         | GET  | /task_result            | 获取最终识别与纪要结果   |

---

## 请求参数说明

### /audio2summary_async
| 参数名 | 类型   | 必填 | 说明           |
|--------|--------|------|----------------|
| file   | File   | 是   | 音频文件（mp3/wav/m4a/flac/ogg）|

### /task_status & /task_result
| 参数名 | 类型   | 必填 | 说明           |
|--------|--------|------|----------------|
| task_id| string | 是   | 任务ID（上传接口返回）|

---

## 接口详细说明

### 1. 上传音频-异步 `/audio2summary_async`
- **方法**：POST
- **请求类型**：multipart/form-data
- **参数**：file（音频文件）
- **返回**：
```json
{
  "task_id": "xxxx-xxxx-xxxx",
  "status": "pending"
}
```
- **说明**：上传后立即返回任务ID，后续用此ID查询进度和结果。

### 2. 查询进度 `/task_status`
- **方法**：GET
- **参数**：task_id（URL参数）
- **返回**：
```json
{
  "status": "processing",
  "progress": 10,
  "result": null,
  "error": null,
  "start_time": 1752571255.1851785,
  "eta": 0
}
```
| 字段        | 类型    | 说明                                 |
|-------------|---------|--------------------------------------|
| status      | string  | 任务状态（processing/done/error）    |
| progress    | int     | 当前进度百分比（0-100）              |
| result      | object/null | 结果数据体（处理中为 null，完成时有结果）|
| error       | string/null | 错误信息（如有）                  |
| start_time  | float   | 任务开始时间（Unix时间戳）           |
| eta         | int     | 预计剩余秒数                        |

### 3. 获取结果 `/task_result`
- **方法**：GET
- **参数**：task_id（URL参数）
- **返回**：
- 处理中：
```json
{
  "status": "processing",
  "progress": 40
}
```
- 完成：
```json
{
  "status": "done",
  "result": {
    "transcript": "...",
    "cleaned": "...",
    "minutes": "..."
  }
}
```
- 错误：
```json
{
  "status": "error",
  "progress": 100,
  "error": "详细错误信息"
}
```
| 字段         | 类型   | 说明                         |
|--------------|--------|------------------------------|
| status       | string | 任务状态（done/processing/error）|
| progress     | int    | 当前进度百分比（0-100）      |
| result       | object | 结果数据体（见下表）         |
| error        | string | 错误信息（如有）             |

#### result 字段说明
| 字段         | 类型   | 说明                         |
|--------------|--------|------------------------------|
| transcript   | string | 原始转写文本（Markdown格式） |
| cleaned      | string | 规整后文本（Markdown格式）   |
| minutes      | string | 会议纪要（Markdown格式）     |

---

## 接口调用示例

### curl 示例

#### 上传音频（异步处理）
```bash
curl -X POST "http://127.0.0.1:8080/audio2summary_async" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@会议录音样本.mp3;type=audio/mpeg"
```

#### 查询进度
```bash
curl -X GET "http://127.0.0.1:8080/task_status?task_id=xxxx-xxxx-xxxx"
```

#### 获取结果
```bash
curl -X GET "http://127.0.0.1:8080/task_result?task_id=xxxx-xxxx-xxxx"
```

### Postman/Apifox 配置
- 上传接口：POST，Body类型为form-data，参数名file，类型为文件
- 查询进度/结果接口：GET，参数task_id放在URL参数

---

## 前端集成建议
1. 用户上传音频，调用 `/audio2summary_async`，获取 `task_id`
2. 前端定时轮询 `/task_status?task_id=xxx`，展示进度条、阶段描述和预计剩余时间
3. 进度到100%后，自动请求 `/task_result?task_id=xxx`，展示会议内容和纪要
4. 可提供“历史任务”功能，方便用户随时查结果
5. 所有文本结果均为 Markdown 格式，前端请用 Markdown 渲染组件美观展示
6. 错误时请友好提示 `error` 字段内容

---

## 常见问题FAQ

**Q1：为什么上传后长时间无响应？**
- 处理超长音频需较长时间，请耐心等待。可通过进度接口实时查看进度和剩余时间。

**Q2：为什么返回 error？**
- 可能原因：音频格式不支持、模型加载失败、服务器资源不足等。请查看 `error` 字段详细信息。

**Q3：支持哪些音频格式？**
- 支持 mp3、wav、m4a、flac、ogg。

**Q4：接口支持并发吗？**
- 支持，多个任务互不影响，但受限于服务器硬件资源。

**Q5：如何保证任务不丢失？**
- 只要服务未重启，task_id 可多次查询进度和结果。建议前端保存历史 task_id。

---

## 错误码说明
| code | 说明           |
|------|----------------|
| 0    | 成功           |
| 500  | 服务器处理失败 |
| 400  | 请求参数错误   |
| 404  | 任务不存在     |

---

如有问题请联系项目开发者，或查阅上述文档。祝对接顺利！ 