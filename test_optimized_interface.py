#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化接口完整测试脚本
测试所有优化的会议问答接口功能
"""

import asyncio
import aiohttp
import requests
import json
import time
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedAPITester:
    """优化API测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", data: Dict = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
    
    def test_system_endpoints(self):
        """测试系统端点"""
        print("\n" + "="*60)
        print("🔧 测试系统端点")
        print("="*60)
        
        # 测试根路径
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "根路径测试", 
                    True, 
                    f"服务版本: {data.get('version', 'unknown')}", 
                    data
                )
            else:
                self.log_test("根路径测试", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("根路径测试", False, f"连接失败: {str(e)}")
            return False
        
        # 测试健康检查
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "健康检查", 
                    True, 
                    f"活跃会话: {data.get('active_sessions', 0)}", 
                    data
                )
            else:
                self.log_test("健康检查", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("健康检查", False, str(e))
        
        return True
    
    def test_audio_upload(self, test_file_path: str = None) -> Optional[str]:
        """测试音频上传"""
        print("\n" + "="*60)
        print("🎵 测试音频上传")
        print("="*60)
        
        if not test_file_path:
            # 查找测试文件
            possible_files = [
                "test_file/河北人设仲裁需求会-1.mp3",
                "temp_20250830_021028_河北人设仲裁需求会-1.mp3",
                "temp_20250830_030100_admin.mp3"
            ]
            
            for file_path in possible_files:
                if os.path.exists(file_path):
                    test_file_path = file_path
                    break
            
            if not test_file_path:
                self.log_test("音频上传", False, "未找到测试音频文件")
                return None
        
        if not os.path.exists(test_file_path):
            self.log_test("音频上传", False, f"文件不存在: {test_file_path}")
            return None
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': (os.path.basename(test_file_path), f, 'audio/mpeg')}
                response = self.session.post(
                    f"{self.base_url}/audio2summary_async", 
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                self.log_test(
                    "音频上传", 
                    True, 
                    f"任务ID: {task_id}", 
                    data
                )
                return task_id
            else:
                self.log_test("音频上传", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("音频上传", False, str(e))
            return None
    
    def wait_for_completion(self, task_id: str, max_wait: int = 600) -> bool:
        """等待任务完成"""
        print(f"\n⏳ 等待任务完成: {task_id}")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(
                    f"{self.base_url}/task_status",
                    params={'task_id': task_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    progress = data.get('progress', 0)
                    
                    print(f"📊 进度: {progress}% - 状态: {status}")
                    
                    if status == 'done':
                        elapsed = time.time() - start_time
                        self.log_test(
                            "任务完成", 
                            True, 
                            f"耗时: {elapsed:.1f}秒", 
                            data
                        )
                        return True
                    elif status == 'error':
                        error = data.get('error', '未知错误')
                        self.log_test("任务完成", False, f"处理错误: {error}")
                        return False
                        
                elif response.status_code == 404:
                    self.log_test("任务完成", False, "任务不存在")
                    return False
                    
            except Exception as e:
                logger.warning(f"状态查询异常: {e}")
            
            time.sleep(10)
        
        self.log_test("任务完成", False, "等待超时")
        return False
    
    def test_task_result(self, task_id: str) -> Optional[Dict]:
        """测试获取任务结果"""
        print(f"\n📋 测试获取任务结果: {task_id}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/task_result",
                params={'task_id': task_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                
                # 验证结果完整性
                required_fields = ['transcript', 'cleaned', 'minutes', 'speaker_count']
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    self.log_test(
                        "获取任务结果", 
                        True, 
                        f"发言人数: {result.get('speaker_count', 0)}", 
                        {
                            "meeting_name": result.get('meeting_name', ''),
                            "speaker_count": result.get('speaker_count', 0),
                            "chat_available": result.get('chat_available', False)
                        }
                    )
                    return result
                else:
                    self.log_test(
                        "获取任务结果", 
                        False, 
                        f"缺少字段: {missing_fields}"
                    )
                    
            else:
                self.log_test("获取任务结果", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test("获取任务结果", False, str(e))
        
        return None
    
    async def test_optimized_qa_async(self, task_id: str):
        """测试优化的问答功能（异步）"""
        print(f"\n🤖 测试优化问答功能: {task_id}")
        
        test_questions = [
            "这次会议有几个发言人？",
            "会议的主要内容是什么？", 
            "会议达成了哪些重要决议？",
            "各个发言人的发言比例如何？",
            "会议讨论了哪些关键问题？"
        ]
        
        successful_answers = 0
        total_response_time = 0
        
        async with aiohttp.ClientSession() as session:
            for i, question in enumerate(test_questions, 1):
                print(f"\n🔍 问题 {i}: {question}")
                
                try:
                    start_time = time.time()
                    
                    async with session.post(
                        f"{self.base_url}/meeting/ask",
                        json={'task_id': task_id, 'question': question},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        response_time = time.time() - start_time
                        total_response_time += response_time
                        
                        if response.status == 200:
                            data = await response.json()
                            if data.get('code') == 0:
                                answer_data = data.get('data', {})
                                answer = answer_data.get('answer', '')
                                from_cache = answer_data.get('from_cache', False)
                                conversation_count = answer_data.get('conversation_count', 0)
                                
                                cache_info = "🔄 缓存" if from_cache else "🆕 新回答"
                                
                                self.log_test(
                                    f"问答-{i}",
                                    True,
                                    f"耗时: {response_time:.2f}s, {cache_info}, 对话数: {conversation_count}",
                                    {
                                        "question": question,
                                        "answer_length": len(answer),
                                        "response_time": response_time,
                                        "from_cache": from_cache
                                    }
                                )
                                
                                successful_answers += 1
                                print(f"💬 回答: {answer[:100]}...")
                            else:
                                self.log_test(f"问答-{i}", False, data.get('msg', '未知错误'))
                        else:
                            error_text = await response.text()
                            self.log_test(f"问答-{i}", False, f"HTTP {response.status}: {error_text}")
                            
                except Exception as e:
                    self.log_test(f"问答-{i}", False, str(e))
        
        # 统计结果
        avg_response_time = total_response_time / len(test_questions) if test_questions else 0
        success_rate = (successful_answers / len(test_questions)) * 100 if test_questions else 0
        
        self.log_test(
            "问答功能统计",
            successful_answers > 0,
            f"成功率: {success_rate:.1f}%, 平均耗时: {avg_response_time:.2f}s",
            {
                "total_questions": len(test_questions),
                "successful_answers": successful_answers,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time
            }
        )
    
    def test_chat_management(self, task_id: str):
        """测试对话管理功能"""
        print(f"\n💬 测试对话管理功能: {task_id}")
        
        # 测试获取对话状态
        try:
            response = self.session.get(
                f"{self.base_url}/meeting/chat/status",
                params={'task_id': task_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    chat_data = data.get('data', {})
                    self.log_test(
                        "获取对话状态",
                        True,
                        f"可用: {chat_data.get('available', False)}, 对话数: {chat_data.get('conversation_count', 0)}",
                        chat_data
                    )
                else:
                    self.log_test("获取对话状态", False, data.get('msg', ''))
            else:
                self.log_test("获取对话状态", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("获取对话状态", False, str(e))
        
        # 测试获取对话历史
        try:
            response = self.session.get(
                f"{self.base_url}/meeting/chat/history",
                params={'task_id': task_id, 'include_stats': True}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    history_data = data.get('data', {})
                    conversations = history_data.get('conversations', [])
                    statistics = history_data.get('statistics', {})
                    
                    self.log_test(
                        "获取对话历史",
                        True,
                        f"对话数: {len(conversations)}, 平均耗时: {statistics.get('avg_response_time', 0)}s",
                        {
                            "conversation_count": len(conversations),
                            "statistics": statistics
                        }
                    )
                    
                    # 显示最近的对话
                    if conversations:
                        print("📚 最近对话:")
                        for conv in conversations[-3:]:  # 显示最后3条
                            print(f"  Q: {conv['question'][:50]}...")
                            print(f"  A: {conv['answer'][:50]}...")
                            print(f"  ⏱️  {conv.get('response_time', 0):.2f}s\n")
                else:
                    self.log_test("获取对话历史", False, data.get('msg', ''))
            else:
                self.log_test("获取对话历史", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("获取对话历史", False, str(e))
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n🚨 测试错误处理")
        
        # 测试无效任务ID
        try:
            response = self.session.post(
                f"{self.base_url}/meeting/ask",
                json={'task_id': 'invalid-task-id', 'question': '测试问题'}
            )
            
            if response.status_code == 404:
                data = response.json()
                self.log_test(
                    "无效任务ID处理",
                    data.get('code') == 1,
                    "正确返回404错误"
                )
            else:
                self.log_test("无效任务ID处理", False, f"意外状态码: {response.status_code}")
        except Exception as e:
            self.log_test("无效任务ID处理", False, str(e))
        
        # 测试空问题
        try:
            response = self.session.post(
                f"{self.base_url}/meeting/ask",
                json={'task_id': 'test', 'question': ''}
            )
            
            if response.status_code == 422:  # 验证错误
                self.log_test("空问题处理", True, "正确返回验证错误")
            else:
                self.log_test("空问题处理", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("空问题处理", False, str(e))
        
        # 测试无效JSON
        try:
            response = self.session.post(
                f"{self.base_url}/meeting/ask",
                data="invalid json",
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 422:
                self.log_test("无效JSON处理", True, "正确返回JSON解析错误")
            else:
                self.log_test("无效JSON处理", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("无效JSON处理", False, str(e))
    
    def test_admin_endpoints(self):
        """测试管理端点"""
        print("\n🔧 测试管理端点")
        
        # 测试会话列表
        try:
            response = self.session.get(f"{self.base_url}/admin/sessions")
            if response.status_code == 200:
                data = response.json()
                session_count = data.get('total_sessions', 0)
                self.log_test(
                    "会话列表",
                    True,
                    f"总会话数: {session_count}",
                    {"session_count": session_count}
                )
            else:
                self.log_test("会话列表", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("会话列表", False, str(e))
        
        # 测试手动清理
        try:
            response = self.session.post(f"{self.base_url}/admin/cleanup")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "手动清理",
                    True,
                    data.get('message', ''),
                    data
                )
            else:
                self.log_test("手动清理", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("手动清理", False, str(e))
    
    async def run_comprehensive_test(self, test_file_path: str = None):
        """运行完整测试"""
        print("\n" + "="*80)
        print("🚀 启动优化接口完整测试")
        print("="*80)
        
        start_time = time.time()
        
        # 1. 测试系统端点
        if not self.test_system_endpoints():
            print("❌ 系统端点测试失败，停止测试")
            return
        
        # 2. 测试音频上传
        task_id = self.test_audio_upload(test_file_path)
        if not task_id:
            print("❌ 音频上传失败，跳过后续测试")
            self.test_error_handling()  # 仍然测试错误处理
            return
        
        # 3. 等待任务完成
        if not self.wait_for_completion(task_id):
            print("❌ 任务处理失败，跳过问答测试")
            return
        
        # 4. 测试获取结果
        result = self.test_task_result(task_id)
        if not result:
            print("❌ 获取结果失败，跳过问答测试")
            return
        
        # 5. 测试优化问答功能
        await self.test_optimized_qa_async(task_id)
        
        # 6. 测试对话管理
        self.test_chat_management(task_id)
        
        # 7. 测试错误处理
        self.test_error_handling()
        
        # 8. 测试管理端点
        self.test_admin_endpoints()
        
        # 统计测试结果
        total_time = time.time() - start_time
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("📊 测试结果统计")
        print("="*80)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"总耗时: {total_time:.1f}秒")
        
        if success_rate >= 80:
            print("✅ 测试结果良好")
        elif success_rate >= 60:
            print("⚠️ 测试结果一般")
        else:
            print("❌ 测试结果不佳")
        
        # 保存详细测试报告
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate,
                "total_time": total_time,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results
        }
        
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📝 详细测试报告已保存: {report_file}")
        except Exception as e:
            print(f"⚠️ 保存测试报告失败: {e}")

async def main():
    """主测试函数"""
    import sys
    
    # 解析命令行参数
    base_url = "http://localhost:8080"
    test_file = None
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    if len(sys.argv) > 2:
        test_file = sys.argv[2]
    
    print(f"🔗 测试服务地址: {base_url}")
    if test_file:
        print(f"🎵 测试音频文件: {test_file}")
    
    tester = OptimizedAPITester(base_url)
    await tester.run_comprehensive_test(test_file)

if __name__ == "__main__":
    # 运行测试
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试执行异常: {e}")
        import traceback
        traceback.print_exc()