#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试8.20.m4a和8.28.m4a音频文件的完整流程
包括音频转录、声纹识别、会议纪要生成和问答测试
"""

import os
import json
import time
from datetime import datetime
from core import MeetingProcessor
from meeting_chat import create_chat_session, ask_meeting_question, get_chat_history, clear_chat_history

class AudioTestManager:
    def __init__(self):
        self.processor = MeetingProcessor()
        self.test_results = {}
        
    def test_audio_file(self, audio_path, meeting_name):
        """测试单个音频文件的完整流程"""
        print(f"\n{'='*60}")
        print(f"开始测试音频文件: {audio_path}")
        print(f"会议名称: {meeting_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # 1. 音频处理
            print("\n1️⃣ 开始音频处理...")
            result = self.processor.process_with_speaker_id(
                audio_path, 
                meeting_name=meeting_name, 
                output_dir="test_output"
            )
            
            processing_time = time.time() - start_time
            
            # 2. 创建问答会话
            print("\n2️⃣ 创建问答会话...")
            task_id = f"test_{meeting_name}_{int(time.time())}"
            chat_success = create_chat_session(
                task_id, 
                result["cleaned"], 
                result["minutes"]
            )
            
            # 3. 问答测试
            print("\n3️⃣ 开始问答测试...")
            questions = [
                "这次会议的主要内容是什么？",
                "会议中有哪些重要决策？", 
                "参会人员有哪些？",
                "会议的核心议题是什么？",
                "有什么需要跟进的行动项吗？"
            ]
            
            qa_results = []
            for i, question in enumerate(questions, 1):
                print(f"\n🤔 问题{i}: {question}")
                answer_result = ask_meeting_question(task_id, question)
                
                if answer_result["success"]:
                    print(f"✅ 回答: {answer_result['answer'][:200]}...")
                    qa_results.append({
                        "question": question,
                        "answer": answer_result["answer"],
                        "success": True
                    })
                else:
                    print(f"❌ 回答失败: {answer_result['error']}")
                    qa_results.append({
                        "question": question,
                        "answer": None,
                        "success": False,
                        "error": answer_result["error"]
                    })
            
            # 4. 获取对话历史
            print("\n4️⃣ 获取对话历史...")
            history = get_chat_history(task_id)
            
            # 5. 汇总测试结果
            test_result = {
                "audio_file": audio_path,
                "meeting_name": meeting_name,
                "task_id": task_id,
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().isoformat(),
                "audio_processing": {
                    "success": True,
                    "speaker_count": result.get("speaker_count", 0),
                    "transcript_length": len(result.get("transcript", "")),
                    "cleaned_length": len(result.get("cleaned", "")),
                    "minutes_length": len(result.get("minutes", "")),
                    "transcript_sample": result.get("transcript", "")[:300] + "..." if result.get("transcript") else "",
                    "minutes_sample": result.get("minutes", "")[:500] + "..." if result.get("minutes") else ""
                },
                "chat_session": {
                    "success": chat_success,
                    "qa_results": qa_results,
                    "total_questions": len(questions),
                    "successful_answers": len([qa for qa in qa_results if qa["success"]])
                },
                "conversation_history": history if history.get("success") else None
            }
            
            self.test_results[meeting_name] = test_result
            
            print(f"\n✅ 测试完成!")
            print(f"⏱️  总耗时: {processing_time:.2f}秒")
            print(f"👥 识别发言人数: {result.get('speaker_count', 0)}")
            print(f"📝 转录文本长度: {len(result.get('transcript', ''))}字符")
            print(f"📋 会议纪要长度: {len(result.get('minutes', ''))}字符")
            print(f"💬 问答成功率: {len([qa for qa in qa_results if qa['success']])}/{len(questions)}")
            
            return test_result
            
        except Exception as e:
            error_result = {
                "audio_file": audio_path,
                "meeting_name": meeting_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "processing_time": time.time() - start_time
            }
            self.test_results[meeting_name] = error_result
            print(f"\n❌ 测试失败: {str(e)}")
            return error_result
    
    def generate_report(self):
        """生成测试报告"""
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "successful_tests": len([r for r in self.test_results.values() if r.get("audio_processing", {}).get("success", False)]),
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": self.test_results
        }
        
        # 保存报告
        report_file = f"audio_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 测试报告已保存: {report_file}")
        return report_file, report

def main():
    """主测试函数"""
    print("开始音频文件测试...")
    
    # 检查音频文件是否存在
    audio_files = [
        ("test_file/8.20.m4a", "8月20日会议"),
        ("test_file/8.28.m4a", "8月28日会议")
    ]
    
    for audio_path, meeting_name in audio_files:
        if not os.path.exists(audio_path):
            print(f"❌ 音频文件不存在: {audio_path}")
            continue
    
    # 开始测试
    test_manager = AudioTestManager()
    
    for audio_path, meeting_name in audio_files:
        if os.path.exists(audio_path):
            test_manager.test_audio_file(audio_path, meeting_name)
        else:
            print(f"⚠️  跳过不存在的文件: {audio_path}")
    
    # 生成报告
    print(f"\n{'='*60}")
    print("📊 生成测试报告...")
    print(f"{'='*60}")
    report_file, report = test_manager.generate_report()
    
    # 打印摘要
    print(f"\n📋 测试摘要:")
    print(f"  • 总测试数: {report['test_summary']['total_tests']}")
    print(f"  • 成功测试: {report['test_summary']['successful_tests']}")
    print(f"  • 成功率: {report['test_summary']['successful_tests']/report['test_summary']['total_tests']*100:.1f}%" if report['test_summary']['total_tests'] > 0 else "  • 成功率: 0%")
    
    return report_file

if __name__ == "__main__":
    main()