#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConferenceAssistant 改进版 Web 服务 - 专门为8080端口
整合了改进的声纹识别系统
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from datetime import datetime
import threading
from async_task_manager import TASKS, generate_task_id, set_task_status
from meeting_chat import meeting_chat_manager

# 使用改进版核心系统
from core import MeetingProcessor

app = FastAPI()

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = MeetingProcessor()

# 添加根路径用于调试
@app.get("/")
def root():
    return {
        "message": "ConferenceAssistant API (Improved Speaker ID)",
        "status": "running",
        "version": "improved-2.0",
        "improvements": [
            "Enhanced speaker identification with silhouette analysis",
            "Better feature extraction (32-dimensional)",
            "Improved clustering with post-processing",
            "Reduced over-segmentation issues"
        ],
        "endpoints": {
            "audio_upload": "/audio2summary_async",
            "task_status": "/task_status", 
            "task_result": "/task_result",
            "meeting_ask": "/meeting/ask",
            "docs": "/docs"
        }
    }

# 异步接口：大文件/长任务推荐
@app.post("/audio2summary_async")
async def audio2summary_async(file: UploadFile = File(...)):
    temp_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    task_id = generate_task_id()
    set_task_status(task_id, "pending", 0, result=None, error=None)
    
    def process_task():
        try:
            set_task_status(task_id, "processing", 10, result=None, error=None, stage="文件上传完成，准备开始处理")
            print(f"🚀 开始处理任务 {task_id} (改进版)")
            
            # 详细的进度报告
            set_task_status(task_id, "processing", 15, result=None, error=None, stage="初始化改进版Whisper模型")
            
            # 使用改进版处理器，它会自动使用改进的声纹识别
            set_task_status(task_id, "processing", 20, result=None, error=None, stage="开始音频转写（改进版）")
            
            # 使用改进版处理方法
            result_data = processor.process_with_speaker_id(temp_path, output_dir="temp_output")
            
            set_task_status(task_id, "processing", 90, result=None, error=None, stage="音频处理完成，创建会议纪要")
            
            print(f"🎯 音频处理完成，说话人数: {result_data.get('speaker_count', 0)}")
            set_task_status(task_id, "processing", 92, result=None, error=None, stage="创建智能问答会话")
            
            # 创建会议对话会话
            try:
                chat_session_created = meeting_chat_manager.create_session(
                    task_id, 
                    result_data["cleaned"], 
                    result_data["minutes"]
                )
                print(f"聊天会话创建{'成功' if chat_session_created else '失败'}")
            except Exception as chat_error:
                print(f"创建聊天会话失败: {chat_error}")
                chat_session_created = False
            
            result = {
                "transcript": result_data["transcript"],
                "cleaned": result_data["cleaned"], 
                "minutes": result_data["minutes"],
                "speaker_count": result_data["speaker_count"],
                "meeting_name": result_data["meeting_name"],
                "chat_available": chat_session_created,
                "version": "improved-speaker-id-2.0"
            }
            
            print(f"✅ 任务 {task_id} 处理完成 (改进版)")
            set_task_status(task_id, "done", 100, result=result, error=None, stage="处理完成")
            
        except Exception as e:
            print(f"❌ 任务 {task_id} 处理失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 提供更详细的错误信息
            error_msg = str(e)
            if "Invalid argument" in error_msg and ".md" in error_msg:
                error_msg = f"文件保存失败，可能包含非法字符: {error_msg}"
            elif "Permission denied" in error_msg:
                error_msg = f"权限不足，无法写入文件: {error_msg}"
            elif "No space left" in error_msg:
                error_msg = f"磁盘空间不足: {error_msg}"
            
            set_task_status(task_id, "error", 100, result=None, error=error_msg)
            
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"🗑️ 已清理临时文件: {temp_path}")
            except Exception as cleanup_error:
                print(f"清理临时文件失败: {cleanup_error}")
    
    threading.Thread(target=process_task, daemon=True).start()
    return {"task_id": task_id, "status": "pending", "version": "improved-speaker-id-2.0"}

@app.get("/task_status")
def task_status(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="任务不存在")
    task = TASKS[task_id]
    if task["status"] == "error":
        return {
            "status": "error",
            "progress": task["progress"],
            "error": task.get("error", "未知错误")
        }
    return task

@app.get("/task_result")
def task_result(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="任务不存在")
    task = TASKS[task_id]
    if task["status"] == "error":
        return {
            "status": "error",
            "progress": task["progress"],
            "error": task.get("error", "未知错误")
        }
    if task["status"] != "done":
        return {"status": task["status"], "progress": task["progress"]}
    return {"status": "done", "result": task["result"]}

# Pydantic 模型定义
class QuestionRequest(BaseModel):
    task_id: str
    question: str

# 会议问答相关API接口
@app.post("/meeting/ask")
def ask_meeting_question(request: QuestionRequest):
    """
    向会议内容提问
    """
    try:
        # 验证输入参数
        if not request.task_id or not request.task_id.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "msg": "task_id不能为空",
                    "data": None
                }
            )
        
        if not request.question or not request.question.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "msg": "question不能为空", 
                    "data": None
                }
            )
        
        # 检查任务是否存在且已完成
        if request.task_id not in TASKS:
            return JSONResponse(
                status_code=404,
                content={
                    "code": 1,
                    "msg": "任务不存在，请先完成音频处理",
                    "data": None
                }
            )
        
        task = TASKS[request.task_id]
        if task["status"] != "done":
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "msg": f"任务尚未完成，当前状态: {task['status']}",
                    "data": None
                }
            )
        
        # 调用问答功能
        result = meeting_chat_manager.ask_question(request.task_id, request.question)
        
        if result["success"]:
            return JSONResponse(
                content={
                    "code": 0,
                    "msg": "success", 
                    "data": {
                        "answer": result["answer"],
                        "question": result["question"],
                        "conversation_count": result["conversation_count"]
                    }
                }
            )
        else:
            return JSONResponse(
                content={
                    "code": 1,
                    "msg": result["error"],
                    "data": None
                }
            )
            
    except Exception as e:
        print(f"问答处理异常: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"问答处理失败: {str(e)}",
                "data": None
            }
        )

@app.get("/meeting/chat/history")
def get_chat_history(task_id: str):
    """获取会议对话历史"""
    try:
        result = meeting_chat_manager.get_conversation_history(task_id)
        
        if result["success"]:
            return {
                "code": 0,
                "msg": "success",
                "data": {
                    "task_id": result["task_id"],
                    "conversation_count": result["conversation_count"],
                    "conversations": result["conversations"],
                    "created_at": result["created_at"]
                }
            }
        else:
            return {
                "code": 1,
                "msg": result["error"],
                "data": None
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")

@app.delete("/meeting/chat/clear")
def clear_chat_history(task_id: str):
    """清空会议对话历史"""
    try:
        result = meeting_chat_manager.clear_conversation(task_id)
        
        if result["success"]:
            return {
                "code": 0,
                "msg": "success",
                "data": {
                    "message": result["message"]
                }
            }
        else:
            return {
                "code": 1, 
                "msg": result["error"],
                "data": None
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空对话失败: {str(e)}")

@app.get("/meeting/chat/status")
def get_chat_status(task_id: str):
    """检查会议对话会话状态"""
    try:
        session = meeting_chat_manager.get_session(task_id)
        
        if session:
            return {
                "code": 0,
                "msg": "success",
                "data": {
                    "task_id": task_id,
                    "available": True,
                    "conversation_count": len(session.conversation_history),
                    "created_at": session.created_at.isoformat()
                }
            }
        else:
            return {
                "code": 1,
                "msg": "会话不存在",
                "data": {
                    "task_id": task_id,
                    "available": False
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查会话状态失败: {str(e)}")

# 健康检查接口
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "improved-speaker-id-2.0",
        "improvements_active": True,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("启动改进版ConferenceAssistant Web服务 (8080端口)")
    print("包含改进的声纹识别系统")
    uvicorn.run(app, host="0.0.0.0", port=8080)