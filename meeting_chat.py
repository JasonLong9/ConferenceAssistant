#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会议内容问答模块
支持基于会议内容的连续对话功能
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import requests

class MeetingChatSession:
    """会议对话会话管理类"""
    
    def __init__(self, task_id: str, cleaned_content: str, meeting_minutes: str):
        """
        初始化会议对话会话
        
        Args:
            task_id: 任务ID
            cleaned_content: 规整后的会议内容
            meeting_minutes: 会议纪要
        """
        self.task_id = task_id
        self.cleaned_content = cleaned_content
        self.meeting_minutes = meeting_minutes
        self.conversation_history: List[Dict[str, str]] = []
        self.created_at = datetime.now()
        
        # 构建初始上下文
        self.context = self._build_initial_context()
    
    def _build_initial_context(self) -> str:
        """构建初始上下文"""
        context = f"""# 会议内容资料

## 会议纪要
{self.meeting_minutes}

## 完整会议内容
{self.cleaned_content}

---
以上是本次会议的完整内容和纪要。请基于这些内容回答用户的问题。"""
        return context
    
    def add_conversation(self, question: str, answer: str):
        """添加对话记录"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer
        })
    
    def get_conversation_context(self) -> str:
        """获取对话上下文"""
        context_parts = [self.context]
        
        if self.conversation_history:
            context_parts.append("\n## 对话历史")
            for i, conv in enumerate(self.conversation_history, 1):
                context_parts.append(f"**Q{i}**: {conv['question']}")
                context_parts.append(f"**A{i}**: {conv['answer']}")
        
        return "\n\n".join(context_parts)

class MeetingChatManager:
    """会议对话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, MeetingChatSession] = {}
        self.deepseek_api_url = "https://api.deepseek.com/v1/chat/completions"
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        if not self.deepseek_api_key:
            print("警告: 未设置DEEPSEEK_API_KEY环境变量")
    
    def create_session(self, task_id: str, cleaned_content: str, meeting_minutes: str) -> bool:
        """
        创建会议对话会话
        
        Args:
            task_id: 任务ID
            cleaned_content: 规整后的会议内容  
            meeting_minutes: 会议纪要
            
        Returns:
            bool: 创建是否成功
        """
        try:
            if task_id in self.sessions:
                print(f"会话 {task_id} 已存在，将更新内容")
            
            session = MeetingChatSession(task_id, cleaned_content, meeting_minutes)
            self.sessions[task_id] = session
            
            print(f"成功创建会议对话会话: {task_id}")
            return True
            
        except Exception as e:
            print(f"创建会话失败: {e}")
            return False
    
    def get_session(self, task_id: str) -> Optional[MeetingChatSession]:
        """获取会话"""
        return self.sessions.get(task_id)
    
    def ask_question(self, task_id: str, question: str) -> Dict:
        """
        向会议内容提问
        
        Args:
            task_id: 任务ID
            question: 用户问题
            
        Returns:
            Dict: 包含答案和状态的响应
        """
        try:
            session = self.get_session(task_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在，请先完成会议处理",
                    "answer": None
                }
            
            # 获取完整的对话上下文
            context = session.get_conversation_context()
            
            # 构建提示词
            system_prompt = """你是一个专业的会议助手，请基于提供的会议内容和对话历史来回答用户的问题。

要求：
1. 基于会议内容准确回答问题
2. 如果问题涉及具体人员发言，请指出是哪个发言人
3. 如果问题需要总结或分析，请结合会议纪要和完整内容
4. 保持回答的专业性和准确性
5. 如果问题超出会议内容范围，请明确说明
6. 参考之前的对话历史，保持对话的连贯性

请直接回答问题，不要包含XML标签或格式化标记。"""
            
            # 调用DeepSeek API
            answer = self._call_deepseek(system_prompt, f"{context}\n\n用户问题: {question}")
            
            if answer:
                # 添加到对话历史
                session.add_conversation(question, answer)
                
                return {
                    "success": True,
                    "answer": answer,
                    "question": question,
                    "conversation_count": len(session.conversation_history)
                }
            else:
                return {
                    "success": False,
                    "error": "API调用失败",
                    "answer": None
                }
                
        except Exception as e:
            print(f"问答处理失败: {e}")
            return {
                "success": False,
                "error": f"处理失败: {str(e)}",
                "answer": None
            }
    
    def get_conversation_history(self, task_id: str) -> Dict:
        """获取对话历史"""
        try:
            session = self.get_session(task_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在"
                }
            
            return {
                "success": True,
                "task_id": task_id,
                "conversation_count": len(session.conversation_history),
                "conversations": session.conversation_history,
                "created_at": session.created_at.isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取对话历史失败: {str(e)}"
            }
    
    def clear_conversation(self, task_id: str) -> Dict:
        """清空对话历史"""
        try:
            session = self.get_session(task_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在"
                }
            
            session.conversation_history = []
            return {
                "success": True,
                "message": "对话历史已清空"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"清空对话失败: {str(e)}"
            }
    
    def _call_deepseek(self, system_prompt: str, user_message: str) -> Optional[str]:
        """调用DeepSeek API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(
                self.deepseek_api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                print(f"DeepSeek API调用失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"DeepSeek API调用异常: {e}")
            return None

# 全局会话管理器实例
meeting_chat_manager = MeetingChatManager()

def create_chat_session(task_id: str, cleaned_content: str, meeting_minutes: str) -> bool:
    """创建聊天会话（便捷函数）"""
    return meeting_chat_manager.create_session(task_id, cleaned_content, meeting_minutes)

def ask_meeting_question(task_id: str, question: str) -> Dict:
    """向会议内容提问（便捷函数）"""
    return meeting_chat_manager.ask_question(task_id, question)

def get_chat_history(task_id: str) -> Dict:
    """获取聊天历史（便捷函数）"""
    return meeting_chat_manager.get_conversation_history(task_id)

def clear_chat_history(task_id: str) -> Dict:
    """清空聊天历史（便捷函数）"""
    return meeting_chat_manager.clear_conversation(task_id)

# 测试函数
def test_meeting_chat():
    """测试会议问答功能"""
    print("=" * 50)
    print("测试会议问答功能")
    print("=" * 50)
    
    # 模拟会议内容
    test_cleaned = """发言人A: 我们今天讨论AI技术在企业中的应用，特别是在IP开发方面。
发言人B: 是的，我认为AI可以大大降低成本，提高效率。我们计划投资100万来开发这个项目。
发言人A: 那么时间安排呢？
发言人B: 我建议3个月内完成第一阶段，6个月内上线。"""
    
    test_minutes = """**会议纪要**
会议主题：AI技术应用讨论
参会人员：发言人A、发言人B
主要决策：
1. 投资100万开发AI应用项目
2. 3个月完成第一阶段
3. 6个月内项目上线"""
    
    # 创建会话
    task_id = "test_meeting_123"
    success = create_chat_session(task_id, test_cleaned, test_minutes)
    print(f"创建会话: {'成功' if success else '失败'}")
    
    if success:
        # 测试问答
        questions = [
            "这次会议的主要决策是什么？",
            "项目预算是多少？",
            "项目时间安排如何？"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n问题{i}: {question}")
            result = ask_meeting_question(task_id, question)
            
            if result["success"]:
                print(f"回答: {result['answer']}")
            else:
                print(f"错误: {result['error']}")
        
        # 获取对话历史
        history = get_chat_history(task_id)
        if history["success"]:
            print(f"\n对话记录数: {history['conversation_count']}")

if __name__ == "__main__":
    test_meeting_chat()