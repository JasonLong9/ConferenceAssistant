#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConferenceAssistant Meeting API 完整测试脚本
测试所有meeting相关的接口功能
"""

import requests
import time
import json
import os
from pathlib import Path
import tempfile
import wave
import numpy as np

class MeetingAPITester:
    """Meeting API测试器"""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.test_task_id = None
    
    def log_test(self, test_name, success, details=""):
        """记录测试结果"""
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   详情: {details}")
        print()
    
    def create_test_audio(self, duration=10, sample_rate=16000):
        """创建测试音频文件"""
        # 生成简单的正弦波音频
        t = np.linspace(0, duration, duration * sample_rate, False)
        # 混合不同频率模拟不同发言人
        audio1 = np.sin(2 * np.pi * 440 * t[:len(t)//3])  # A音符
        audio2 = np.sin(2 * np.pi * 523 * t[len(t)//3:2*len(t)//3])  # C音符
        audio3 = np.sin(2 * np.pi * 659 * t[2*len(t)//3:])  # E音符
        
        audio = np.concatenate([audio1, audio2, audio3])
        audio = (audio * 32767).astype(np.int16)
        
        # 保存为WAV文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio.tobytes())
        
        return temp_file.name
    
    def test_server_health(self):
        """测试服务器健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_test("服务器健康检查", True, f"状态码: {response.status_code}")
            else:
                self.log_test("服务器健康检查", False, f"状态码: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test("服务器健康检查", False, "无法连接到服务器，请确保服务已启动")
            return False
        except Exception as e:
            self.log_test("服务器健康检查", False, f"连接错误: {str(e)}")
            return False
        
        return True
    
    def test_upload_audio(self):
        """测试音频上传接口"""
        try:
            # 创建测试音频文件
            audio_file = self.create_test_audio(duration=30)  # 30秒测试音频
            
            with open(audio_file, 'rb') as f:
                files = {'file': ('test_meeting.wav', f, 'audio/wav')}
                response = self.session.post(f"{self.base_url}/audio2summary_async", files=files)
            
            # 清理临时文件
            os.unlink(audio_file)
            
            if response.status_code == 200:
                result = response.json()
                if 'task_id' in result:
                    self.test_task_id = result['task_id']
                    self.log_test("音频上传", True, f"任务ID: {self.test_task_id}")
                    return True
                else:
                    self.log_test("音频上传", False, f"响应缺少task_id: {result}")
            else:
                self.log_test("音频上传", False, f"状态码: {response.status_code}, 响应: {response.text}")
        
        except Exception as e:
            self.log_test("音频上传", False, f"异常: {str(e)}")
        
        return False
    
    def test_task_status(self):
        """测试任务状态查询接口"""
        if not self.test_task_id:
            self.log_test("任务状态查询", False, "没有有效的task_id")
            return False
        
        try:
            params = {'task_id': self.test_task_id}
            response = self.session.get(f"{self.base_url}/task_status", params=params)
            
            if response.status_code == 200:
                result = response.json()
                if 'status' in result:
                    self.log_test("任务状态查询", True, f"状态: {result.get('status', 'unknown')}")
                    return True
                else:
                    self.log_test("任务状态查询", False, f"响应格式错误: {result}")
            else:
                self.log_test("任务状态查询", False, f"状态码: {response.status_code}")
        
        except Exception as e:
            self.log_test("任务状态查询", False, f"异常: {str(e)}")
        
        return False
    
    def wait_for_task_completion(self, timeout=300):
        """等待任务完成"""
        if not self.test_task_id:
            self.log_test("等待任务完成", False, "没有有效的task_id")
            return False
        
        start_time = time.time()
        last_status = ""
        
        print(f"等待任务 {self.test_task_id} 完成...")
        
        while time.time() - start_time < timeout:
            try:
                params = {'task_id': self.test_task_id}
                response = self.session.get(f"{self.base_url}/task_status", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status', 'unknown')
                    progress = result.get('progress', 0)
                    
                    if status != last_status:
                        print(f"  状态: {status}, 进度: {progress}%")
                        last_status = status
                    
                    if status == "done":
                        self.log_test("等待任务完成", True, f"任务完成，耗时: {time.time() - start_time:.1f}秒")
                        return True
                    elif status == "error":
                        self.log_test("等待任务完成", False, "任务处理失败")
                        return False
                
                time.sleep(5)  # 每5秒检查一次
            
            except Exception as e:
                self.log_test("等待任务完成", False, f"检查状态时出错: {str(e)}")
                return False
        
        self.log_test("等待任务完成", False, f"超时 ({timeout}秒)")
        return False
    
    def test_task_result(self):
        """测试获取任务结果接口"""
        if not self.test_task_id:
            self.log_test("获取任务结果", False, "没有有效的task_id")
            return False
        
        try:
            params = {'task_id': self.test_task_id}
            response = self.session.get(f"{self.base_url}/task_result", params=params)
            
            if response.status_code == 200:
                result = response.json()
                if 'status' in result and result['status'] == 'done' and 'result' in result:
                    meeting_result = result['result']
                    details = f"转写长度: {len(meeting_result.get('transcript', ''))}字符, "
                    details += f"发言人数: {meeting_result.get('speaker_count', 'unknown')}, "
                    details += f"问答可用: {meeting_result.get('chat_available', False)}"
                    
                    self.log_test("获取任务结果", True, details)
                    return meeting_result.get('chat_available', False)
                else:
                    self.log_test("获取任务结果", False, f"响应格式错误或任务未完成: {result}")
            else:
                self.log_test("获取任务结果", False, f"状态码: {response.status_code}")
        
        except Exception as e:
            self.log_test("获取任务结果", False, f"异常: {str(e)}")
        
        return False
    
    def test_meeting_ask(self):
        """测试会议问答接口"""
        if not self.test_task_id:
            self.log_test("会议问答", False, "没有有效的task_id")
            return False
        
        test_questions = [
            "这次会议有几个发言人？",
            "会议的主要内容是什么？",
            "请总结一下会议要点"
        ]
        
        success_count = 0
        
        for i, question in enumerate(test_questions, 1):
            try:
                data = {
                    'task_id': self.test_task_id,
                    'question': question
                }
                response = self.session.post(f"{self.base_url}/meeting/ask", json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0 and 'data' in result:
                        answer = result['data'].get('answer', '')
                        conv_count = result['data'].get('conversation_count', 0)
                        self.log_test(f"会议问答-问题{i}", True, 
                                    f"问题: {question[:20]}..., 回答长度: {len(answer)}字符, 对话数: {conv_count}")
                        success_count += 1
                    else:
                        self.log_test(f"会议问答-问题{i}", False, f"业务逻辑错误: {result}")
                else:
                    self.log_test(f"会议问答-问题{i}", False, f"状态码: {response.status_code}")
            
            except Exception as e:
                self.log_test(f"会议问答-问题{i}", False, f"异常: {str(e)}")
            
            time.sleep(1)  # 避免请求过快
        
        overall_success = success_count == len(test_questions)
        self.log_test("会议问答整体测试", overall_success, f"成功 {success_count}/{len(test_questions)} 个问题")
        
        return overall_success
    
    def test_chat_history(self):
        """测试获取对话历史接口"""
        if not self.test_task_id:
            self.log_test("对话历史", False, "没有有效的task_id")
            return False
        
        try:
            params = {'task_id': self.test_task_id}
            response = self.session.get(f"{self.base_url}/meeting/chat/history", params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 and 'data' in result:
                    data = result['data']
                    conv_count = data.get('conversation_count', 0)
                    conversations = data.get('conversations', [])
                    
                    self.log_test("对话历史", True, 
                                f"对话数量: {conv_count}, 历史记录: {len(conversations)}条")
                    return True
                else:
                    self.log_test("对话历史", False, f"业务逻辑错误: {result}")
            else:
                self.log_test("对话历史", False, f"状态码: {response.status_code}")
        
        except Exception as e:
            self.log_test("对话历史", False, f"异常: {str(e)}")
        
        return False
    
    def test_chat_status(self):
        """测试检查会话状态接口"""
        if not self.test_task_id:
            self.log_test("会话状态检查", False, "没有有效的task_id")
            return False
        
        try:
            params = {'task_id': self.test_task_id}
            response = self.session.get(f"{self.base_url}/meeting/chat/status", params=params)
            
            if response.status_code == 200:
                result = response.json()
                if 'code' in result and 'data' in result:
                    data = result['data']
                    available = data.get('available', False)
                    conv_count = data.get('conversation_count', 0)
                    
                    self.log_test("会话状态检查", True, 
                                f"可用: {available}, 对话数: {conv_count}")
                    return True
                else:
                    self.log_test("会话状态检查", False, f"响应格式错误: {result}")
            else:
                self.log_test("会话状态检查", False, f"状态码: {response.status_code}")
        
        except Exception as e:
            self.log_test("会话状态检查", False, f"异常: {str(e)}")
        
        return False
    
    def test_chat_clear(self):
        """测试清空对话历史接口"""
        if not self.test_task_id:
            self.log_test("清空对话历史", False, "没有有效的task_id")
            return False
        
        try:
            params = {'task_id': self.test_task_id}
            response = self.session.delete(f"{self.base_url}/meeting/chat/clear", params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.log_test("清空对话历史", True, "对话历史已清空")
                    
                    # 验证确实被清空了
                    time.sleep(1)
                    history_response = self.session.get(f"{self.base_url}/meeting/chat/history", params=params)
                    if history_response.status_code == 200:
                        history_result = history_response.json()
                        if history_result.get('code') == 0:
                            conv_count = history_result['data'].get('conversation_count', 0)
                            if conv_count == 0:
                                self.log_test("清空对话历史验证", True, "确认对话历史已清空")
                                return True
                            else:
                                self.log_test("清空对话历史验证", False, f"对话未完全清空，剩余: {conv_count}")
                    
                    return True
                else:
                    self.log_test("清空对话历史", False, f"业务逻辑错误: {result}")
            else:
                self.log_test("清空对话历史", False, f"状态码: {response.status_code}")
        
        except Exception as e:
            self.log_test("清空对话历史", False, f"异常: {str(e)}")
        
        return False
    
    def test_error_cases(self):
        """测试错误情况处理"""
        fake_task_id = "non-existent-task-id"
        
        # 测试不存在的任务ID
        test_cases = [
            ("任务状态查询-无效ID", "GET", "/task_status", {'task_id': fake_task_id}),
            ("任务结果获取-无效ID", "GET", "/task_result", {'task_id': fake_task_id}),
            ("会议问答-无效ID", "POST", "/meeting/ask", {'task_id': fake_task_id, 'question': '测试问题'}),
            ("对话历史-无效ID", "GET", "/meeting/chat/history", {'task_id': fake_task_id}),
            ("会话状态-无效ID", "GET", "/meeting/chat/status", {'task_id': fake_task_id}),
            ("清空对话-无效ID", "DELETE", "/meeting/chat/clear", {'task_id': fake_task_id}),
        ]
        
        error_handled_count = 0
        
        for test_name, method, endpoint, params in test_cases:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", params=params)
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", json=params)
                elif method == "DELETE":
                    response = self.session.delete(f"{self.base_url}{endpoint}", params=params)
                
                # 检查是否正确处理了错误情况
                if response.status_code in [404, 400] or (response.status_code == 200 and response.json().get('code') == 1):
                    self.log_test(test_name, True, "正确返回错误状态")
                    error_handled_count += 1
                else:
                    self.log_test(test_name, False, f"错误处理不当: {response.status_code}, {response.text[:100]}")
            
            except Exception as e:
                self.log_test(test_name, False, f"异常: {str(e)}")
        
        overall_success = error_handled_count == len(test_cases)
        self.log_test("错误处理整体测试", overall_success, f"正确处理 {error_handled_count}/{len(test_cases)} 个错误情况")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("ConferenceAssistant Meeting API 完整测试")
        print("=" * 80)
        print()
        
        # 1. 基础测试
        if not self.test_server_health():
            print("❌ 服务器无法连接，终止测试")
            return
        
        # 2. 音频处理流程测试
        if self.test_upload_audio():
            self.test_task_status()
            
            if self.wait_for_task_completion():
                chat_available = self.test_task_result()
                
                # 3. 问答功能测试（仅在chat可用时进行）
                if chat_available:
                    self.test_chat_status()
                    self.test_meeting_ask()
                    self.test_chat_history()
                    self.test_chat_clear()
                else:
                    print("⚠️ 问答功能不可用，跳过相关测试")
        
        # 4. 错误处理测试
        self.test_error_cases()
        
        # 5. 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print("测试报告")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test_name']}: {result['details']}")
        
        # 保存详细报告到文件
        report_file = f"meeting_api_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': passed_tests/total_tests*100
                },
                'details': self.test_results,
                'test_task_id': self.test_task_id,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ConferenceAssistant Meeting API 测试工具')
    parser.add_argument('--url', '-u', default='http://localhost:8080', 
                       help='API服务地址 (默认: http://localhost:8080)')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='快速测试模式（跳过音频处理）')
    
    args = parser.parse_args()
    
    if args.quick:
        print("⚠️ 快速测试模式：将跳过音频上传和处理步骤")
        print("请确保有一个已完成的任务ID用于问答功能测试")
        
        # 在快速模式下，可以手动设置一个已知的task_id
        task_id = input("请输入已完成的任务ID（留空跳过问答测试）: ").strip()
        
        tester = MeetingAPITester(args.url)
        if task_id:
            tester.test_task_id = task_id
        
        # 只运行不依赖音频处理的测试
        tester.test_server_health()
        if task_id:
            tester.test_task_status()
            tester.test_task_result()
            tester.test_chat_status()
            tester.test_meeting_ask()
            tester.test_chat_history()
            tester.test_chat_clear()
        tester.test_error_cases()
        tester.generate_report()
    else:
        # 完整测试
        tester = MeetingAPITester(args.url)
        tester.run_all_tests()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()