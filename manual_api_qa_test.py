#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手动创建会话并测试API问答功能
"""

import os
import requests
import json
from datetime import datetime

def create_manual_sessions_and_test():
    """手动创建会话并测试问答"""
    
    # 设置环境变量
    os.environ["DEEPSEEK_API_KEY"] = "sk-3519120a65864619abc585d1dcd70f6b"
    
    # 导入会话管理器
    from meeting_chat import meeting_chat_manager
    
    # API基础URL
    base_url = "http://localhost:8080"
    
    print("开始手动创建会话并测试API问答...")
    
    # 读取8.20会议内容和纪要
    content_820_path = "temp_output/会议内容_项目成本、系统开发及利润分配讨论_20250904_222930.md"
    minutes_820_path = "temp_output/会议纪要_项目成本、系统开发及利润分配讨论_20250904_222930.md"
    
    content_828_path = "temp_output/会议内容_教育培训行业现状、AI技术结合及课程设计策略讨论_20250904_222905.md"
    minutes_828_path = "temp_output/会议纪要_教育培训行业现状、AI技术结合及课程设计策略讨论_20250904_222905.md"
    
    try:
        # 读取8.20会议内容
        with open(content_820_path, 'r', encoding='utf-8') as f:
            content_820 = f.read()
        
        with open(minutes_820_path, 'r', encoding='utf-8') as f:
            minutes_820 = f.read()
        
        print(f"8.20会议内容长度: {len(content_820)}字符")
        print(f"8.20会议纪要长度: {len(minutes_820)}字符")
        
        # 读取8.28会议内容
        with open(content_828_path, 'r', encoding='utf-8') as f:
            content_828 = f.read()
            
        with open(minutes_828_path, 'r', encoding='utf-8') as f:
            minutes_828 = f.read()
        
        print(f"8.28会议内容长度: {len(content_828)}字符")  
        print(f"8.28会议纪要长度: {len(minutes_828)}字符")
        
        # 创建会话
        task_id_820 = "a4b65dbe-6466-463c-9f03-53cbc352a7d4"
        task_id_828 = "0675410e-e055-4522-ab8b-6df4c3b34484"
        
        print(f"\\n创建8.20会议会话: {task_id_820}")
        success_820 = meeting_chat_manager.create_session(task_id_820, content_820, minutes_820)
        print(f"8.20会话创建: {'成功' if success_820 else '失败'}")
        
        print(f"\\n创建8.28会议会话: {task_id_828}")
        success_828 = meeting_chat_manager.create_session(task_id_828, content_828, minutes_828)
        print(f"8.28会话创建: {'成功' if success_828 else '失败'}")
        
        if success_820:
            print("\\n" + "="*60)
            print("测试8.20会议API问答接口")
            print("="*60)
            
            questions_820 = [
                "这次会议识别出了几个发言人？",
                "会议的主要议题是什么？",
                "系统1.0版本要开发哪些功能？",
                "客户是如何分级的，各级收益如何？"
            ]
            
            qa_results_820 = []
            for i, question in enumerate(questions_820, 1):
                print(f"\\n问题{i}: {question}")
                
                # 调用API
                response = requests.post(f"{base_url}/meeting/ask", 
                    json={
                        "task_id": task_id_820,
                        "question": question
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "answer" in result:
                        answer = result["answer"]
                        print(f"回答: {answer[:300]}...")
                        qa_results_820.append({
                            "question": question,
                            "answer": answer,
                            "status_code": response.status_code,
                            "success": True
                        })
                    else:
                        print(f"API响应异常: {result}")
                        qa_results_820.append({
                            "question": question,
                            "error": str(result),
                            "status_code": response.status_code,
                            "success": False
                        })
                else:
                    print(f"API调用失败: {response.status_code} - {response.text}")
                    qa_results_820.append({
                        "question": question,
                        "error": response.text,
                        "status_code": response.status_code,
                        "success": False
                    })
        
        if success_828:
            print("\\n" + "="*60)
            print("测试8.28会议API问答接口") 
            print("="*60)
            
            questions_828 = [
                "这次会议讨论了什么主题？",
                "会议中识别出了几个发言人？",
                "会议提到了哪些具体的行动计划？",
                "关于AI技术应用有什么讨论？"
            ]
            
            qa_results_828 = []
            for i, question in enumerate(questions_828, 1):
                print(f"\\n问题{i}: {question}")
                
                # 调用API
                response = requests.post(f"{base_url}/meeting/ask",
                    json={
                        "task_id": task_id_828,
                        "question": question
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "answer" in result:
                        answer = result["answer"] 
                        print(f"回答: {answer[:300]}...")
                        qa_results_828.append({
                            "question": question,
                            "answer": answer,
                            "status_code": response.status_code,
                            "success": True
                        })
                    else:
                        print(f"API响应异常: {result}")
                        qa_results_828.append({
                            "question": question,
                            "error": str(result),
                            "status_code": response.status_code,
                            "success": False
                        })
                else:
                    print(f"API调用失败: {response.status_code} - {response.text}")
                    qa_results_828.append({
                        "question": question,
                        "error": response.text,
                        "status_code": response.status_code,
                        "success": False
                    })
        
        # 测试其他接口
        print("\\n" + "="*60)
        print("测试其他会话管理接口")
        print("="*60)
        
        # 测试对话历史接口
        print("\\n测试对话历史查询接口...")
        history_response = requests.get(f"{base_url}/meeting/chat/history",
            params={"task_id": task_id_820}
        )
        print(f"对话历史查询: {history_response.status_code}")
        if history_response.status_code == 200:
            history_data = history_response.json()
            print(f"历史记录数: {history_data.get('conversation_count', 0) if 'conversation_count' in history_data else '未知'}")
        
        # 测试会话状态接口  
        print("\\n测试会话状态查询接口...")
        status_response = requests.get(f"{base_url}/meeting/chat/status",
            params={"task_id": task_id_820}
        )
        print(f"会话状态查询: {status_response.status_code}")
        
        # 保存测试结果
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "session_creation": {
                "820_success": success_820,
                "828_success": success_828
            },
            "qa_results_820": qa_results_820 if success_820 else [],
            "qa_results_828": qa_results_828 if success_828 else [],
            "api_tests": {
                "history_status": history_response.status_code,
                "status_status": status_response.status_code
            }
        }
        
        result_file = f"manual_api_test_results_{datetime.now().strftime('%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\\n测试结果已保存到: {result_file}")
        
        return test_results
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    create_manual_sessions_and_test()