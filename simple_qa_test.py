#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版问答测试，解决编码问题
"""

import os
import json
import time
from datetime import datetime
from meeting_chat import create_chat_session, ask_meeting_question

def simple_qa_test():
    """简化版问答测试"""
    
    # 读取已处理的会议内容
    content_file = "test_output/会议内容_8月20日会议_20250904_213502.md"
    minutes_file = "test_output/会议纪要_8月20日会议_20250904_213502.md"
    
    try:
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(minutes_file, 'r', encoding='utf-8') as f:
            minutes = f.read()
        
        print("Content length:", len(content))
        print("Minutes length:", len(minutes))
        
        # 创建问答会话
        task_id = f"simple_test_{int(time.time())}"
        print("Creating chat session:", task_id)
        
        chat_success = create_chat_session(task_id, content, minutes)
        
        if not chat_success:
            print("Chat session creation failed")
            return None
        
        print("Chat session created successfully")
        
        # 测试问题
        questions = [
            "这次会议的主要内容是什么？",
            "项目的利润点设计是怎样的？"
        ]
        
        qa_results = []
        for i, question in enumerate(questions, 1):
            print(f"\nQuestion {i}: {question}")
            
            answer_result = ask_meeting_question(task_id, question)
            
            if answer_result["success"]:
                print("Answer successful")
                print("Answer:", answer_result["answer"][:200], "...")
                qa_results.append({
                    "question": question,
                    "answer": answer_result["answer"],
                    "success": True
                })
            else:
                print("Answer failed:", answer_result["error"])
                qa_results.append({
                    "question": question,
                    "error": answer_result["error"],
                    "success": False
                })
        
        # 保存结果
        result = {
            "task_id": task_id,
            "total_questions": len(questions),
            "successful_answers": len([qa for qa in qa_results if qa["success"]]),
            "qa_results": qa_results,
            "timestamp": datetime.now().isoformat()
        }
        
        result_file = f"simple_qa_result_{datetime.now().strftime('%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Results saved to: {result_file}")
        success_rate = len([qa for qa in qa_results if qa["success"]])
        print(f"Success rate: {success_rate}/{len(questions)}")
        
        return result
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return None

if __name__ == "__main__":
    # 设置环境变量
    os.environ["DEEPSEEK_API_KEY"] = "sk-3519120a65864619abc585d1dcd70f6b"
    simple_qa_test()