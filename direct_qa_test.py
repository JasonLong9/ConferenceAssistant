#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接调用会话管理器测试问答功能（绕过API任务状态检查）
"""

import os
import json
from datetime import datetime
from meeting_chat import meeting_chat_manager

def direct_qa_test():
    """直接测试问答功能"""
    
    # 设置环境变量
    os.environ["DEEPSEEK_API_KEY"] = "sk-3519120a65864619abc585d1dcd70f6b"
    
    print("直接测试问答功能（绕过API状态检查）...")
    
    # 任务ID
    task_id_820 = "a4b65dbe-6466-463c-9f03-53cbc352a7d4"
    task_id_828 = "0675410e-e055-4522-ab8b-6df4c3b34484"
    
    print("\\n" + "="*60)
    print("测试8.20会议问答功能")
    print("="*60)
    
    questions_820 = [
        "这次会议识别出了几个发言人？",
        "会议的主要议题是什么？",
        "系统1.0版本要开发哪些功能？",
        "客户是如何分级的？"
    ]
    
    qa_results_820 = []
    for i, question in enumerate(questions_820, 1):
        print(f"\\n问题{i}: {question}")
        
        # 直接调用会话管理器
        result = meeting_chat_manager.ask_question(task_id_820, question)
        
        if result["success"]:
            answer = result["answer"]
            print(f"回答: {answer}")
            qa_results_820.append({
                "question": question,
                "answer": answer,
                "success": True
            })
        else:
            print(f"回答失败: {result['error']}")
            qa_results_820.append({
                "question": question,
                "error": result["error"],
                "success": False
            })
    
    print("\\n" + "="*60)
    print("测试8.28会议问答功能")
    print("="*60)
    
    questions_828 = [
        "这次会议讨论了什么主题？",
        "会议中识别出了几个发言人？",
        "会议提到了哪些具体的行动计划？"
    ]
    
    qa_results_828 = []
    for i, question in enumerate(questions_828, 1):
        print(f"\\n问题{i}: {question}")
        
        # 直接调用会话管理器
        result = meeting_chat_manager.ask_question(task_id_828, question)
        
        if result["success"]:
            answer = result["answer"]
            print(f"回答: {answer}")
            qa_results_828.append({
                "question": question,
                "answer": answer,
                "success": True
            })
        else:
            print(f"回答失败: {result['error']}")
            qa_results_828.append({
                "question": question,
                "error": result["error"],
                "success": False
            })
    
    # 测试对话历史
    print("\\n" + "="*60)
    print("测试对话历史功能")
    print("="*60)
    
    history_820 = meeting_chat_manager.get_conversation_history(task_id_820)
    print(f"\\n8.20会议对话历史: {'成功' if history_820['success'] else '失败'}")
    if history_820["success"]:
        print(f"对话记录数: {history_820['conversation_count']}")
    
    history_828 = meeting_chat_manager.get_conversation_history(task_id_828)
    print(f"\\n8.28会议对话历史: {'成功' if history_828['success'] else '失败'}")
    if history_828["success"]:
        print(f"对话记录数: {history_828['conversation_count']}")
    
    # 保存结果
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "qa_results_820": qa_results_820,
        "qa_results_828": qa_results_828,
        "history_820": history_820,
        "history_828": history_828,
        "summary": {
            "820_questions": len(questions_820),
            "820_success": len([r for r in qa_results_820 if r["success"]]),
            "828_questions": len(questions_828), 
            "828_success": len([r for r in qa_results_828 if r["success"]]),
        }
    }
    
    result_file = f"direct_qa_test_results_{datetime.now().strftime('%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\\n测试结果已保存到: {result_file}")
    
    # 打印摘要
    print("\\n" + "="*60)
    print("测试结果摘要")  
    print("="*60)
    print(f"8.20会议问答: {test_results['summary']['820_success']}/{test_results['summary']['820_questions']} 成功")
    print(f"8.28会议问答: {test_results['summary']['828_success']}/{test_results['summary']['828_questions']} 成功")
    
    return test_results

if __name__ == "__main__":
    direct_qa_test()