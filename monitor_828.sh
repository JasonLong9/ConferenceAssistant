#!/bin/bash

echo "=== 开始监控8.28.mp3处理进度 ==="
echo "任务ID: 2bf95577-cf3b-4d7e-a57b-dbc99cac0fbe"
echo "音频时长: 22分31秒"
echo "预期时间段: 0-5,5-10,10-15,15-20,20-22分钟"
echo ""

TASK_ID="2bf95577-cf3b-4d7e-a57b-dbc99cac0fbe"

for i in {1..30}; do
    echo "=== 检查 $i/30 ($(date)) ==="
    
    curl -s "http://localhost:8080/task_status?task_id=$TASK_ID" | python -c "
import json,sys
data = json.load(sys.stdin)
status = data.get('status')
progress = data.get('progress', 0)
stage = data.get('stage', '未知')
error = data.get('error', '无')

print(f'状态: {status}, 进度: {progress}%, 阶段: {stage}')
print(f'错误: {error}')

if status == 'done':
    print('*** 处理完成！ ***')
    exit(0)
elif status == 'error':
    print('*** 处理出错！ ***')
    exit(1)
else:
    exit(2)
"
    
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "*** 8.28.mp3处理完成！开始获取结果 ***"
        break
    elif [ $EXIT_CODE -eq 1 ]; then
        echo "*** 处理出错，停止监控 ***"
        break
    fi
    
    if [ $i -lt 30 ]; then
        echo "等待60秒..."
        sleep 60
    fi
done