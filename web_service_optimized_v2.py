from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import asyncio
import uvicorn
from contextlib import asynccontextmanager
import time
import logging
from datetime import datetime, timedelta

# 导入核心模块
from core import MeetingProcessor
from async_task_manager import TASKS, generate_task_id, set_task_status
from meeting_chat_optimized import (
    optimized_meeting_chat_manager, 
    MeetingMetadata,
    create_optimized_chat_session
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 ConferenceAssistant API 启动中...")
    
    # 启动后台清理任务
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # 关闭时执行
    logger.info("🛑 ConferenceAssistant API 关闭中...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("清理任务已取消")

app = FastAPI(
    title="ConferenceAssistant API (Optimized)",
    description="优化的会议助手API，支持音频转录、会议纪要生成和智能问答",
    version="2.0.0",
    lifespan=lifespan
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 可选：添加信任主机中间件（生产环境建议）
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

# 全局处理器实例
processor = MeetingProcessor()

# 请求限流中间件
class RateLimitMiddleware:
    """简单的请求限流中间件"""
    def __init__(self):
        self.requests = {}
        
    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # 清理过期记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] 
                if current_time - req_time < 60  # 1分钟窗口
            ]
        
        # 检查请求频率（每分钟最多30次请求）
        if client_ip in self.requests and len(self.requests[client_ip]) >= 30:
            return JSONResponse(
                status_code=429,
                content={
                    "code": 1,
                    "msg": "请求过于频繁，请稍后再试",
                    "data": None
                }
            )
        
        # 记录当前请求
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        return response

# 添加限流中间件
app.add_middleware(RateLimitMiddleware)

# Pydantic 数据模型
class QuestionRequest(BaseModel):
    """问题请求模型"""
    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")
    question: str = Field(..., min_length=1, max_length=1000, description="问题内容")
    
    @validator('task_id')
    def validate_task_id(cls, v):
        if not v.strip():
            raise ValueError('任务ID不能为空')
        return v.strip()
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('问题内容不能为空')
        return v.strip()

class StandardResponse(BaseModel):
    """标准响应模型"""
    code: int = Field(description="状态码：0-成功，1-失败")
    msg: str = Field(description="响应消息")
    data: Optional[dict] = Field(description="响应数据")

# API端点定义
@app.get("/", tags=["系统"])
def root():
    """API根路径 - 系统信息"""
    return {
        "service": "ConferenceAssistant API (Optimized)",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "音频转录 (Whisper)",
            "声纹识别",  
            "会议纪要生成",
            "智能问答 (优化版)",
            "对话历史管理",
            "异步任务处理"
        ],
        "endpoints": {
            "upload": "POST /audio2summary_async",
            "status": "GET /task_status",
            "result": "GET /task_result", 
            "ask": "POST /meeting/ask",
            "history": "GET /meeting/chat/history",
            "clear": "DELETE /meeting/chat/clear",
            "chat_status": "GET /meeting/chat/status",
            "docs": "/docs"
        }
    }

@app.get("/health", tags=["系统"])
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "运行中",
        "active_sessions": len(optimized_meeting_chat_manager.sessions),
        "active_tasks": len(TASKS)
    }

@app.post("/audio2summary_async", tags=["音频处理"])
async def upload_audio_async(file: UploadFile = File(...)):
    """
    异步音频上传和处理
    
    - 支持MP3、WAV、M4A等格式
    - 自动转录、声纹识别、生成纪要
    - 创建智能问答会话
    """
    
    # 文件验证
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 检查文件大小（限制100MB）
    if hasattr(file, 'size') and file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件大小超过限制（最大100MB）")
    
    # 检查文件格式
    allowed_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.flac'}
    file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}"
        )
    
    # 保存临时文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_path = f"temp_{timestamp}_{file.filename}"
    
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # 创建异步任务
        task_id = generate_task_id()
        set_task_status(task_id, "pending", 0, result=None, error=None)
        
        # 启动后台处理任务
        asyncio.create_task(process_audio_task(task_id, temp_path, file.filename))
        
        logger.info(f"音频上传成功，任务ID: {task_id}，文件: {file.filename}")
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "文件上传成功，开始处理",
            "filename": file.filename,
            "estimated_time": "预计3-10分钟"
        }
        
    except Exception as e:
        logger.error(f"音频上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

async def process_audio_task(task_id: str, temp_path: str, filename: str):
    """后台音频处理任务"""
    try:
        set_task_status(task_id, "processing", 10, result=None, error=None)
        logger.info(f"开始处理音频任务: {task_id}")
        
        # 使用优化的处理方法
        result_data = processor.process_with_speaker_id(temp_path, output_dir="temp_output")
        set_task_status(task_id, "processing", 80, result=None, error=None)
        
        logger.info(f"音频处理完成，开始创建优化问答会话: {task_id}")
        
        # 创建会议元数据
        metadata = MeetingMetadata(
            meeting_name=result_data.get("meeting_name", "未知会议"),
            speaker_count=result_data.get("speaker_count", 0),
            duration=0.0,  # 可以从处理结果中获取
            topics=[],
            key_decisions=[]
        )
        
        # 创建优化的问答会话
        try:
            success, message = create_optimized_chat_session(
                task_id,
                result_data["cleaned"], 
                result_data["minutes"],
                metadata
            )
            
            if success:
                logger.info(f"优化问答会话创建成功: {task_id}")
                result_data["chat_available"] = True
                result_data["chat_optimized"] = True
            else:
                logger.warning(f"优化问答会话创建失败: {task_id} - {message}")
                result_data["chat_available"] = False
                result_data["chat_error"] = message
                
        except Exception as chat_error:
            logger.error(f"创建优化问答会话异常: {chat_error}")
            result_data["chat_available"] = False
            result_data["chat_error"] = str(chat_error)
        
        # 任务完成
        set_task_status(task_id, "done", 100, result=result_data, error=None)
        logger.info(f"任务处理完成: {task_id}")
        
    except Exception as e:
        error_msg = f"处理失败: {str(e)}"
        logger.error(f"任务处理异常: {task_id} - {error_msg}")
        set_task_status(task_id, "error", 0, result=None, error=error_msg)
    finally:
        # 清理临时文件
        try:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f"临时文件已清理: {temp_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

@app.get("/task_status", tags=["任务管理"])
def get_task_status(task_id: str = Query(..., description="任务ID")):
    """
    查询任务处理状态
    
    - pending: 待处理
    - processing: 处理中  
    - done: 已完成
    - error: 处理失败
    """
    if not task_id.strip():
        raise HTTPException(status_code=400, detail="任务ID不能为空")
        
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = TASKS[task_id]
    
    response = {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "last_updated": task.get("updated_at", datetime.now().isoformat())
    }
    
    # 添加预计剩余时间
    if task["status"] == "processing":
        # 简单的ETA计算（可以根据历史数据优化）
        progress = max(task["progress"], 1)
        elapsed = time.time() - task.get("start_time", time.time())
        eta = (elapsed / progress) * (100 - progress) / 100
        response["eta"] = round(eta, 2)
    
    if task["status"] == "error":
        response["error"] = task.get("error", "未知错误")
    
    return response

@app.get("/task_result", tags=["任务管理"])  
def get_task_result(task_id: str = Query(..., description="任务ID")):
    """
    获取任务处理结果
    
    只有状态为 'done' 的任务才会返回结果
    """
    if not task_id.strip():
        raise HTTPException(status_code=400, detail="任务ID不能为空")
        
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = TASKS[task_id]
    
    if task["status"] == "error":
        return {
            "status": "error",
            "progress": task["progress"],
            "error": task.get("error", "未知错误"),
            "task_id": task_id
        }
    
    if task["status"] != "done":
        return {
            "status": task["status"],
            "progress": task["progress"],
            "task_id": task_id,
            "message": "任务尚未完成"
        }
    
    return {
        "status": "done", 
        "result": task["result"],
        "task_id": task_id,
        "completed_at": task.get("updated_at", "")
    }

@app.post("/meeting/ask", response_model=StandardResponse, tags=["智能问答"])
async def ask_meeting_question_optimized(request: QuestionRequest):
    """
    智能会议问答（优化版）
    
    - 支持上下文相关的连续对话
    - 智能缓存提高响应速度
    - 增强的错误处理和验证
    - 详细的响应统计信息
    """
    try:
        # 验证任务状态
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
                    "data": {
                        "current_status": task["status"],
                        "progress": task["progress"]
                    }
                }
            )
        
        # 使用优化的异步问答方法
        result = await optimized_meeting_chat_manager.ask_question_async(
            request.task_id, 
            request.question
        )
        
        if result["success"]:
            return {
                "code": 0,
                "msg": "success",
                "data": {
                    "answer": result["answer"],
                    "question": result["question"],
                    "conversation_count": result["conversation_count"],
                    "response_time": result.get("response_time", 0),
                    "from_cache": result.get("from_cache", False),
                    "timestamp": datetime.now().isoformat()
                }
            }
        else:
            status_code = 404 if result.get("code") == 404 else 500
            return JSONResponse(
                status_code=status_code,
                content={
                    "code": 1,
                    "msg": result["error"],
                    "data": None
                }
            )
            
    except Exception as e:
        logger.error(f"问答处理异常: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"问答处理失败: {str(e)}",
                "data": None
            }
        )

@app.get("/meeting/chat/history", response_model=StandardResponse, tags=["对话管理"])
def get_optimized_chat_history(
    task_id: str = Query(..., description="任务ID"),
    include_stats: bool = Query(False, description="是否包含统计信息")
):
    """
    获取优化的对话历史
    
    - 包含详细的对话记录和时间戳
    - 可选的统计信息（响应时间、会话状态等）
    - 支持分页（未来版本）
    """
    try:
        result = optimized_meeting_chat_manager.get_conversation_history(task_id, include_stats)
        
        if result["success"]:
            return {
                "code": 0,
                "msg": "success", 
                "data": {
                    "task_id": result["task_id"],
                    "conversation_count": result["conversation_count"],
                    "conversations": result["conversations"],
                    "created_at": result["created_at"],
                    "last_activity": result["last_activity"],
                    **({"statistics": result["statistics"]} if include_stats and "statistics" in result else {})
                }
            }
        else:
            status_code = 404 if result.get("code") == 404 else 500
            return JSONResponse(
                status_code=status_code,
                content={
                    "code": 1,
                    "msg": result["error"],
                    "data": None
                }
            )
            
    except Exception as e:
        logger.error(f"获取对话历史异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")

@app.delete("/meeting/chat/clear", response_model=StandardResponse, tags=["对话管理"])
def clear_optimized_chat_history(task_id: str = Query(..., description="任务ID")):
    """
    清空优化的对话历史
    
    - 保留会话基础信息
    - 重置对话计数器
    - 清理缓存数据
    """
    try:
        result = optimized_meeting_chat_manager.clear_conversation(task_id)
        
        if result["success"]:
            return {
                "code": 0,
                "msg": "success",
                "data": {
                    "message": result["message"],
                    "timestamp": datetime.now().isoformat()
                }
            }
        else:
            status_code = 404 if result.get("code") == 404 else 500
            return JSONResponse(
                status_code=status_code,
                content={
                    "code": 1,
                    "msg": result["error"],
                    "data": None
                }
            )
            
    except Exception as e:
        logger.error(f"清空对话历史异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清空对话失败: {str(e)}")

@app.get("/meeting/chat/status", response_model=StandardResponse, tags=["对话管理"])
def get_optimized_chat_status(task_id: str = Query(..., description="任务ID")):
    """
    获取优化的对话会话状态
    
    - 会话可用性检查
    - 详细的统计信息
    - 会话健康状态
    """
    try:
        result = optimized_meeting_chat_manager.get_session_status(task_id)
        
        if result["success"]:
            return {
                "code": 0,
                "msg": "success",
                "data": {
                    "task_id": result["task_id"],
                    "available": result["available"],
                    "status": result["status"],
                    "conversation_count": result["conversation_count"],
                    "created_at": result["created_at"],
                    "last_activity": result["last_activity"],
                    "statistics": result["statistics"]
                }
            }
        else:
            return {
                "code": 1,
                "msg": result["error"],
                "data": {
                    "task_id": task_id,
                    "available": False
                }
            }
            
    except Exception as e:
        logger.error(f"获取对话状态异常: {str(e)}")
        return {
            "code": 1,
            "msg": f"获取对话状态失败: {str(e)}",
            "data": {
                "task_id": task_id,
                "available": False
            }
        }

# 管理端点
@app.get("/admin/sessions", tags=["管理"])
def list_sessions():
    """列出所有活跃会话（管理用）"""
    sessions = []
    for task_id, session in optimized_meeting_chat_manager.sessions.items():
        sessions.append({
            "task_id": task_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(), 
            "conversation_count": len(session.conversation_history),
            "status": session.status.value
        })
    
    return {
        "total_sessions": len(sessions),
        "sessions": sessions,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/admin/cleanup", tags=["管理"])
def manual_cleanup():
    """手动清理过期会话（管理用）"""
    try:
        cleaned_count = optimized_meeting_chat_manager.cleanup_inactive_sessions(max_age_hours=24)
        return {
            "message": f"清理完成，清理了{cleaned_count}个过期会话",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

# 后台定时任务
async def periodic_cleanup():
    """定期清理任务"""
    while True:
        try:
            await asyncio.sleep(3600)  # 每小时执行一次
            cleaned = optimized_meeting_chat_manager.cleanup_inactive_sessions(max_age_hours=24)
            if cleaned > 0:
                logger.info(f"定期清理: 清理了{cleaned}个过期会话")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"定期清理异常: {e}")

# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": 1,
            "msg": exc.detail,
            "data": None,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 1,
            "msg": "服务器内部错误",
            "data": None,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        },
    )

if __name__ == "__main__":
    uvicorn.run(
        "web_service_optimized_v2:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info",
        access_log=True
    )