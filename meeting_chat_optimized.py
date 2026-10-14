#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化的会议内容问答模块
支持基于会议内容的连续对话功能，增强错误处理和性能优化
"""

import json
import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import requests
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionStatus(Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class APIProvider(Enum):
    """AI API提供商枚举"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CLAUDE = "claude"

@dataclass
class ConversationRecord:
    """对话记录数据类"""
    timestamp: str
    question: str
    answer: str
    response_time: float = 0.0
    token_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "question": self.question,
            "answer": self.answer,
            "response_time": self.response_time,
            "token_count": self.token_count
        }

@dataclass
class MeetingMetadata:
    """会议元数据"""
    meeting_name: str = ""
    speaker_count: int = 0
    duration: float = 0.0
    topics: List[str] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)

class OptimizedMeetingChatSession:
    """优化的会议对话会话管理类"""
    
    def __init__(self, task_id: str, cleaned_content: str, meeting_minutes: str, metadata: Optional[MeetingMetadata] = None):
        """
        初始化会议对话会话
        
        Args:
            task_id: 任务ID
            cleaned_content: 规整后的会议内容
            meeting_minutes: 会议纪要
            metadata: 会议元数据
        """
        self.task_id = task_id
        self.cleaned_content = cleaned_content
        self.meeting_minutes = meeting_minutes
        self.metadata = metadata or MeetingMetadata()
        self.conversation_history: List[ConversationRecord] = []
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = self.created_at
        self.status = SessionStatus.ACTIVE
        self._content_hash = self._generate_content_hash()
        
        # 构建优化的上下文
        self.base_context = self._build_optimized_context()
        
        # 性能统计
        self.total_questions = 0
        self.total_response_time = 0.0
        
    def _generate_content_hash(self) -> str:
        """生成内容哈希，用于缓存和去重"""
        content = f"{self.cleaned_content}{self.meeting_minutes}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def _build_optimized_context(self) -> str:
        """构建优化的初始上下文"""
        context_parts = ["# 会议分析资料\n"]
        
        # 会议基本信息
        if self.metadata.meeting_name:
            context_parts.append(f"**会议名称**: {self.metadata.meeting_name}")
        if self.metadata.speaker_count > 0:
            context_parts.append(f"**参与人数**: {self.metadata.speaker_count}人")
        if self.metadata.duration > 0:
            context_parts.append(f"**会议时长**: {self.metadata.duration:.1f}分钟")
        
        # 主要议题
        if self.metadata.topics:
            context_parts.append(f"\n**主要议题**:")
            for i, topic in enumerate(self.metadata.topics[:5], 1):  # 限制前5个议题
                context_parts.append(f"{i}. {topic}")
        
        # 关键决策
        if self.metadata.key_decisions:
            context_parts.append(f"\n**关键决策**:")
            for i, decision in enumerate(self.metadata.key_decisions[:5], 1):
                context_parts.append(f"{i}. {decision}")
        
        # 会议纪要（精简版）
        context_parts.append(f"\n## 会议纪要\n{self.meeting_minutes}")
        
        # 完整内容（截取前3000字符避免过长）
        content_preview = self.cleaned_content[:3000]
        if len(self.cleaned_content) > 3000:
            content_preview += "\n...(内容已截取，如需了解更多细节请具体询问)"
        
        context_parts.append(f"\n## 会议内容\n{content_preview}")
        
        context_parts.append("\n---\n请基于以上会议内容回答用户问题。")
        
        return "\n".join(context_parts)
    
    def add_conversation(self, question: str, answer: str, response_time: float = 0.0, token_count: int = 0):
        """添加对话记录"""
        record = ConversationRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            question=question,
            answer=answer,
            response_time=response_time,
            token_count=token_count
        )
        
        self.conversation_history.append(record)
        self.last_activity = datetime.now(timezone.utc)
        self.total_questions += 1
        self.total_response_time += response_time
        
        # 限制历史记录数量，避免上下文过长
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-15:]  # 保留最近15条
    
    def get_optimized_context(self, max_history: int = 5) -> str:
        """获取优化的对话上下文"""
        context_parts = [self.base_context]
        
        # 只包含最近的对话历史，避免上下文过长
        if self.conversation_history:
            recent_history = self.conversation_history[-max_history:]
            context_parts.append("\n## 最近对话")
            for i, conv in enumerate(recent_history, 1):
                context_parts.append(f"**Q{i}**: {conv.question}")
                context_parts.append(f"**A{i}**: {conv.answer[:200]}...")  # 截取答案前200字符
        
        return "\n\n".join(context_parts)
    
    def get_statistics(self) -> Dict:
        """获取会话统计信息"""
        avg_response_time = self.total_response_time / self.total_questions if self.total_questions > 0 else 0
        
        return {
            "total_questions": self.total_questions,
            "avg_response_time": round(avg_response_time, 2),
            "session_duration": (datetime.now(timezone.utc) - self.created_at).total_seconds() / 60,
            "last_activity": self.last_activity.isoformat(),
            "status": self.status.value,
            "content_hash": self._content_hash
        }

class OptimizedMeetingChatManager:
    """优化的会议对话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, OptimizedMeetingChatSession] = {}
        
        # API配置
        self.api_configs = {
            APIProvider.DEEPSEEK: {
                "url": "https://api.deepseek.com/v1/chat/completions",
                "key": os.getenv("DEEPSEEK_API_KEY", ""),
                "model": "deepseek-chat",
                "max_tokens": 2000,
                "temperature": 0.3
            }
        }
        
        # 当前使用的API提供商
        self.current_provider = APIProvider.DEEPSEEK
        
        # 线程池用于并发处理
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # 请求缓存（简单的内存缓存）
        self._response_cache: Dict[str, Tuple[str, datetime]] = {}
        self._cache_ttl = 300  # 缓存5分钟
        
        logger.info(f"OptimizedMeetingChatManager initialized with provider: {self.current_provider.value}")
        
        # 检查API密钥
        if not self.api_configs[self.current_provider]["key"]:
            logger.warning(f"API密钥未设置: {self.current_provider.value.upper()}_API_KEY")
    
    def create_session(self, task_id: str, cleaned_content: str, meeting_minutes: str, 
                      metadata: Optional[MeetingMetadata] = None) -> Tuple[bool, str]:
        """
        创建会议对话会话
        
        Args:
            task_id: 任务ID
            cleaned_content: 规整后的会议内容  
            meeting_minutes: 会议纪要
            metadata: 会议元数据
            
        Returns:
            Tuple[bool, str]: (创建是否成功, 错误信息或成功信息)
        """
        try:
            if not cleaned_content.strip() or not meeting_minutes.strip():
                return False, "会议内容或纪要为空"
            
            if task_id in self.sessions:
                logger.info(f"会话 {task_id} 已存在，将更新内容")
            
            session = OptimizedMeetingChatSession(
                task_id=task_id, 
                cleaned_content=cleaned_content, 
                meeting_minutes=meeting_minutes,
                metadata=metadata
            )
            self.sessions[task_id] = session
            
            logger.info(f"成功创建会议对话会话: {task_id}")
            return True, "会话创建成功"
            
        except Exception as e:
            error_msg = f"创建会话失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_session(self, task_id: str) -> Optional[OptimizedMeetingChatSession]:
        """获取会话"""
        session = self.sessions.get(task_id)
        if session and session.status != SessionStatus.ERROR:
            session.last_activity = datetime.now(timezone.utc)
        return session
    
    def _generate_cache_key(self, task_id: str, question: str) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{task_id}:{question}".encode('utf-8')).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """获取缓存的响应"""
        if cache_key in self._response_cache:
            response, timestamp = self._response_cache[cache_key]
            if (datetime.now(timezone.utc) - timestamp).total_seconds() < self._cache_ttl:
                return response
            else:
                # 清理过期缓存
                del self._response_cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response: str):
        """缓存响应"""
        self._response_cache[cache_key] = (response, datetime.now(timezone.utc))
        
        # 清理旧缓存（简单的LRU策略）
        if len(self._response_cache) > 100:
            oldest_key = min(self._response_cache.keys(), 
                           key=lambda k: self._response_cache[k][1])
            del self._response_cache[oldest_key]
    
    async def ask_question_async(self, task_id: str, question: str) -> Dict:
        """
        异步提问方法
        
        Args:
            task_id: 任务ID
            question: 用户问题
            
        Returns:
            Dict: 包含答案和状态的响应
        """
        start_time = time.time()
        
        try:
            session = self.get_session(task_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在，请先完成会议处理",
                    "answer": None,
                    "code": 404
                }
            
            # 检查缓存
            cache_key = self._generate_cache_key(task_id, question)
            cached_answer = self._get_cached_response(cache_key)
            if cached_answer:
                logger.info(f"使用缓存回答问题: {question[:50]}...")
                return {
                    "success": True,
                    "answer": cached_answer,
                    "question": question,
                    "conversation_count": len(session.conversation_history),
                    "from_cache": True,
                    "code": 0
                }
            
            # 获取优化的对话上下文
            context = session.get_optimized_context()
            
            # 构建增强的系统提示词
            system_prompt = self._build_enhanced_system_prompt(session)
            
            # 调用AI API
            answer = await self._call_ai_api_async(
                system_prompt, 
                f"{context}\n\n**用户问题**: {question}"
            )
            
            response_time = time.time() - start_time
            
            if answer:
                # 缓存响应
                self._cache_response(cache_key, answer)
                
                # 添加到对话历史
                session.add_conversation(question, answer, response_time)
                
                return {
                    "success": True,
                    "answer": answer,
                    "question": question,
                    "conversation_count": len(session.conversation_history),
                    "response_time": round(response_time, 2),
                    "from_cache": False,
                    "code": 0
                }
            else:
                return {
                    "success": False,
                    "error": "AI API调用失败",
                    "answer": None,
                    "code": 500
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"处理失败: {str(e)}"
            logger.error(f"问答处理异常 (耗时{response_time:.2f}s): {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "answer": None,
                "response_time": round(response_time, 2),
                "code": 500
            }
    
    def ask_question(self, task_id: str, question: str) -> Dict:
        """
        同步提问方法（保持向后兼容）
        
        Args:
            task_id: 任务ID
            question: 用户问题
            
        Returns:
            Dict: 包含答案和状态的响应
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.ask_question_async(task_id, question))
        finally:
            loop.close()
    
    def _build_enhanced_system_prompt(self, session: OptimizedMeetingChatSession) -> str:
        """构建增强的系统提示词"""
        prompt_parts = [
            "你是一个专业的会议分析助手，具备以下能力：",
            "",
            "**核心功能**：",
            "• 准确理解会议内容和上下文",
            "• 识别关键决策和行动项",
            "• 分析发言人观点和立场",
            "• 提供结构化的信息总结",
            "",
            "**回答原则**：",
            "1. **准确性优先**：严格基于会议内容回答，不添加未提及的信息",
            "2. **结构化表达**：使用清晰的格式组织回答",
            "3. **上下文关联**：结合对话历史提供连贯的回答",
            "4. **具体明确**：涉及人员、时间、数字时要具体引用",
            "5. **范围明确**：明确说明回答的信息来源范围",
            "",
            "**特殊处理**：",
            "• 如涉及多个发言人，请明确指出具体是谁说的",
            "• 如问题超出会议内容范围，请明确说明限制",
            "• 对于模糊问题，请提供多角度的分析",
            "",
            "**回答格式**：直接回答问题，使用markdown格式增强可读性，不要包含XML标签。"
        ]
        
        return "\n".join(prompt_parts)
    
    async def _call_ai_api_async(self, system_prompt: str, user_message: str) -> Optional[str]:
        """异步调用AI API"""
        try:
            config = self.api_configs[self.current_provider]
            
            if not config["key"]:
                logger.error(f"API密钥未配置: {self.current_provider.value}")
                return None
            
            headers = {
                "Authorization": f"Bearer {config['key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": config["model"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config["url"],
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        error_text = await response.text()
                        logger.error(f"AI API调用失败: {response.status} - {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("AI API调用超时")
            return None
        except Exception as e:
            logger.error(f"AI API调用异常: {e}")
            return None
    
    def get_conversation_history(self, task_id: str, include_stats: bool = False) -> Dict:
        """获取对话历史"""
        try:
            session = self.get_session(task_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在",
                    "code": 404
                }
            
            result = {
                "success": True,
                "task_id": task_id,
                "conversation_count": len(session.conversation_history),
                "conversations": [conv.to_dict() for conv in session.conversation_history],
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "code": 0
            }
            
            if include_stats:
                result["statistics"] = session.get_statistics()
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取对话历史失败: {str(e)}",
                "code": 500
            }
    
    def clear_conversation(self, task_id: str) -> Dict:
        """清空对话历史"""
        try:
            session = self.get_session(task_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在",
                    "code": 404
                }
            
            # 保存统计信息
            old_count = len(session.conversation_history)
            
            session.conversation_history = []
            session.last_activity = datetime.now(timezone.utc)
            
            return {
                "success": True,
                "message": f"已清空{old_count}条对话记录",
                "code": 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"清空对话失败: {str(e)}",
                "code": 500
            }
    
    def get_session_status(self, task_id: str) -> Dict:
        """获取会话状态"""
        try:
            session = self.get_session(task_id)
            
            if session:
                return {
                    "success": True,
                    "task_id": task_id,
                    "available": True,
                    "status": session.status.value,
                    "conversation_count": len(session.conversation_history),
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "statistics": session.get_statistics(),
                    "code": 0
                }
            else:
                return {
                    "success": False,
                    "task_id": task_id,
                    "available": False,
                    "error": "会话不存在",
                    "code": 404
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"获取会话状态失败: {str(e)}",
                "code": 500
            }
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """清理非活跃会话"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_sessions = []
            
            for task_id, session in self.sessions.items():
                age_hours = (current_time - session.last_activity).total_seconds() / 3600
                if age_hours > max_age_hours:
                    expired_sessions.append(task_id)
            
            for task_id in expired_sessions:
                del self.sessions[task_id]
                logger.info(f"清理过期会话: {task_id}")
            
            logger.info(f"会话清理完成，清理了{len(expired_sessions)}个过期会话")
            return len(expired_sessions)
            
        except Exception as e:
            logger.error(f"清理会话失败: {e}")
            return 0

# 全局优化的会话管理器实例
optimized_meeting_chat_manager = OptimizedMeetingChatManager()

# 便捷函数保持向后兼容
def create_optimized_chat_session(task_id: str, cleaned_content: str, meeting_minutes: str, 
                                 metadata: Optional[MeetingMetadata] = None) -> Tuple[bool, str]:
    """创建优化的聊天会话"""
    return optimized_meeting_chat_manager.create_session(task_id, cleaned_content, meeting_minutes, metadata)

def ask_meeting_question_optimized(task_id: str, question: str) -> Dict:
    """向会议内容提问（优化版）"""
    return optimized_meeting_chat_manager.ask_question(task_id, question)

def get_optimized_chat_history(task_id: str, include_stats: bool = False) -> Dict:
    """获取优化的聊天历史"""
    return optimized_meeting_chat_manager.get_conversation_history(task_id, include_stats)

def clear_optimized_chat_history(task_id: str) -> Dict:
    """清空优化的聊天历史"""
    return optimized_meeting_chat_manager.clear_conversation(task_id)

def get_optimized_session_status(task_id: str) -> Dict:
    """获取优化的会话状态"""
    return optimized_meeting_chat_manager.get_session_status(task_id)

# 测试函数
async def test_optimized_meeting_chat():
    """测试优化的会议问答功能"""
    print("=" * 60)
    print("测试优化的会议问答功能")
    print("=" * 60)
    
    # 模拟会议数据
    test_cleaned = """SPEAKER_00: 欢迎大家参加今天的AI技术应用讨论会议。我是项目负责人张经理。
SPEAKER_01: 大家好，我是技术总监李工程师。今天我们主要讨论AI在IP开发中的应用前景。
SPEAKER_00: 是的，根据市场调研，AI技术可以大幅降低开发成本，预估能节省40%的时间。
SPEAKER_01: 我同意这个观点。我们计划投资100万人民币来启动这个AI项目。
SPEAKER_00: 关于时间安排，我建议分两个阶段执行。
SPEAKER_01: 第一阶段用3个月完成核心算法开发，第二阶段用6个月完成产品化。"""
    
    test_minutes = """# AI技术应用讨论会议纪要

## 会议基本信息
- 会议时间: 2025-08-30
- 主持人: 张经理（项目负责人）  
- 参会人员: 张经理、李工程师（技术总监）
- 会议主题: AI技术在IP开发中的应用

## 主要讨论内容
1. **AI技术应用价值**
   - 可降低40%的开发时间
   - 显著提升开发效率
   
2. **项目投资决策**
   - 确定投资100万人民币
   - 启动AI项目开发

3. **项目时间规划**
   - 第一阶段: 3个月完成核心算法
   - 第二阶段: 6个月完成产品化
   - 总计9个月完成整个项目

## 会议决议
- 批准AI项目投资预算
- 确认项目时间表
- 下次会议时间待定"""

    # 创建会话元数据
    metadata = MeetingMetadata(
        meeting_name="AI技术应用讨论会",
        speaker_count=2,
        duration=45.0,
        topics=["AI技术应用", "投资决策", "项目规划"],
        key_decisions=["投资100万启动AI项目", "采用两阶段开发模式"]
    )
    
    # 创建会话
    task_id = "test_optimized_meeting_456"
    success, message = create_optimized_chat_session(task_id, test_cleaned, test_minutes, metadata)
    print(f"创建优化会话: {'✓ 成功' if success else '✗ 失败'} - {message}")
    
    if success:
        # 测试问答序列
        questions = [
            "这次会议的主要参会人员是谁？",
            "AI项目的投资预算是多少？",  
            "项目的时间安排是怎样的？",
            "AI技术预期能带来什么效益？",
            "会议达成了哪些重要决议？"
        ]
        
        print(f"\n开始测试{len(questions)}个问题...")
        
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*20} 问题 {i} {'='*20}")
            print(f"问题: {question}")
            
            # 使用异步方法测试
            result = await optimized_meeting_chat_manager.ask_question_async(task_id, question)
            
            if result["success"]:
                print(f"✓ 回答成功 (耗时: {result.get('response_time', 0)}s)")
                print(f"📋 答案: {result['answer']}")
                print(f"📊 对话数: {result['conversation_count']}")
                if result.get('from_cache'):
                    print("🔄 使用了缓存")
            else:
                print(f"✗ 回答失败: {result['error']}")
        
        # 获取会话状态和统计
        print(f"\n{'='*20} 会话状态 {'='*20}")
        status = get_optimized_session_status(task_id)
        if status["success"]:
            stats = status["statistics"]
            print(f"📈 会话统计:")
            print(f"  • 总问题数: {stats['total_questions']}")
            print(f"  • 平均响应时间: {stats['avg_response_time']}s")  
            print(f"  • 会话时长: {stats['session_duration']:.1f}分钟")
            print(f"  • 会话状态: {stats['status']}")
        
        # 获取对话历史
        print(f"\n{'='*20} 对话历史 {'='*20}")
        history = get_optimized_chat_history(task_id, include_stats=True)
        if history["success"]:
            print(f"📚 对话记录: {history['conversation_count']}条")
            print(f"📅 创建时间: {history['created_at']}")
            print(f"🕒 最后活动: {history['last_activity']}")

if __name__ == "__main__":
    # 测试异步功能
    asyncio.run(test_optimized_meeting_chat())