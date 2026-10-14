#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConferenceAssistant API 综合测试脚本
测试所有可用的API接口，并记录问题和性能
"""

import requests
import json
import time
import os
from pathlib import Path

class APITester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.test_audio_path = "test_file/admin.MP3"
        self.results = []
        self.task_id = None
        
    def log_test(self, test_name, success, details="", response_time=0):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results.append(result)
        
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} {test_name}: {details} (耗时: {response_time:.2f}s)")
        
    def test_health_and_root(self):
        """测试基础健康检查接口"""
        print("\n=== 测试基础接口 ===")
        
        # 测试根路径
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("根路径访问", True, f"服务状态: {data.get('status', 'unknown')}", response_time)
            else:
                self.log_test("根路径访问", False, f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("根路径访问", False, f"连接错误: {str(e)}")
            
        # 测试健康检查（如果存在）
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("健康检查", True, f"活跃任务: {data.get('tasks_active', 0)}", response_time)
            elif response.status_code == 404:
                self.log_test("健康检查", False, "接口不存在", response_time)
            else:
                self.log_test("健康检查", False, f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("健康检查", False, f"连接错误: {str(e)}")
            
    def test_audio_upload(self):
        """测试音频上传接口"""
        print("\n=== 测试音频上传接口 ===")
        
        if not os.path.exists(self.test_audio_path):
            self.log_test("音频文件检查", False, f"测试文件不存在: {self.test_audio_path}")
            return False
            
        file_size = os.path.getsize(self.test_audio_path)
        self.log_test("音频文件检查", True, f"文件大小: {file_size / 1024:.2f} KB")
        
        try:
            start_time = time.time()
            
            with open(self.test_audio_path, 'rb') as f:
                files = {'file': (os.path.basename(self.test_audio_path), f, 'audio/mpeg')}
                response = requests.post(f"{self.base_url}/audio2summary_async", files=files, timeout=30)
                
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.task_id = data.get('task_id')
                self.log_test("音频上传", True, f"任务ID: {self.task_id}", response_time)
                return True
            else:
                self.log_test("音频上传", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("音频上传", False, "请求超时")
            return False
        except Exception as e:
            self.log_test("音频上传", False, f"上传错误: {str(e)}")
            return False
            
    def test_task_status_monitoring(self):
        """监控任务状态直到完成"""
        print("\n=== 监控任务进度 ===")
        
        if not self.task_id:
            self.log_test("任务状态监控", False, "没有有效的任务ID")
            return False
            
        max_attempts = 120  # 最多等待2分钟
        attempt = 0
        
        while attempt < max_attempts:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/task_status", params={"task_id": self.task_id})
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    progress = data.get('progress', 0)
                    
                    if status == 'done':
                        self.log_test("任务完成", True, f"进度: {progress}%", response_time)
                        return True
                    elif status == 'error':
                        error = data.get('error', '未知错误')
                        self.log_test("任务失败", False, f"错误: {error}", response_time)
                        return False
                    else:
                        if attempt % 10 == 0:  # 每10次打印一次进度
                            print(f"  任务进度: {status} - {progress}% (尝试 {attempt + 1})")
                        
                else:
                    self.log_test("状态查询", False, f"HTTP {response.status_code}", response_time)
                    return False
                    
            except Exception as e:
                self.log_test("状态查询", False, f"查询错误: {str(e)}")
                return False
                
            attempt += 1
            time.sleep(1)
            
        self.log_test("任务超时", False, f"任务未在{max_attempts}秒内完成")
        return False
        
    def test_task_result(self):
        """测试获取任务结果"""
        print("\n=== 测试任务结果获取 ===")
        
        if not self.task_id:
            self.log_test("结果获取", False, "没有有效的任务ID")
            return None
            
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/task_result", params={"task_id": self.task_id})
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'done':
                    result = data.get('result', {})
                    
                    # 检查关键字段
                    transcript = result.get('transcript', '')
                    cleaned = result.get('cleaned', '')
                    minutes = result.get('minutes', '')
                    speaker_count = result.get('speaker_count', 0)
                    chat_available = result.get('chat_available', False)
                    
                    details = f"转录: {len(transcript)}字符, 清理: {len(cleaned)}字符, 纪要: {len(minutes)}字符, 说话人: {speaker_count}, 问答: {'可用' if chat_available else '不可用'}"
                    self.log_test("结果获取", True, details, response_time)
                    
                    # 保存结果到文件以便检查
                    with open("test_result.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        
                    return result
                else:
                    self.log_test("结果获取", False, f"任务状态: {data.get('status')}", response_time)
                    return None
            else:
                self.log_test("结果获取", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_test("结果获取", False, f"获取错误: {str(e)}")
            return None
            
    def test_chat_interfaces(self):
        """测试问答接口"""
        print("\n=== 测试智能问答接口 ===")
        
        if not self.task_id:
            self.log_test("问答接口测试", False, "没有有效的任务ID")
            return
            
        # 测试会话状态
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/meeting/chat/status", params={"task_id": self.task_id})
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                available = data.get('data', {}).get('available', False) if data.get('code') == 0 else False
                self.log_test("会话状态检查", True, f"会话可用: {'是' if available else '否'}", response_time)
            else:
                self.log_test("会话状态检查", False, f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("会话状态检查", False, f"检查错误: {str(e)}")
            
        # 测试问答
        test_questions = [
            "这个会议的主要内容是什么？",
            "会议中讨论了哪些重点？",
            "有多少人参加了会议？"
        ]
        
        for question in test_questions:
            try:
                start_time = time.time()
                
                payload = {
                    "task_id": self.task_id,
                    "question": question
                }
                
                response = requests.post(f"{self.base_url}/meeting/ask", json=payload, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0:
                        answer = data.get('data', {}).get('answer', '')
                        self.log_test(f"问答: {question[:20]}...", True, f"回答长度: {len(answer)}字符", response_time)
                    else:
                        error_msg = data.get('msg', '未知错误')
                        self.log_test(f"问答: {question[:20]}...", False, f"业务错误: {error_msg}", response_time)
                else:
                    self.log_test(f"问答: {question[:20]}...", False, f"HTTP {response.status_code}", response_time)
                    
            except requests.exceptions.Timeout:
                self.log_test(f"问答: {question[:20]}...", False, "请求超时")
            except Exception as e:
                self.log_test(f"问答: {question[:20]}...", False, f"问答错误: {str(e)}")
                
        # 测试对话历史
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/meeting/chat/history", params={"task_id": self.task_id})
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    conversations = data.get('data', {}).get('conversations', [])
                    self.log_test("对话历史", True, f"对话记录: {len(conversations)}条", response_time)
                else:
                    self.log_test("对话历史", False, f"业务错误: {data.get('msg')}", response_time)
            else:
                self.log_test("对话历史", False, f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("对话历史", False, f"历史错误: {str(e)}")
            
    def test_performance_stats(self):
        """测试性能统计接口"""
        print("\n=== 测试性能统计接口 ===")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/stats/performance")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                active_tasks = data.get('active_tasks', 0)
                completed_tasks = data.get('completed_tasks', 0)
                self.log_test("性能统计", True, f"活跃: {active_tasks}, 完成: {completed_tasks}", response_time)
            elif response.status_code == 404:
                self.log_test("性能统计", False, "接口不存在（可能是旧版本）", response_time)
            else:
                self.log_test("性能统计", False, f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("性能统计", False, f"统计错误: {str(e)}")
            
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始ConferenceAssistant API 综合测试")
        print(f"📡 测试服务器: {self.base_url}")
        print(f"🎵 测试音频文件: {self.test_audio_path}")
        
        start_time = time.time()
        
        # 运行所有测试
        self.test_health_and_root()
        
        upload_success = self.test_audio_upload()
        if upload_success:
            task_success = self.test_task_status_monitoring()
            if task_success:
                self.test_task_result()
                self.test_chat_interfaces()
        
        self.test_performance_stats()
        
        total_time = time.time() - start_time
        
        # 生成测试报告
        self.generate_report(total_time)
        
    def generate_report(self, total_time):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 ConferenceAssistant API 测试报告")
        print("="*60)
        
        successful_tests = sum(1 for result in self.results if result['success'])
        total_tests = len(self.results)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"总测试数: {total_tests}")
        print(f"成功数: {successful_tests}")
        print(f"失败数: {total_tests - successful_tests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"总耗时: {total_time:.2f}秒")
        
        print("\n详细测试结果:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
            
        # 保存完整报告到文件
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": success_rate,
                "total_time": total_time,
                "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "results": self.results,
            "task_id": self.task_id
        }
        
        with open("api_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📋 详细报告已保存到: api_test_report.json")
        
        # 问题总结
        failed_tests = [r for r in self.results if not r['success']]
        if failed_tests:
            print("\n🚨 发现的问题:")
            for i, result in enumerate(failed_tests, 1):
                print(f"{i}. {result['test']}: {result['details']}")
        else:
            print("\n🎉 所有测试均通过!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ConferenceAssistant API综合测试")
    parser.add_argument("--url", default="http://localhost:8080", help="API服务器地址")
    parser.add_argument("--audio", default="test_file/admin.MP3", help="测试音频文件路径")
    
    args = parser.parse_args()
    
    tester = APITester(args.url)
    tester.test_audio_path = args.audio
    tester.run_all_tests()