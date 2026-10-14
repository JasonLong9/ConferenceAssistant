from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import threading
from datetime import datetime
from core import MeetingProcessor
from async_task_manager import TASKS, generate_task_id, set_task_status

app = FastAPI()
processor = MeetingProcessor()

@app.post("/audio2summary_async")
async def audio2summary_async(file: UploadFile = File(...)):
    temp_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    task_id = generate_task_id()
    set_task_status(task_id, "pending", 0, result=None, error=None)
    def process_task():
        try:
            set_task_status(task_id, "processing", 10, result=None, error=None)  # 上传完成
            # 使用新的带声纹识别的处理方法
            result_data = processor.process_with_speaker_id(temp_path, output_dir="temp_output")
            set_task_status(task_id, "processing", 90, result=None, error=None)  # 处理完成
            
            result = {
                "transcript": result_data["transcript"],
                "cleaned": result_data["cleaned"], 
                "minutes": result_data["minutes"],
                "speaker_count": result_data["speaker_count"],
                "meeting_name": result_data["meeting_name"]
            }
            set_task_status(task_id, "done", 100, result=result, error=None)
        except Exception as e:
            set_task_status(task_id, "error", 100, result=None, error=str(e))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    threading.Thread(target=process_task, daemon=True).start()
    return {"task_id": task_id, "status": "pending"}

@app.get("/task_status")
def task_status(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TASKS[task_id]

@app.get("/task_result")
def task_result(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="任务不存在")
    task = TASKS[task_id]
    if task["status"] != "done":
        return {"status": task["status"], "progress": task["progress"]}
    return {"status": "done", "result": task["result"]} 