#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试会话状态
"""

import os
from meeting_chat import meeting_chat_manager

def debug_sessions():
    """调试会话状态"""
    
    os.environ["DEEPSEEK_API_KEY"] = "sk-3519120a65864619abc585d1dcd70f6b"
    
    print("调试会话管理器状态...")
    print(f"当前会话数量: {len(meeting_chat_manager.sessions)}")
    
    for task_id, session in meeting_chat_manager.sessions.items():
        print(f"会话ID: {task_id}")
        print(f"创建时间: {session.created_at}")
        print(f"对话记录数: {len(session.conversation_history)}")
        print("---")
    
    # 重新创建会话
    print("\\n重新创建会话...")
    
    # 读取文件内容
    content_820_path = "temp_output/会议内容_项目成本、系统开发及利润分配讨论_20250904_222930.md"
    minutes_820_path = "temp_output/会议纪要_项目成本、系统开发及利润分配讨论_20250904_222930.md"
    
    try:
        with open(content_820_path, 'r', encoding='utf-8') as f:
            content_820 = f.read()
        
        with open(minutes_820_path, 'r', encoding='utf-8') as f:
            minutes_820 = f.read()
        
        # 使用新的任务ID
        new_task_id = "manual_test_820"
        success = meeting_chat_manager.create_session(new_task_id, content_820, minutes_820)
        print(f"新会话创建: {'成功' if success else '失败'}")
        
        if success:
            # 测试问答
            question = "这次会议识别出了几个发言人？"
            print(f"\\n测试问题: {question}")
            
            result = meeting_chat_manager.ask_question(new_task_id, question)
            
            if result["success"]:
                print(f"回答: {result['answer']}")
            else:
                print(f"回答失败: {result['error']}")
        
        print(f"\\n最终会话数量: {len(meeting_chat_manager.sessions)}")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    debug_sessions()