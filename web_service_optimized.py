#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConferenceAssistant 优化版 Web 服务
主要优化：
1. 使用优化的核心处理模块
2. 改进的任务管理和进度报告
3. 内存使用优化
4. 性能监控和统计
"""

import os
import time
import tempfile
from typing import Optional
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 导入优化的核心模块
from core_optimized import OptimizedMeetingProcessor, OPTIMIZE_CONFIG
from async_task_manager import AsyncTaskManager
from meeting_chat import MeetingChatManager

# 请求模型
class MeetingQuestion(BaseModel):
    task_id: str
    question: str

# 全局变量
meeting_processor = None
task_manager = None
chat_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    global meeting_processor, task_manager, chat_manager
    
    print("🚀 启动优化版ConferenceAssistant服务...")
    
    # 初始化组件
    meeting_processor = OptimizedMeetingProcessor()
    task_manager = AsyncTaskManager()
    chat_manager = MeetingChatManager()
    
    print("✅ 服务初始化完成")
    print(f"📊 优化配置: {OPTIMIZE_CONFIG}")
    
    yield
    
    # 关闭时清理
    print("🔄 正在关闭服务...")
    if task_manager:
        # 等待所有任务完成或超时
        task_manager.shutdown(timeout=30)
    print("✅ 服务已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="ConferenceAssistant API (Optimized)",
    description="优化版AI会议助手 - 提供高性能的音频处理和智能问答服务",
    version="2.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "ConferenceAssistant API (Optimized)",
        "version": "2.0.0",
        "status": "running",
        "optimization": OPTIMIZE_CONFIG,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "tasks_active": task_manager.get_active_task_count() if task_manager else 0,
        "memory_optimization": OPTIMIZE_CONFIG.get('enable_gpu_memory_optimization', False)
    }

@app.post("/audio2summary_async")
async def upload_audio_optimized(file: UploadFile = File(...)):
    """
    优化版异步音频处理接口
    """
    try:
        # 验证文件格式
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        file_extension = file.filename.lower().split('.')[-1]
        supported_formats = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'mp4', 'webm']
        if file_extension not in supported_formats:
            raise HTTPException(
                status_code=415, 
                detail=f"Unsupported audio format: {file_extension}. Supported: {supported_formats}"
            )
        
        # 文件大小检查（100MB限制）
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=413, detail="File too large (max 100MB)")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # 保存临时文件
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f".{file_extension}",
            prefix="meeting_"
        )
        temp_file.write(content)
        temp_file.close()
        
        print(f"📁 文件已保存: {temp_file.name} ({file_size / 1024 / 1024:.2f}MB)")
        
        # 创建优化处理任务
        task_id = str(uuid.uuid4())
        
        def optimized_processing_task():
            """优化的处理任务"""
            try:
                print(f"🚀 开始处理任务 {task_id}")
                
                # 使用优化的处理器
                result = meeting_processor.process_with_optimization(
                    audio_path=temp_file.name,
                    meeting_name=None,
                    output_dir="outputs"
                )
                
                # 创建聊天会话
                if result.get("speaker_count", 0) > 0 or len(result.get("cleaned", "")) > 100:
                    try:
                        chat_manager.create_chat_session(
                            task_id=task_id,
                            meeting_content=result["cleaned"],
                            meeting_minutes=result["minutes"]
                        )
                        result["chat_available"] = True
                    except Exception as e:
                        print(f"创建聊天会话失败: {e}")
                        result["chat_available"] = False
                else:
                    result["chat_available"] = False
                
                print(f"✅ 任务 {task_id} 处理完成")
                print(f"📊 处理统计: {result.get('processing_stats', {})}")
                
                return result
                
            except Exception as e:
                print(f"❌ 任务 {task_id} 处理失败: {e}")
                import traceback
                traceback.print_exc()
                raise e
            
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_file.name)
                    print(f"🗑️ 清理临时文件: {temp_file.name}")
                except:
                    pass
        
        # 提交任务
        task_manager.submit_task(task_id, optimized_processing_task)
        
        return JSONResponse(
            status_code=200,
            content={
                "task_id": task_id,
                "status": "pending",
                "message": "任务已提交，正在使用优化算法处理",
                "optimization_enabled": True,
                "file_size_mb": round(file_size / 1024 / 1024, 2)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"上传处理失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.get("/task_status")
async def get_task_status_optimized(task_id: str = Query(...)):
    """
    获取任务状态（优化版，包含详细统计）
    """
    try:
        status_info = task_manager.get_task_status(task_id)
        
        if not status_info:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 添加优化信息
        response = {
            "status": status_info["status"],
            "progress": status_info.get("progress", 0),
            "eta": status_info.get("eta"),
            "start_time": status_info.get("start_time"),
            "optimization_enabled": True
        }
        
        # 如果有错误，添加错误信息
        if status_info.get("error"):
            response["error"] = status_info["error"]
        
        # 如果任务完成，添加性能统计
        if status_info["status"] == "done" and status_info.get("result"):
            result = status_info["result"]
            if "processing_stats" in result:
                response["performance"] = result["processing_stats"]
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@app.get("/task_result")
async def get_task_result_optimized(task_id: str = Query(...)):
    """
    获取任务结果（优化版，包含性能统计）
    """
    try:
        task_info = task_manager.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task_info["status"] == "pending":
            return JSONResponse(content={
                "status": "pending",
                "progress": 0,
                "message": "任务等待处理中"
            })
        
        if task_info["status"] == "processing":
            return JSONResponse(content={
                "status": "processing", 
                "progress": task_info.get("progress", 0),
                "eta": task_info.get("eta"),
                "message": "任务处理中（使用优化算法）"
            })
        
        if task_info["status"] == "error":
            return JSONResponse(content={
                "status": "error",
                "progress": task_info.get("progress", 0),
                "error": task_info.get("error", "未知错误"),
                "message": "任务处理失败"
            })
        
        if task_info["status"] == "done":
            result = task_info["result"]
            
            response_data = {
                "status": "done",
                "result": {
                    "transcript": result["transcript"],
                    "cleaned": result["cleaned"], 
                    "minutes": result["minutes"],
                    "speaker_count": result.get("speaker_count", 0),
                    "meeting_name": result["meeting_name"],
                    "chat_available": result.get("chat_available", False),
                    "transcript_markdown_path": result.get("transcript_markdown_path", ""),
                    "minutes_markdown_path": result.get("minutes_markdown_path", "")
                },
                "optimization_stats": result.get("processing_stats", {})
            }
            
            return JSONResponse(content=response_data)
        
        # 未知状态
        return JSONResponse(content={
            "status": task_info["status"],
            "message": f"未知任务状态: {task_info['status']}"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取任务结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")

# 智能问答接口（使用原有的chat_manager）
@app.post("/meeting/ask")
async def ask_meeting_question(request: MeetingQuestion):
    """向会议内容提问"""
    try:
        result = chat_manager.ask_question(request.task_id, request.question)
        return JSONResponse(content=result)
    except Exception as e:
        print(f"问答处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")

@app.get("/meeting/chat/history")
async def get_chat_history(task_id: str = Query(...)):
    """获取对话历史"""
    try:
        result = chat_manager.get_chat_history(task_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")

@app.delete("/meeting/chat/clear")
async def clear_chat_history(task_id: str = Query(...)):
    """清空对话历史"""
    try:
        result = chat_manager.clear_chat_history(task_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空历史失败: {str(e)}")

@app.get("/meeting/chat/status")
async def get_chat_status(task_id: str = Query(...)):
    """检查会话状态"""
    try:
        result = chat_manager.check_chat_status(task_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查状态失败: {str(e)}")

# 新增：性能统计接口
@app.get("/stats/performance")
async def get_performance_stats():
    """获取系统性能统计"""
    try:
        stats = {
            "active_tasks": task_manager.get_active_task_count() if task_manager else 0,
            "completed_tasks": task_manager.get_completed_task_count() if task_manager else 0,
            "optimization_config": OPTIMIZE_CONFIG,
            "chat_sessions": chat_manager.get_session_count() if chat_manager else 0
        }
        
        # 添加系统资源信息
        try:
            import psutil
            stats["system"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        except ImportError:
            stats["system"] = {"note": "psutil not available"}
        
        # 添加GPU信息（如果可用）
        try:
            import torch
            if torch.cuda.is_available():
                stats["gpu"] = {
                    "available": True,
                    "device_count": torch.cuda.device_count(),
                    "current_device": torch.cuda.current_device(),
                    "memory_allocated": torch.cuda.memory_allocated() / 1024**3,  # GB
                    "memory_cached": torch.cuda.memory_reserved() / 1024**3      # GB
                }
            else:
                stats["gpu"] = {"available": False}
        except ImportError:
            stats["gpu"] = {"note": "PyTorch not available"}
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

# 新增：优化配置接口
@app.get("/config/optimization")
async def get_optimization_config():
    """获取当前优化配置"""
    return JSONResponse(content=OPTIMIZE_CONFIG)

@app.post("/config/optimization")
async def update_optimization_config(config: dict):
    """更新优化配置（重启后生效）"""
    try:
        valid_keys = set(OPTIMIZE_CONFIG.keys())
        update_keys = set(config.keys())
        
        if not update_keys.issubset(valid_keys):
            invalid_keys = update_keys - valid_keys
            raise HTTPException(
                status_code=400, 
                detail=f"无效的配置键: {list(invalid_keys)}"
            )
        
        # 这里可以添加配置验证逻辑
        # 注意：配置更新通常需要重启服务才能生效
        
        return JSONResponse(content={
            "message": "配置已接收，重启服务后生效",
            "current_config": OPTIMIZE_CONFIG,
            "requested_updates": config
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ConferenceAssistant Optimized Web Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"🚀 启动优化版ConferenceAssistant Web服务")
    print(f"📡 地址: http://{args.host}:{args.port}")
    print(f"📊 优化配置: {OPTIMIZE_CONFIG}")
    
    uvicorn.run(
        "web_service_optimized:app",
        host=args.host,
        port=args.port,
        workers=args.workers if not args.reload else 1,
        reload=args.reload,
        log_level="info"
    )