# ConferenceAssistant 使用示例

本文档提供 ConferenceAssistant 各种使用场景的详细示例。

## 目录
1. [快速开始](#快速开始)
2. [命令行使用](#命令行使用)
3. [Web API使用](#web-api使用)
4. [Python客户端示例](#python客户端示例)
5. [高级用法](#高级用法)
6. [实际场景应用](#实际场景应用)

---

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置DeepSeek API Key
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env

# 启动Web服务
uvicorn web_service:app --reload
```

### 2. 第一次使用

```bash
# 方式1: 命令行处理
python main.py meeting_audio.wav --meeting_name "项目讨论会"

# 方式2: Web API处理
curl -X POST http://localhost:8080/audio2summary_async \
  -F "file=@meeting_audio.wav"
```

---

## 命令行使用

### 基本音频转写

```bash
# 单个文件处理
python main.py audio1.wav

# 批量处理
python main.py audio1.wav audio2.mp3 audio3.m4a

# 指定会议名称
python main.py meeting.wav --meeting_name "产品规划会议"

# 指定输出目录
python main.py meeting.wav --output_dir "./meeting_outputs"

# 指定处理设备
python main.py meeting.wav --device cuda  # GPU
python main.py meeting.wav --device cpu   # CPU
```

### 输出结果

命令行处理完成后会生成：
```
outputs/
├── 会议内容_产品规划会议_20241230_143022.md    # 转写内容
└── 会议纪要_产品规划会议_20241230_143022.md    # 会议纪要
```

---

## Web API使用

### 1. 异步音频处理

```bash
# 上传音频文件
curl -X POST http://localhost:8080/audio2summary_async \
  -F "file=@meeting_recording.wav" \
  -o response.json

# 获取task_id
TASK_ID=$(cat response.json | jq -r '.task_id')
echo "任务ID: $TASK_ID"
```

### 2. 监控处理进度

```bash
# 查看处理状态
curl "http://localhost:8080/task_status?task_id=$TASK_ID"

# 持续监控直到完成
while true; do
    STATUS=$(curl -s "http://localhost:8080/task_status?task_id=$TASK_ID" | jq -r '.status')
    PROGRESS=$(curl -s "http://localhost:8080/task_status?task_id=$TASK_ID" | jq -r '.progress')
    echo "状态: $STATUS, 进度: $PROGRESS%"
    
    if [ "$STATUS" = "done" ] || [ "$STATUS" = "error" ]; then
        break
    fi
    sleep 5
done
```

### 3. 获取处理结果

```bash
# 获取完整结果
curl "http://localhost:8080/task_result?task_id=$TASK_ID" | jq '.'

# 提取特定字段
curl -s "http://localhost:8080/task_result?task_id=$TASK_ID" | jq -r '.result.meeting_name'
curl -s "http://localhost:8080/task_result?task_id=$TASK_ID" | jq -r '.result.speaker_count'
```

### 4. 会议问答

```bash
# 检查问答会话状态
curl "http://localhost:8080/meeting/chat/status?task_id=$TASK_ID"

# 提问
curl -X POST http://localhost:8080/meeting/ask \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"$TASK_ID\",\"question\":\"这次会议讨论了哪些主要议题？\"}"

# 连续对话示例
questions=(
    "参会人员有哪些？"
    "会议做了什么重要决定？"
    "下一步的行动计划是什么？"
    "预算安排如何？"
    "时间安排是怎样的？"
)

for question in "${questions[@]}"; do
    echo "问题: $question"
    response=$(curl -s -X POST http://localhost:8080/meeting/ask \
      -H "Content-Type: application/json" \
      -d "{\"task_id\":\"$TASK_ID\",\"question\":\"$question\"}")
    
    answer=$(echo $response | jq -r '.data.answer')
    echo "回答: $answer"
    echo "---"
    sleep 2
done
```

---

## Python客户端示例

### 基础客户端类

```python
import requests
import time
import json
from typing import Optional, Dict, Any

class ConferenceAssistantClient:
    """ConferenceAssistant Python客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def upload_audio(self, file_path: str) -> str:
        """上传音频文件并返回任务ID"""
        with open(file_path, 'rb') as f:
            response = self.session.post(
                f"{self.base_url}/audio2summary_async",
                files={"file": f}
            )
        response.raise_for_status()
        return response.json()["task_id"]
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        response = self.session.get(
            f"{self.base_url}/task_status",
            params={"task_id": task_id}
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, task_id: str, timeout: int = 600, 
                          callback=None) -> bool:
        """等待任务完成，支持进度回调"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_info = self.get_task_status(task_id)
            status = status_info["status"]
            progress = status_info.get("progress", 0)
            eta = status_info.get("eta", 0)
            
            if callback:
                callback(status, progress, eta)
            
            if status == "done":
                return True
            elif status == "error":
                error = status_info.get("error", "未知错误")
                raise Exception(f"任务处理失败: {error}")
            
            time.sleep(5)
        
        raise TimeoutError(f"任务超时（{timeout}秒）")
    
    def get_result(self, task_id: str) -> Dict[str, Any]:
        """获取处理结果"""
        response = self.session.get(
            f"{self.base_url}/task_result",
            params={"task_id": task_id}
        )
        response.raise_for_status()
        return response.json()["result"]
    
    def ask_question(self, task_id: str, question: str) -> Dict[str, Any]:
        """向会议内容提问"""
        response = self.session.post(
            f"{self.base_url}/meeting/ask",
            json={"task_id": task_id, "question": question}
        )
        response.raise_for_status()
        return response.json()
    
    def get_chat_history(self, task_id: str) -> Dict[str, Any]:
        """获取对话历史"""
        response = self.session.get(
            f"{self.base_url}/meeting/chat/history",
            params={"task_id": task_id}
        )
        response.raise_for_status()
        return response.json()
    
    def clear_chat_history(self, task_id: str) -> bool:
        """清空对话历史"""
        response = self.session.delete(
            f"{self.base_url}/meeting/chat/clear",
            params={"task_id": task_id}
        )
        response.raise_for_status()
        result = response.json()
        return result["code"] == 0
```

### 完整使用示例

```python
def main():
    """完整的会议处理和问答示例"""
    client = ConferenceAssistantClient()
    
    # 1. 上传音频文件
    print("📁 正在上传音频文件...")
    audio_file = "meeting_recording.wav"
    task_id = client.upload_audio(audio_file)
    print(f"✅ 上传完成，任务ID: {task_id}")
    
    # 2. 等待处理完成（带进度显示）
    print("⏳ 正在处理音频...")
    
    def progress_callback(status, progress, eta):
        if eta > 0:
            print(f"📊 {status}: {progress}% (预计剩余: {eta:.1f}秒)")
        else:
            print(f"📊 {status}: {progress}%")
    
    try:
        success = client.wait_for_completion(task_id, timeout=600, 
                                           callback=progress_callback)
        if success:
            print("✅ 音频处理完成！")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return
    
    # 3. 获取处理结果
    print("\n📋 获取处理结果...")
    result = client.get_result(task_id)
    
    print(f"🎯 会议主题: {result['meeting_name']}")
    print(f"👥 发言人数: {result['speaker_count']}")
    print(f"💬 问答可用: {'是' if result['chat_available'] else '否'}")
    
    print(f"\n📝 会议纪要预览:")
    print(result["minutes"][:300] + "..." if len(result["minutes"]) > 300 else result["minutes"])
    
    # 4. 智能问答
    if result['chat_available']:
        print("\n🤖 开始智能问答...")
        
        # 预设问题列表
        questions = [
            "这次会议的主要议题是什么？",
            "会议中做出了哪些重要决定？", 
            "有哪些具体的行动项或任务分配？",
            "会议中提到的时间节点有哪些？",
            "预算或资源分配情况如何？"
        ]
        
        conversation_data = []
        
        for i, question in enumerate(questions, 1):
            print(f"\n❓ 问题 {i}: {question}")
            
            try:
                response = client.ask_question(task_id, question)
                if response["code"] == 0:
                    answer = response["data"]["answer"]
                    print(f"🎯 回答: {answer}")
                    
                    conversation_data.append({
                        "question": question,
                        "answer": answer
                    })
                else:
                    print(f"❌ 问答失败: {response['msg']}")
                    
            except Exception as e:
                print(f"❌ 问答出错: {e}")
            
            time.sleep(1)  # 避免请求过于频繁
        
        # 5. 导出对话记录
        print("\n📄 导出对话记录...")
        try:
            chat_history = client.get_chat_history(task_id)
            if chat_history["code"] == 0:
                # 保存为JSON文件
                output_file = f"chat_history_{task_id[:8]}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(chat_history["data"], f, 
                             ensure_ascii=False, indent=2)
                print(f"✅ 对话记录已保存到: {output_file}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
        
        # 6. 生成总结报告
        print("\n📊 生成总结报告...")
        generate_summary_report(result, conversation_data, task_id)

def generate_summary_report(result: Dict, conversations: list, task_id: str):
    """生成会议总结报告"""
    report = f"""
# 会议处理总结报告

**任务ID**: {task_id}
**处理时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**会议主题**: {result['meeting_name']}
**发言人数**: {result['speaker_count']}

## 会议纪要
{result['minutes']}

## 问答摘要
"""
    
    for i, conv in enumerate(conversations, 1):
        report += f"""
### {i}. {conv['question']}
{conv['answer']}
"""
    
    # 保存报告
    report_file = f"meeting_report_{task_id[:8]}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 总结报告已保存到: {report_file}")

if __name__ == "__main__":
    main()
```

### 批量处理示例

```python
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

def batch_process_meetings():
    """批量处理多个会议录音"""
    client = ConferenceAssistantClient()
    
    # 扫描音频文件
    audio_dir = Path("./meeting_audios")
    audio_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.mp3"))
    
    print(f"📁 发现 {len(audio_files)} 个音频文件")
    
    # 批量上传
    tasks = []
    for audio_file in audio_files:
        print(f"📤 上传: {audio_file.name}")
        task_id = client.upload_audio(str(audio_file))
        tasks.append({
            "task_id": task_id,
            "filename": audio_file.name,
            "filepath": str(audio_file)
        })
    
    # 等待所有任务完成
    results = []
    for task in tasks:
        print(f"⏳ 等待处理: {task['filename']}")
        try:
            client.wait_for_completion(task["task_id"], timeout=1800)
            result = client.get_result(task["task_id"])
            
            results.append({
                "文件名": task["filename"],
                "会议主题": result["meeting_name"],
                "发言人数": result["speaker_count"],
                "处理状态": "成功",
                "任务ID": task["task_id"]
            })
            
        except Exception as e:
            results.append({
                "文件名": task["filename"],
                "会议主题": "处理失败",
                "发言人数": 0,
                "处理状态": str(e),
                "任务ID": task["task_id"]
            })
    
    # 生成处理报告
    df = pd.DataFrame(results)
    report_file = f"batch_processing_report_{int(time.time())}.xlsx"
    df.to_excel(report_file, index=False)
    print(f"📊 批量处理报告已保存到: {report_file}")
    
    return results

# 运行批量处理
if __name__ == "__main__":
    batch_process_meetings()
```

---

## 高级用法

### 1. 自定义问题模板

```python
class MeetingAnalyzer:
    """会议分析器 - 使用预定义问题模板"""
    
    ANALYSIS_TEMPLATES = {
        "项目会议": [
            "项目的主要目标和里程碑是什么？",
            "当前项目进展如何？",
            "遇到了哪些风险和挑战？", 
            "资源分配和预算情况如何？",
            "下一阶段的具体任务安排？"
        ],
        "产品讨论": [
            "讨论了哪些产品功能？",
            "用户反馈和需求是什么？",
            "技术实现方案如何？",
            "产品发布时间计划？",
            "市场竞争分析结果？"
        ],
        "销售会议": [
            "本期销售业绩如何？",
            "重点客户的跟进情况？",
            "市场机会和挑战分析？",
            "销售策略调整建议？",
            "下期销售目标设定？"
        ]
    }
    
    def __init__(self, client: ConferenceAssistantClient):
        self.client = client
    
    def analyze_meeting(self, task_id: str, meeting_type: str = "项目会议"):
        """根据会议类型进行专项分析"""
        questions = self.ANALYSIS_TEMPLATES.get(meeting_type, 
                                               self.ANALYSIS_TEMPLATES["项目会议"])
        
        analysis_result = {
            "meeting_type": meeting_type,
            "analysis": []
        }
        
        for question in questions:
            try:
                response = self.client.ask_question(task_id, question)
                if response["code"] == 0:
                    analysis_result["analysis"].append({
                        "question": question,
                        "answer": response["data"]["answer"]
                    })
            except Exception as e:
                print(f"分析问题失败: {question} - {e}")
        
        return analysis_result
```

### 2. 实时监控和通知

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MeetingMonitor:
    """会议处理监控和通知"""
    
    def __init__(self, client: ConferenceAssistantClient, 
                 email_config: Dict[str, str]):
        self.client = client
        self.email_config = email_config
    
    def monitor_with_notification(self, task_id: str, 
                                notification_email: str):
        """监控处理进度并发送邮件通知"""
        try:
            # 等待处理完成
            self.client.wait_for_completion(task_id, timeout=1800)
            
            # 获取结果
            result = self.client.get_result(task_id)
            
            # 发送成功通知
            self.send_success_notification(
                notification_email, task_id, result
            )
            
        except Exception as e:
            # 发送失败通知
            self.send_error_notification(
                notification_email, task_id, str(e)
            )
    
    def send_success_notification(self, email: str, task_id: str, result: Dict):
        """发送处理成功通知"""
        subject = f"会议处理完成 - {result['meeting_name']}"
        
        body = f"""
        您的会议录音已处理完成：
        
        任务ID: {task_id}
        会议主题: {result['meeting_name']}
        发言人数: {result['speaker_count']}
        问答功能: {'可用' if result['chat_available'] else '不可用'}
        
        您现在可以开始向会议内容提问了。
        """
        
        self.send_email(email, subject, body)
    
    def send_email(self, to_email: str, subject: str, body: str):
        """发送邮件"""
        # 邮件发送实现...
        pass
```

---

## 实际场景应用

### 场景1: 企业会议记录自动化

```python
def enterprise_meeting_workflow():
    """企业会议记录自动化流程"""
    client = ConferenceAssistantClient()
    
    # 1. 处理会议录音
    meeting_file = "board_meeting_20241230.wav"
    print("🏢 开始处理董事会会议录音...")
    
    task_id = client.upload_audio(meeting_file)
    client.wait_for_completion(task_id)
    result = client.get_result(task_id)
    
    # 2. 生成标准会议纪要
    print("📋 生成会议纪要...")
    meeting_minutes = result["minutes"]
    
    # 3. 提取关键信息
    key_questions = [
        "会议通过了哪些决议？",
        "各部门的业绩报告要点是什么？",
        "需要跟进的行动项有哪些？",
        "下次会议的时间安排？"
    ]
    
    key_info = {}
    for question in key_questions:
        response = client.ask_question(task_id, question)
        if response["code"] == 0:
            key_info[question] = response["data"]["answer"]
    
    # 4. 生成正式会议纪要文档
    generate_formal_minutes(result, key_info)
    
    # 5. 分发给相关人员
    distribute_minutes(meeting_minutes, key_info)

def generate_formal_minutes(result: Dict, key_info: Dict):
    """生成正式的会议纪要文档"""
    template = f"""
# {result['meeting_name']} 会议纪要

**会议时间**: {time.strftime('%Y年%m月%d日')}
**参会人数**: {result['speaker_count']}人
**记录方式**: AI自动生成

## 会议内容概要
{result['minutes']}

## 关键信息提取
"""
    
    for question, answer in key_info.items():
        template += f"\n### {question}\n{answer}\n"
    
    template += """
---
*本纪要由ConferenceAssistant自动生成，如有疑问请联系会议组织者*
"""
    
    # 保存为Word文档或PDF
    output_file = f"formal_minutes_{int(time.time())}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"📄 正式会议纪要已生成: {output_file}")
```

### 场景2: 客户访谈分析

```python
def customer_interview_analysis():
    """客户访谈分析流程"""
    client = ConferenceAssistantClient()
    
    # 批量处理多个客户访谈
    interview_files = [
        "customer_interview_1.wav",
        "customer_interview_2.wav", 
        "customer_interview_3.wav"
    ]
    
    all_insights = []
    
    for i, interview_file in enumerate(interview_files, 1):
        print(f"🎤 处理第 {i} 个客户访谈...")
        
        task_id = client.upload_audio(interview_file)
        client.wait_for_completion(task_id)
        result = client.get_result(task_id)
        
        # 针对客户访谈的专项问题
        interview_questions = [
            "客户对我们产品的主要反馈是什么？",
            "客户提到了哪些痛点和需求？",
            "客户对竞品的看法如何？",
            "客户的购买意向和预算情况？",
            "客户建议的产品改进方向？"
        ]
        
        insights = {"客户": f"客户{i}", "访谈分析": {}}
        
        for question in interview_questions:
            response = client.ask_question(task_id, question)
            if response["code"] == 0:
                insights["访谈分析"][question] = response["data"]["answer"]
        
        all_insights.append(insights)
    
    # 生成客户洞察报告
    generate_customer_insights_report(all_insights)

def generate_customer_insights_report(insights_list: list):
    """生成客户洞察报告"""
    report = "# 客户访谈洞察报告\n\n"
    
    # 汇总所有客户反馈
    for customer_insight in insights_list:
        report += f"## {customer_insight['客户']} 访谈分析\n"
        
        for question, answer in customer_insight["访谈分析"].items():
            report += f"### {question}\n{answer}\n\n"
    
    # 保存报告
    report_file = f"customer_insights_{int(time.time())}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📊 客户洞察报告已生成: {report_file}")
```

### 场景3: 培训课程分析

```python
def training_session_analysis():
    """培训课程分析和问答生成"""
    client = ConferenceAssistantClient()
    
    # 处理培训录音
    training_file = "python_training_session.wav"
    print("🎓 处理培训课程录音...")
    
    task_id = client.upload_audio(training_file)
    client.wait_for_completion(task_id)
    result = client.get_result(task_id)
    
    # 生成培训知识点问答
    training_questions = [
        "这次培训的主要知识点有哪些？",
        "学员提出了什么问题？",
        "讲师给出了哪些实用建议？",
        "课程中的代码示例有哪些？",
        "需要课后练习的内容是什么？"
    ]
    
    qa_pairs = []
    for question in training_questions:
        response = client.ask_question(task_id, question)
        if response["code"] == 0:
            qa_pairs.append({
                "Q": question,
                "A": response["data"]["answer"]
            })
    
    # 生成学习资料
    generate_study_materials(result, qa_pairs)

def generate_study_materials(result: Dict, qa_pairs: list):
    """生成学习资料"""
    materials = f"""
# {result['meeting_name']} - 学习资料

## 课程内容总结
{result['minutes']}

## 重点问答
"""
    
    for i, qa in enumerate(qa_pairs, 1):
        materials += f"\n### {i}. {qa['Q']}\n{qa['A']}\n"
    
    materials += """
## 复习建议
请根据以上内容进行复习，并完成相关练习。如有疑问，可以参考录音原文或咨询讲师。
"""
    
    # 保存学习资料
    study_file = f"study_materials_{int(time.time())}.md"
    with open(study_file, 'w', encoding='utf-8') as f:
        f.write(materials)
    
    print(f"📚 学习资料已生成: {study_file}")
```

---

## 错误处理和调试

### 常见错误处理

```python
def robust_meeting_processing(audio_file: str):
    """健壮的会议处理流程"""
    client = ConferenceAssistantClient()
    
    try:
        # 1. 上传音频
        print("📤 上传音频文件...")
        task_id = client.upload_audio(audio_file)
        print(f"✅ 上传成功，任务ID: {task_id}")
        
    except FileNotFoundError:
        print("❌ 音频文件不存在")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请检查服务是否启动")
        return None
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return None
    
    try:
        # 2. 等待处理完成
        print("⏳ 等待处理完成...")
        success = client.wait_for_completion(task_id, timeout=1800)
        
        if not success:
            print("❌ 处理超时")
            return None
            
    except TimeoutError:
        print("❌ 处理超时，请稍后查看任务状态")
        return task_id
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return None
    
    try:
        # 3. 获取结果
        result = client.get_result(task_id)
        print("✅ 处理完成")
        return result
        
    except Exception as e:
        print(f"❌ 获取结果失败: {e}")
        return None

# 使用示例
result = robust_meeting_processing("meeting.wav")
if result:
    print(f"会议主题: {result['meeting_name']}")
else:
    print("处理失败，请检查日志")
```

---

## 性能优化建议

### 1. 并发处理

```python
from concurrent.futures import ThreadPoolExecutor
import time

def concurrent_processing(audio_files: list):
    """并发处理多个音频文件"""
    client = ConferenceAssistantClient()
    
    def process_single_file(audio_file):
        try:
            task_id = client.upload_audio(audio_file)
            client.wait_for_completion(task_id)
            result = client.get_result(task_id)
            return {"file": audio_file, "result": result, "status": "success"}
        except Exception as e:
            return {"file": audio_file, "error": str(e), "status": "error"}
    
    # 限制并发数量避免服务器过载
    max_workers = min(3, len(audio_files))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_single_file, audio_files))
    
    return results

# 使用示例
audio_files = ["meeting1.wav", "meeting2.wav", "meeting3.wav"]
results = concurrent_processing(audio_files)

for result in results:
    if result["status"] == "success":
        print(f"✅ {result['file']}: {result['result']['meeting_name']}")
    else:
        print(f"❌ {result['file']}: {result['error']}")
```

### 2. 缓存和重试机制

```python
import pickle
import hashlib
from pathlib import Path

class CachedMeetingProcessor:
    """带缓存的会议处理器"""
    
    def __init__(self, cache_dir: str = "./cache"):
        self.client = ConferenceAssistantClient()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_file_hash(self, file_path: str) -> str:
        """计算文件哈希值用于缓存键"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def process_with_cache(self, audio_file: str) -> Dict[str, Any]:
        """带缓存的处理流程"""
        file_hash = self.get_file_hash(audio_file)
        cache_file = self.cache_dir / f"{file_hash}.pkl"
        
        # 检查缓存
        if cache_file.exists():
            print(f"📄 使用缓存结果: {audio_file}")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        
        # 处理音频
        print(f"🔄 处理音频: {audio_file}")
        result = self.process_with_retry(audio_file)
        
        # 保存缓存
        if result:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        
        return result
    
    def process_with_retry(self, audio_file: str, max_retries: int = 3) -> Optional[Dict]:
        """带重试的处理流程"""
        for attempt in range(max_retries):
            try:
                task_id = self.client.upload_audio(audio_file)
                self.client.wait_for_completion(task_id)
                return self.client.get_result(task_id)
                
            except Exception as e:
                print(f"⚠️ 第{attempt+1}次尝试失败: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(10)  # 等待后重试
        
        return None

# 使用示例
processor = CachedMeetingProcessor()
result = processor.process_with_cache("meeting.wav")
```

这些示例涵盖了ConferenceAssistant的各种使用场景，从基本的音频处理到复杂的企业级应用。根据您的具体需求选择合适的示例进行修改和使用。