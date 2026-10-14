#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试8.20会议的问答功能
"""

import json
import time
from datetime import datetime
from meeting_chat import create_chat_session, ask_meeting_question, get_chat_history

def test_8_20_qa():
    """测试8.20会议问答"""
    
    # 读取已处理的会议内容
    content_file = "test_output/会议内容_8月20日会议_20250904_213502.md"
    minutes_file = "test_output/会议纪要_8月20日会议_20250904_213502.md"
    
    try:
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(minutes_file, 'r', encoding='utf-8') as f:
            minutes = f.read()
        
        print("已读取会议内容和纪要")
        print(f"内容长度: {len(content)}字符")
        print(f"纪要长度: {len(minutes)}字符")
        
        # 创建问答会话
        task_id = f"test_820_qa_{int(time.time())}"
        print(f"\n创建问答会话: {task_id}")
        
        chat_success = create_chat_session(task_id, content, minutes)
        
        if not chat_success:
            print("问答会话创建失败")
            return None
        
        print("问答会话创建成功，开始测试...")
        
        # 测试问题
        questions = [
            "这次会议的主要内容是什么？",
            "项目的利润点设计是怎样的？",
            "会议中讨论的成本投入包括哪些？", 
            "系统1.0版本要开发什么功能？",
            "商户分层是如何设计的？",
            "有哪些需要跟进的行动项？"
        ]
        
        qa_results = []
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*60}")
            print(f"问题{i}: {question}")
            print('='*60)
            
            start_time = time.time()
            answer_result = ask_meeting_question(task_id, question)
            response_time = time.time() - start_time
            
            if answer_result["success"]:
                print(f"✅ 回答成功 (耗时: {response_time:.2f}秒)")
                print(f"回答: {answer_result['answer']}")
                qa_results.append({
                    "question": question,
                    "answer": answer_result["answer"],
                    "success": True,
                    "response_time": round(response_time, 2)
                })
            else:
                print(f"❌ 回答失败: {answer_result['error']}")
                qa_results.append({
                    "question": question,
                    "error": answer_result["error"],
                    "success": False,
                    "response_time": round(response_time, 2)
                })
        
        # 获取对话历史
        print(f"\n{'='*60}")
        print("获取对话历史...")
        print('='*60)
        
        history = get_chat_history(task_id)
        if history["success"]:
            print(f"对话记录数: {history['conversation_count']}")
        
        # 保存测试结果
        test_result = {
            "task_id": task_id,
            "meeting_name": "8月20日会议",
            "content_length": len(content),
            "minutes_length": len(minutes),
            "total_questions": len(questions),
            "successful_answers": len([qa for qa in qa_results if qa["success"]]),
            "qa_results": qa_results,
            "conversation_history": history if history.get("success") else None,
            "timestamp": datetime.now().isoformat()
        }
        
        result_file = f"qa_test_820_{datetime.now().strftime('%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试结果已保存: {result_file}")
        print(f"问答成功率: {len([qa for qa in qa_results if qa['success']])}/{len(questions)}")
        
        return test_result
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None

if __name__ == "__main__":
    test_8_20_qa()