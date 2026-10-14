#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试8.28.m4a音频文件
"""

import os
import json
import time
from datetime import datetime
from core import MeetingProcessor
from meeting_chat import create_chat_session, ask_meeting_question

def test_8_28_audio():
    """测试8.28音频文件"""
    audio_path = "test_file/8.28.m4a"
    meeting_name = "8月28日会议"
    
    if not os.path.exists(audio_path):
        print(f"文件不存在: {audio_path}")
        return None
    
    print(f"开始测试: {audio_path}")
    print(f"会议: {meeting_name}")
    
    start_time = time.time()
    
    try:
        # 音频处理
        print("正在处理音频...")
        processor = MeetingProcessor()
        result = processor.process_with_speaker_id(
            audio_path, 
            meeting_name=meeting_name, 
            output_dir="test_output"
        )
        
        processing_time = time.time() - start_time
        print(f"音频处理完成，用时: {processing_time:.2f}秒")
        print(f"识别发言人数: {result.get('speaker_count', 0)}")
        print(f"转录长度: {len(result.get('transcript', ''))}字符")
        print(f"纪要长度: {len(result.get('minutes', ''))}字符")
        
        # 创建问答会话
        print("创建问答会话...")
        task_id = f"test_828_{int(time.time())}"
        chat_success = create_chat_session(
            task_id, 
            result["cleaned"], 
            result["minutes"]
        )
        
        qa_results = []
        if chat_success:
            print("问答会话创建成功")
            
            # 测试问题
            questions = [
                "这次会议的主要内容是什么？",
                "参会人员有哪些？", 
                "会议中有哪些重要决策？",
                "有什么需要跟进的行动项吗？"
            ]
            
            for i, question in enumerate(questions, 1):
                print(f"\n问题{i}: {question}")
                answer = ask_meeting_question(task_id, question)
                
                if answer["success"]:
                    print(f"回答: {answer['answer'][:300]}...")
                    qa_results.append({
                        "question": question,
                        "answer": answer["answer"],
                        "success": True
                    })
                else:
                    print(f"回答失败: {answer['error']}")
                    qa_results.append({
                        "question": question,
                        "answer": None,
                        "success": False,
                        "error": answer["error"]
                    })
        
        # 保存结果
        test_result = {
            "audio_file": audio_path,
            "meeting_name": meeting_name,
            "task_id": task_id,
            "processing_time": round(processing_time, 2),
            "speaker_count": result.get("speaker_count", 0),
            "transcript_length": len(result.get("transcript", "")),
            "minutes_length": len(result.get("minutes", "")),
            "transcript_sample": result.get("transcript", "")[:500],
            "minutes_sample": result.get("minutes", "")[:500], 
            "chat_success": chat_success,
            "qa_results": qa_results,
            "timestamp": datetime.now().isoformat()
        }
        
        result_file = f"test_result_828_{datetime.now().strftime('%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {result_file}")
        return test_result
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return {"error": str(e), "audio_file": audio_path}

if __name__ == "__main__":
    test_8_28_audio()