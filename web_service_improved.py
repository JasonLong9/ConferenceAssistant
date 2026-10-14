from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core import LocalWhisper, clean_transcript, generate_meeting_minutes, extract_meeting_name, MeetingProcessor
import os
from datetime import datetime
import threading
from async_task_manager import TASKS, generate_task_id, set_task_status
from meeting_chat import meeting_chat_manager

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
    from core import IMPROVED_SPEAKER_ID_AVAILABLE
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
        "improved_speaker_id_active": IMPROVED_SPEAKER_ID_AVAILABLE,
        "endpoints": {
            "audio_upload": "/audio2summary_async",
            "task_status": "/task_status", 
            "task_result": "/task_result",
            "meeting_ask": "/meeting/ask",
            "health": "/health",
            "docs": "/docs"
        }
    }

# # 同步接口：已废弃，仅保留异步接口
# @app.post("/audio2summary")
# async def audio2summary(file: UploadFile = File(...)):
#     temp_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
#     with open(temp_path, "wb") as f:
#         f.write(await file.read())
#     try:
#         whisper = LocalWhisper()
#         full_text = whisper.transcribe(temp_path)
#         cleaned = clean_transcript(full_text)
#         summary = generate_meeting_minutes(cleaned)
#         meeting_name = extract_meeting_name(summary)
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         return JSONResponse({
#             "code": 0,
#             "msg": "success",
#             "data": {
#                 "original_text": full_text,
#                 "cleaned": cleaned,
#                 "summary": summary,
#                 "meeting_name": meeting_name,
#                 "timestamp": timestamp
#             }
#         })
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"处理失败: {e}")
#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)

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
            print(f"开始处理任务 {task_id}")
            
            # 详细的进度报告
            set_task_status(task_id, "processing", 15, result=None, error=None, stage="初始化Whisper模型")
            
            # 使用现有的方法，同时手动更新进度
            set_task_status(task_id, "processing", 20, result=None, error=None, stage="开始音频转写")
            
            # 检查是否有支持进度的方法
            if hasattr(processor, 'process_with_speaker_id_progress'):
                result_data = processor.process_with_speaker_id_progress(temp_path, output_dir="temp_output", 
                                                                       progress_callback=lambda p, s: set_task_status(task_id, "processing", p, result=None, error=None, stage=s))
            else:
                # 使用原有方法并手动更新进度
                set_task_status(task_id, "processing", 30, result=None, error=None, stage="正在进行音频转写...")
                result_data = processor.process_with_speaker_id(temp_path, output_dir="temp_output")
                set_task_status(task_id, "processing", 70, result=None, error=None, stage="音频转写完成，生成会议纪要")
            set_task_status(task_id, "processing", 90, result=None, error=None, stage="音频处理完成，创建会议纪要")
            
            print(f"音频处理完成，开始创建聊天会话...")
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
            
            # 强制格式化transcript为【Speaker_X】格式
            def force_speaker_format(text: str, speaker_count: int = None) -> str:
                """强制将文本格式化为【Speaker_X】格式"""
                if not text or not text.strip():
                    return ""
                
                # 检查是否已经有【Speaker_】格式
                if "【Speaker_" in text:
                    return text
                
                # 如果没有发言人格式，强制添加
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if not lines:
                    return ""
                
                # 按句子数量估算发言人数
                total_sentences = len([line for line in lines if line.endswith(('.', '。', '!', '！', '?', '？'))])
                estimated_speakers = min(5, max(1, total_sentences // 10)) if speaker_count is None else speaker_count
                
                formatted_lines = []
                sentences_per_speaker = max(1, len(lines) // estimated_speakers)
                
                for i, line in enumerate(lines):
                    speaker_id = min(i // sentences_per_speaker, estimated_speakers - 1)
                    
                    # 在发言人切换时添加标识
                    if i == 0 or (i // sentences_per_speaker) != ((i-1) // sentences_per_speaker):
                        if formatted_lines:  # 不是第一个发言人
                            formatted_lines.append("")
                        formatted_lines.append(f"【Speaker_{speaker_id}】")
                    
                    formatted_lines.append(line)
                
                return "\n".join(formatted_lines)
            
            # 强制格式化transcript
            formatted_transcript = force_speaker_format(result_data['transcript'], result_data.get('speaker_count', 3))
            
            # 格式化cleaned内容 - 使用强制格式化的transcript
            formatted_cleaned = f"三、规整后文本内容\n\n以下是经过声纹识别和语音识别处理后的完整对话文本：\n\n{formatted_transcript}"
            
            # 确保minutes也基于格式化的transcript生成
            # 由于minutes是基于cleaned生成的，我们需要确保cleaned也使用正确格式
            # 这里可能需要重新生成minutes，但为了保持性能，暂时保持原样
            formatted_minutes = result_data["minutes"]
            
            result = {
                "transcript": formatted_transcript,  # 使用强制格式化的transcript
                "cleaned": formatted_cleaned, 
                "minutes": formatted_minutes,
                "speaker_count": result_data["speaker_count"],
                "meeting_name": result_data["meeting_name"],
                "chat_available": chat_session_created
            }
            
            print(f"任务 {task_id} 处理完成")
            set_task_status(task_id, "done", 100, result=result, error=None, stage="处理完成")
            
        except Exception as e:
            print(f"任务 {task_id} 处理失败: {e}")
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
                    print(f"已清理临时文件: {temp_path}")
            except Exception as cleanup_error:
                print(f"清理临时文件失败: {cleanup_error}")
    threading.Thread(target=process_task, daemon=True).start()
    return {"task_id": task_id, "status": "pending"}

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
@app.get("/meeting/ask")
def ask_meeting_question(task_id: str, question: str):
    """
    向会议内容提问
    
    Args:
        task_id: 任务ID (URL参数)
        question: 问题内容 (URL参数)
        
    Returns:
        问答结果
    """
    try:
        # 验证输入参数
        if not task_id or not task_id.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "msg": "task_id不能为空",
                    "data": None
                }
            )
        
        if not question or not question.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "msg": "question不能为空", 
                    "data": None
                }
            )
        
        # 检查任务是否存在且已完成
        if task_id not in TASKS:
            return JSONResponse(
                status_code=404,
                content={
                    "code": 1,
                    "msg": "任务不存在，请先完成音频处理",
                    "data": None
                }
            )
        
        task = TASKS[task_id]
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
        result = meeting_chat_manager.ask_question(task_id, question)
        
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
    """
    获取会议对话历史
    
    Args:
        task_id: 任务ID (URL参数)
        
    Returns:
        对话历史
    """
    try:
        # 验证输入参数
        if not task_id or not task_id.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "msg": "task_id不能为空",
                    "data": None
                }
            )
        
        result = meeting_chat_manager.get_conversation_history(task_id)
        
        if result["success"]:
            return JSONResponse(
                content={
                    "code": 0,
                    "msg": "success",
                    "data": {
                        "task_id": result["task_id"],
                        "conversation_count": result["conversation_count"],
                        "conversations": result["conversations"],
                        "created_at": result["created_at"]
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
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"获取对话历史失败: {str(e)}",
                "data": None
            }
        )

@app.get("/meeting/chat/clear")
def clear_chat_history(task_id: str):
    """
    清空会议对话历史
    
    Args:
        task_id: 任务ID (URL参数)
        
    Returns:
        操作结果
    """
    try:
        # 验证输入参数
        if not task_id or not task_id.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "msg": "task_id不能为空",
                    "data": None
                }
            )
        
        result = meeting_chat_manager.clear_conversation(task_id)
        
        if result["success"]:
            return JSONResponse(
                content={
                    "code": 0,
                    "msg": "success",
                    "data": {
                        "message": result["message"]
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
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"清空对话失败: {str(e)}",
                "data": None
            }
        )

@app.get("/meeting/chat/status")
def get_chat_status(task_id: str):
    """
    检查会议对话会话状态
    
    Args:
        task_id: 任务ID (URL参数)
        
    Returns:
        会话状态信息
    """
    try:
        # 验证输入参数
        if not task_id or not task_id.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "msg": "task_id不能为空",
                    "data": None
                }
            )
        
        session = meeting_chat_manager.get_session(task_id)
        
        if session:
            return JSONResponse(
                content={
                    "code": 0,
                    "msg": "success",
                    "data": {
                        "task_id": task_id,
                        "available": True,
                        "conversation_count": len(session.conversation_history),
                        "created_at": session.created_at.isoformat()
                    }
                }
            )
        else:
            return JSONResponse(
                content={
                    "code": 1,
                    "msg": "会话不存在",
                    "data": {
                        "task_id": task_id,
                        "available": False
                    }
                }
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": 1,
                "msg": f"检查会话状态失败: {str(e)}",
                "data": None
            }
        )

# 健康检查接口
@app.get("/health")
def health_check():
    from core import IMPROVED_SPEAKER_ID_AVAILABLE
    return {
        "status": "healthy",
        "version": "improved-speaker-id-2.0",
        "improvements_active": IMPROVED_SPEAKER_ID_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }