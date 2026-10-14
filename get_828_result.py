#!/usr/bin/env python3
"""
获取8.28.mp3的完整处理结果并更新文档
"""

import requests
import json
import time
from datetime import datetime

TASK_ID = "2bf95577-cf3b-4d7e-a57b-dbc99cac0fbe"
REPORT_FILE = "8.28.MP3完整处理报告_20250905_024500.md"

def check_task_status():
    """检查任务状态"""
    try:
        response = requests.get(f"http://localhost:8080/task_status?task_id={TASK_ID}")
        return response.json()
    except Exception as e:
        print(f"检查状态失败: {e}")
        return None

def get_task_result():
    """获取任务结果"""
    try:
        response = requests.get(f"http://localhost:8080/task_result?task_id={TASK_ID}")
        return response.json()
    except Exception as e:
        print(f"获取结果失败: {e}")
        return None

def update_report_with_result(result_data):
    """使用结果更新报告"""
    try:
        # 读取现有报告
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新时间
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        
        if result_data and result_data.get("status") == "done":
            result = result_data.get("result", {})
            
            # 准备新的内容部分
            transcript_section = f"""## 二、声纹识别后的规整文本

**发言人数量**: {result.get('speaker_count', '未知')}人
**会议名称**: {result.get('meeting_name', '未知')}

```
{result.get('cleaned', '处理中...')}
```

---

"""
            
            minutes_section = f"""## 三、会议纪要内容

{result.get('minutes', '处理中...')}

---

"""
            
            # 替换文档中的占位符
            content = content.replace("*(处理中，将在完成后更新)*", "")
            content = content.replace("## 三、声纹识别后的规整文本\n\n*(处理中，将在完成后更新)*\n\n---\n\n## 四、会议纪要内容\n\n### 预期结构\n会议纪要将包含以下部分：\n1. **会议基本信息** - 主题、时间、参与者\n2. **讨论要点** - 按发言人整理的关键内容\n3. **重要决策** - 会议中做出的决定和结论\n4. **行动项** - 后续需要执行的任务\n5. **重要时间点讨论摘要** - 基于实际22分钟时长的5个时间段\n\n*(详细内容将在处理完成后更新)*\n\n---\n\n## 五、系统改进确认", 
                            transcript_section + minutes_section + "## 四、系统改进确认")
            
            # 更新处理状态
            status_update = f"""### 进度跟踪
- ✅ 文件上传 (20.6MB)
- ✅ 时长检测 (22分31秒) 
- ✅ 动态分段生成 (0-5,5-10,10-15,15-20,20-22分钟)
- ✅ 音频转写完成
- ✅ 声纹识别完成 (识别到{result.get('speaker_count', '未知')}个发言人)
- ✅ 文本规整完成
- ✅ 会议纪要生成完成(使用动态时间段)
- ✅ 智能问答会话创建{'成功' if result.get('chat_available') else '失败'}

**处理完成时间**: {current_time}

---

"""
            
            content = content.replace("### 进度跟踪\n- 开始时间: 2025年9月5日 02:45:00\n- 当前进度: 等待处理开始...", status_update.strip())
            
            # 更新最后更新时间
            content = content.replace("**最后更新时间**: 2025年9月5日 02:45:00", f"**最后更新时间**: {current_time}")
            
            # 添加完成标记
            content = content.replace("*(持续跟踪中，完成后更新完整结果...)*", f"✅ **处理完成！** 于 {current_time}")
            
        else:
            # 如果处理失败或还在进行中，更新状态
            content = content.replace("**最后更新时间**: 2025年9月5日 02:45:00", f"**最后更新时间**: {current_time}")
            if result_data and result_data.get("status") == "error":
                error_msg = result_data.get("error", "未知错误")
                content = content.replace("*(持续跟踪中，完成后更新完整结果...)*", f"❌ **处理失败**: {error_msg}")
        
        # 保存更新后的报告
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"报告已更新: {REPORT_FILE}")
        
    except Exception as e:
        print(f"更新报告失败: {e}")

def main():
    """主函数"""
    print(f"开始监控8.28.mp3处理进度...")
    print(f"任务ID: {TASK_ID}")
    print(f"报告文件: {REPORT_FILE}")
    print()
    
    # 持续监控直到完成
    for i in range(30):  # 最多检查30次，每次间隔60秒
        print(f"=== 检查 {i+1}/30 ({datetime.now().strftime('%H:%M:%S')}) ===")
        
        status = check_task_status()
        if status:
            print(f"状态: {status.get('status')}, 进度: {status.get('progress', 0)}%, 阶段: {status.get('stage', '未知')}")
            
            if status.get('status') == 'done':
                print("*** 8.28.mp3处理完成！获取完整结果 ***")
                result = get_task_result()
                if result:
                    update_report_with_result(result)
                    print("报告已更新完成！")
                else:
                    print("获取结果失败")
                break
                
            elif status.get('status') == 'error':
                print("*** 处理出错！ ***")
                update_report_with_result(status)
                break
                
        if i < 29:
            print("等待60秒...")
            time.sleep(60)
    else:
        print("监控超时，请手动检查")

if __name__ == "__main__":
    main()